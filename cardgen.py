#!/usr/bin/env python

import sys
import math
import json
import os.path
from operator import itemgetter, attrgetter
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from curved import CubicBezier, CurvedText
from hearthstone.cardxml import load
import custom
from component import (
	ComponentType, ShapeType, Region, Shape, Image, Text, Clip, Curve,
	Component, ComponentData
)

theme = "../hearthforge/styles/default/"
dataFilename = "default.json"
artwork = "./output/artwork/"
card_xml = "./output/CardDefs.xml"

def as_shape(obj):
	if "type" in obj:
		if obj["type"] == "curve":
			return CubicBezier()
		else:
			return Shape(obj["type"], obj["x"], obj["y"], obj["width"], obj["height"])
	else:
		return obj


def get_scale(img, w, h):
	return (round(float(w) / img.get_width(), 2), round(float(h) / img.get_height(), 2))


def draw_crosshair(ctx, x, y, length, color=None):
	if not color:
		color = (1, 0, 0)
	ctx.save()
	ctx.set_source_rgb(*color)
	ctx.set_line_width(2.0)
	ctx.set_line_cap(cairo.LINE_CAP_BUTT)
	ctx.new_path()
	ctx.move_to(x, y + length)
	ctx.line_to(x, y - length)
	ctx.move_to(x + length, y)
	ctx.line_to(x - length, y)
	ctx.stroke()
	ctx.restore()


def draw_image(ctx, image, key):
	file_path = os.path.join(theme, image.assets[key])
	if not os.path.isfile(file_path):
		print("Asset ({}) not found".format(file_path))
		return
	ctx.save()
	img = cairo.ImageSurface.create_from_png(file_path)
	scl = get_scale(img, image.width, image.height)
	ctx.translate(image.x, image.y)
	ctx.scale(scl[0], scl[1]) # TODO only scale if not 1.0
	ctx.set_source_surface(img)
	ctx.paint()
	ctx.restore()


# TODO merge draw image functions
def draw_image_override(ctx, image, dir, file):
	file_path = os.path.join(dir, file)
	if not os.path.isfile(file_path):
		print("Asset ({}) not found".format(file_path))
		return
	ctx.save()
	img = cairo.ImageSurface.create_from_png(file_path)
	scl = get_scale(img, image.width, image.height)
	ctx.translate(image.x, image.y)
	ctx.scale(scl[0], scl[1]) # TODO only scale if not 1.0
	ctx.set_source_surface(img)
	ctx.paint()
	ctx.restore()

def draw_clip_region(ctx, obj):
	if obj.type == ShapeType.ellipse:
		draw_box_ellipse(ctx, obj.x, obj.y, obj.width, obj.height)
	elif obj.type == ShapeType.rectangle:
		draw_rectangle(ctx, obj.x, obj.y, obj.width, obj.height)


def draw_box_ellipse(ctx, x, y, width, height):
	ctx.save()
	ctx.translate(x + width / 2.0, y + height / 2.0)
	ctx.scale(width / 2.0, height / 2.0)
	ctx.arc(0, 0, 1, 0, 2 * math.pi)
	ctx.set_source_rgb(1, 0, 0)
	ctx.set_line_width(0.01)
	#ctx.stroke()
	print("clip1: %s %s %s %s" % ctx.clip_extents())
	#ctx.clip()
	print("clip2: %s %s %s %s" % ctx.clip_extents())
	ctx.restore() # TODO what effect does this has
	print("clip3: %s %s %s %s" % ctx.clip_extents())


def draw_rectangle(ctx, x, y, width, height):
	ctx.save()
	print("clip1: %s %s %s %s" % ctx.clip_extents())
	ctx.rectangle(x, y, width, height)
	ctx.set_source_rgb(1, 0, 0)
	ctx.set_line_width(0.01)
	print("clip2: %s %s %s %s" % ctx.clip_extents())
	ctx.restore() # TODO what effect does this has
	print("clip3: %s %s %s %s" % ctx.clip_extents())


def draw_text(ctx, obj, text, debug=False):
	ctx.save()

	lyt = PangoCairo.create_layout(ctx)
	pg_ctx = lyt.get_context()

	fo = cairo.FontOptions()
	fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
	PangoCairo.context_set_font_options(pg_ctx, fo)
	font = Pango.FontDescription("Belwe Bd BT %dpx" % (obj.height * 1.3))
	lyt.set_font_description(font)
	lyt.set_text(text, -1) # force length calculation

	# lyt.set_height(obj["height"])
	# lyt.set_width(obj["height"])
	# PangoCairo.update_layout(ctx, lyt)

	pg_size = lyt.get_pixel_size()
	ink, logical = lyt.get_pixel_extents()
	if debug:
		print("pg: %s x %s" % pg_size)
		print("ink: %s %s %s %s" % (ink.x, ink.y, ink.width, ink.height))
		print("logical: %s %s %s %s" % (logical.x, logical.y, logical.width, logical.height))
		print("spacing: %s" % (lyt.get_spacing()))
		print("height: %s" % (lyt.get_height()))
		print("width: %s" % (lyt.get_width()))

	#x = obj["x"] - pext.x - pext.width / 2
	#y = obj["y"] - pext.y - pext.height / 2
	x = (obj.x + obj.width / 2) - ((ink.x + ink.width / 2))
	y = (obj.y + obj.height / 2) - ((ink.y + ink.height / 2))
	if debug:
		print("x,y: %s, %s" % (x, y))
	ctx.translate(x, y)

	PangoCairo.update_layout(ctx, lyt)
	PangoCairo.layout_path(ctx, lyt)
	ctx.set_line_width(9.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.set_line_join(cairo.LINE_JOIN_ROUND)
	ctx.set_source_rgb(0, 0, 0)
	ctx.stroke()

	ctx.set_source_rgb(1, 1, 1)
	PangoCairo.show_layout(ctx, lyt)

	if debug:
		ctx.rectangle(ink.x, ink.y, ink.width, ink.height)
		ctx.set_line_width(2.0)
		ctx.set_line_join(cairo.LINE_JOIN_MITER)
		ctx.set_source_rgb(0, 0.8, 0)
		ctx.stroke()
		ctx.rectangle(logical.x, logical.y, logical.width, logical.height)
		ctx.set_line_width(2.0)
		ctx.set_line_join(cairo.LINE_JOIN_MITER)
		ctx.set_source_rgb(0, 0.2, 0.9)
		ctx.stroke()

	ctx.restore()

	if debug:
		#draw_crosshair(ctx, obj["x"] + obj["width"] / 2, obj["y"] + obj["height"] / 2, 20, (1, 1, 1))
		draw_crosshair(ctx, obj.x, obj.y, 20, (1, 1, 1))


def draw_powers(ctx, obj, text, debug=False):
	ctx.save()

	lyt = PangoCairo.create_layout(ctx)
	pg_ctx = lyt.get_context()

	fo = cairo.FontOptions()
	fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
	PangoCairo.context_set_font_options(pg_ctx, fo)
	font = Pango.FontDescription("Franklin Gothic FS 38px")
	# font.set_stretch(Pango.Stretch.ULTRA_EXPANDED)
	# print(">>>>>", font.get_stretch())
	lyt.set_font_description(font)
	lyt.set_markup(text, -1) # force length calculation
	#lyt.set_markup(
	#	'<span font_family="sans" font_stretch="expanded" letter_spacing="100" font_weight="bold">SANS</span>', -1)

	lyt.set_height(obj["height"] * Pango.SCALE * 1.5)
	lyt.set_width(obj["width"] * Pango.SCALE)
	lyt.set_alignment(Pango.Alignment.CENTER)
	#PangoCairo.update_layout(ctx, lyt)

	pg_size = lyt.get_pixel_size()
	ink, logical = lyt.get_pixel_extents()
	print("pg: %s x %s" % pg_size)
	print("ink: %s %s %s %s" % (ink.x, ink.y, ink.width, ink.height))
	print("logical: %s %s %s %s" % (logical.x, logical.y, logical.width, logical.height))
	print("spacing: %s" % (lyt.get_spacing()))
	print("height: %s" % (lyt.get_height()))
	print("width: %s" % (lyt.get_width()))

	#x = obj["x"] - pext.x - pext.width / 2
	#y = obj["y"] - pext.y - pext.height / 2
	x = (obj["x"] + obj["width"] / 2) - ((ink.x + ink.width / 2))
	y = (obj["y"] + obj["height"] / 2) - ((ink.y + ink.height / 2))
	#x = obj["x"]
	#y = obj["y"]
	print("x,y: %s, %s" % (x, y))
	ctx.translate(x, y)

	PangoCairo.update_layout(ctx, lyt)
	PangoCairo.layout_path(ctx, lyt)
	ctx.set_line_width(9.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.set_line_join(cairo.LINE_JOIN_ROUND)
	ctx.set_source_rgb(0, 0, 0)
	#ctx.stroke()

	#ctx.set_source_rgb(1, 1, 1)
	PangoCairo.show_layout(ctx, lyt)
	ctx.new_path()
	if debug:
		ctx.rectangle(ink.x, ink.y, ink.width, ink.height)
		ctx.set_line_width(2.0)
		ctx.set_line_join(cairo.LINE_JOIN_MITER)
		ctx.set_source_rgb(0, 0.8, 0)
		ctx.stroke()
		ctx.rectangle(logical.x, logical.y, logical.width, logical.height)
		ctx.set_line_width(2.0)
		ctx.set_line_join(cairo.LINE_JOIN_MITER)
		ctx.set_source_rgb(0, 0.2, 0.9)
		ctx.stroke()

	ctx.restore()

	if debug:
		#draw_crosshair(ctx, obj["x"] + obj["width"] / 2, obj["y"] + obj["height"] / 2, 20, (1, 1, 1))
		draw_crosshair(ctx, obj["x"], obj["y"], 20, (1, 1, 1))


def setup_context(width, height):
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	ctx = cairo.Context(surface)
	#ctx.scale(width, height) # Normalizing the canvas
	ctx.set_source_rgba(0, 0, 0, 0) # transparent bg
	ctx.paint()
	return (ctx, surface)


def draw_curved_text(ctx, obj, text):
	curve = CubicBezier(
		obj.start.x, obj.start.y, obj.c1.x, obj.c1.y,
		obj.c2.x, obj.c2.y, obj.end.x, obj.end.y)
	text = CurvedText(curve, "Belwe Bd BT", 30, text)
	text.draw(ctx)


def render_component(context, component, data):
	print(component.type)
	# first check if there is a clipping region
	if component.clip:
		# TODO get shape type
		draw_clip_region(context, component.clip)
		context.clip()
	# draw image
	if component.image and data.override:
		draw_image_override(context, component.image, artwork, data.override)
		# reset the clip TODO maybe only when actually clipped
		context.reset_clip()
	elif component.image and data.key in component.image.assets:
		draw_image(context, component.image, data.key)
		# reset the clip TODO maybe only when actually clipped
		context.reset_clip()
	# draw text next
	if component.text and data.text:
		draw_text(context, component.text, data.text)
	# draw curved text if any
	if component.curve and data.text:
		draw_curved_text(context, component.curve, data.text)
	# custom handling
	if component.custom:
		if hasattr(custom, component.custom["name"]):
			func = getattr(custom, component.custom["name"])
			func(context, component, data.data)


def main():
	# sample card id param
	card_id = "LOE_076"
	if len(sys.argv) > 1:
		card_id = sys.argv[1]

	# load card data
	db, xml = load(card_xml)
	if card_id in db:
		card = db[card_id]
	else:
		print("Unknown card {}".format(card_id))
		return

	# load theme data
	with open(theme + dataFilename) as f:
		themeData = json.load(f)

	cardType = card.type.name.lower()
	if cardType in themeData:
		data = themeData[cardType]
	else:
		print("{} not found".format(cardType))
		return

	components = []
	for ct in ComponentType:
		obj = data.get(ct.name)
		if obj:
			cp = Component(data[ct.name], ct)
			components.append(cp)
	components.sort(key=attrgetter("layer"))

	ctx, surface = setup_context(data["width"], data["height"])

	for c in components:
		cdata = None

		if c.type == ComponentType.name:
			cdata = ComponentData("default", card.name)
		elif c.type == ComponentType.elite and card.elite:
			cdata = ComponentData("default")
		elif c.type == ComponentType.rarity and card.rarity.craftable: # TODO check correctness
			cdata = ComponentData(card.rarity.name.lower())
		elif c.type == ComponentType.multiClass and card.multi_class_group != 0: # TODO use actual invalid enum
			cdata = ComponentData(card.multi_class_group.name.lower())
		elif c.type == ComponentType.classDecoration:
			cdata = ComponentData(card.card_class.name.lower())
		elif c.type == ComponentType.cost:
			cdata = ComponentData("default", str(card.cost))
		elif c.type == ComponentType.health:
			cdata = ComponentData("default", str(card.health))
		elif c.type == ComponentType.attack:
			cdata = ComponentData("default", str(card.atk))
		elif c.type == ComponentType.race and card.race.visible:
			cdata = ComponentData("default", card.race.name.lower())
		elif c.type == ComponentType.portrait:
			cdata = ComponentData(None, None, card.id + ".png")
		elif c.type == ComponentType.base:
			cdata = ComponentData("default")
		elif c.type == ComponentType.cardSet:
			# TODO need to rework theme dir here and elsewehre
			# TODO pass on premium state, taken from input?
			# TODO card type, can get this from cardxml?
			cdata = ComponentData(None,
				data={"card": card, "dir": theme, "premium": False, "cardtype": "minion"})

		if cdata:
			render_component(ctx, c, cdata)


	surface.flush()
	surface.write_to_png("./output/output.png")

if __name__ == "__main__":
	main()
