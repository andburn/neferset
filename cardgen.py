#!/usr/bin/env python

import math
import json
import os.path
from operator import itemgetter, attrgetter
from enum import Enum
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from curved import CubicBezier, CurvedText
from hearthstone.cardxml import load

assets = "../hearthforge/gaunt/minion/"
minion = "../hearthforge/gaunt/minion/data.json"
artwork = "./output/artwork/"
card_xml = "./output/CardDefs.xml"

class ComponentType(Enum):
	powers = 1
	elite = 2
	health = 3
	cost = 4
	attack = 5
	name = 6
	multiClass = 7
	race = 8
	rarity = 9
	cardSet = 10
	classDecoration = 11
	base = 12
	portrait = 13


class ShapeType(Enum):
	rectangle = 1
	ellipse = 2
	curve = 3


class Region:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def __str__(self):
		return "({}, {}, {}, {})".format(self.x, self.y, self.width, self.height)



class Shape(Region):
	def __init__(self, type, x, y, width, height):
		super().__init__(x, y, width, height)
		self.type = type


class Image(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]
		self.assets = data["assets"]


class Text(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]


class Clip(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]
		self.type = ShapeType[data["type"]]

class Point:
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]

	def __str__(self):
		return "({}, {})".format(self.x, self.y)


class Curve:
	def __init__(self, data):
		self.start = Point(data["start"])
		self.end = Point(data["end"])
		self.c1 = Point(data["c1"])
		self.c2 = Point(data["c2"])

	def __str__(self):
		return "{} {} {} {}".format(self.start, self.c1, self.c2, self.end)


class Component:
	def __init__(self, data, type):
		self.layer = data["layer"]
		txt = data.get("text")
		self.text = Text(txt) if txt else None
		img = data.get("image")
		self.image = Image(img) if img else None
		clp = data.get("clipRegion")
		self.clip = Clip(clp) if clp else None
		crv = data.get("textCurve")
		self.curve = Curve(crv) if crv else None
		self.type = type

	def __str__(self):
		return "({}) {}, {}, {}, {}, {}".format(self.type.name, self.layer, self.text, self.image, self.clip, self.curve)


class ComponentData:
	def __init__(self, key, text=None, override=None):
		self.key = key
		self.text = text
		self.override = override


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
	file_path = os.path.join(assets, image.assets[key])
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
	ctx.translate(x, y)
	ctx.rectangle(x, y, width, height)
	ctx.set_source_rgb(1, 0, 0)
	ctx.set_line_width(0.01)
	#ctx.stroke()
	print("clip1: %s %s %s %s" % ctx.clip_extents())
	#ctx.clip()
	print("clip2: %s %s %s %s" % ctx.clip_extents())
	ctx.restore() # TODO what effect does this has
	print("clip3: %s %s %s %s" % ctx.clip_extents())


def get_components(json, id):
	objs = []
	json["portrait"]["image"] = artwork + id + ".png"
	json["base"]["image"] = assets + json["base"]["variants"]["neutral"]
	json["rarity"]["image"] = assets + json["rarity"]["variants"]["legendary"]
	json["health"]["image"] = assets + json["health"]["image"]
	json["attack"]["image"] = assets + json["attack"]["image"]
	json["cost"]["image"] = assets + json["cost"]["image"]
	json["banner"]["image"] = assets + json["banner"]["image"]
	json["rarityFrame"]["image"] = assets + json["rarityFrame"]["image"]
	json["race"]["image"] = assets + json["race"]["image"]
	objs.append(json["portrait"])
	objs.append(json["base"])
	objs.append(json["rarity"])
	objs.append(json["health"])
	objs.append(json["attack"])
	objs.append(json["cost"])
	objs.append(json["banner"])
	objs.append(json["rarityFrame"])
	objs.append(json["race"])
	return objs


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


def main():
	with open(minion) as f:
		data = json.load(f)

	with open(cards) as f:
		cards_data = json.load(f)

	WIDTH = data["width"]
	HEIGHT = data["height"]

	for card in cards_data:
		components = get_components(data, card["id"])

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
		ctx = cairo.Context(surface)
		#ctx.scale(WIDTH, HEIGHT) # Normalizing the canvas
		ctx.set_source_rgba(0, 0, 0, 0) # transparent bg
		ctx.paint()

		components = sorted(components, key=itemgetter("index"))
		for c in components:
			if artwork in c["image"]:
				# clip portrait TODO from data in json
				draw_box_ellipse(ctx, 154, 78, 332, 450)
				ctx.clip()
				print("clip4: %s %s %s %s" % ctx.clip_extents())
				draw_image(ctx, c)
				ctx.reset_clip()
			else:
				draw_image(ctx, c)

		# add text
		dbg = True
		draw_text(ctx, data["text"]["cost"], str(card["cost"]), dbg)
		draw_text(ctx, data["text"]["health"], str(card["health"]), dbg)
		draw_text(ctx, data["text"]["attack"], str(card["attack"]), dbg)
		draw_text(ctx, data["text"]["race"], "Murloc", dbg)
		draw_powers(ctx, data["text"]["powers"], card["text"], dbg)
		# add title
		#ctx.translate(-170, -105)
		cpts = data["text"]["name"]
		#curve = CubicBezier(276, 578, 362, 610, 592, 499, 731, 574)
		curve = CubicBezier(
			cpts["start"]["x"], cpts["start"]["y"],
			cpts["controlPoint1"]["x"], cpts["controlPoint1"]["y"],
			cpts["controlPoint2"]["x"], cpts["controlPoint2"]["y"],
			cpts["end"]["x"], cpts["end"]["y"])
		text = CurvedText(curve, "Belwe Bd BT", 30, card["name"])
		text.draw(ctx)
		#ctx.new_path()
		#text.draw_curve(ctx)

		## TEST
		#tcost = json.loads(data["text"]["cost"], object_hook=as_shape)
		#print(tcost)

		surface.flush()
		surface.write_to_png("./output/output.png")

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


def test():
	# load card data
	db, xml = load(card_xml)
	card = db["AT_027"]

	# load theme data
	with open(minion) as f:
		data = json.load(f)

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

		if cdata:
			render_component(ctx, c, cdata)


	surface.flush()
	surface.write_to_png("./output/output.png")

test()
