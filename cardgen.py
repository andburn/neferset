#!/usr/bin/env python

import math
import json
import os.path
from operator import itemgetter
from enum import Enum
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from curved import CubicBezier, CurvedText

assets = "../hearthforge/default/minion/"
minion = "../hearthforge/default/minion/data.json"
artwork = "./output/artwork/"
cards = "./output/cardsample.json"


class ShapeType(Enum):
	rectangle = 1
	ellipse = 2
	curve = 3


class Shape:
	def __init__(self, type, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height


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

def draw_image(context, obj):
	if (not os.path.isfile(obj["image"])):
		print("Asset (%s) not found" % (obj["image"]))
		return
	context.save()
	img = cairo.ImageSurface.create_from_png(obj["image"])
	scl = get_scale(img, obj["width"], obj["height"])
	context.translate(obj["x"], obj["y"])
	context.scale(scl[0], scl[1]) # TODO only scale if not 1.0
	context.set_source_surface(img)
	context.paint()
	context.restore()

def draw_box_ellipse(ctx, x, y, width, height):
	ctx.save()
	ctx.translate(x + width / 2.0, y + height / 2.0)
	ctx.scale(width / 2.0, height / 2.0)
	ctx.arc(0, 0, 1, 0, 2 * math.pi)
	ctx.set_source_rgb(1, 0, 0)
	ctx.set_line_width(0.01)
	ctx.stroke_preserve()
	print("clip1: %s %s %s %s" % ctx.clip_extents())
	#ctx.clip()
	print("clip2: %s %s %s %s" % ctx.clip_extents())
	ctx.restore()
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
	font = Pango.FontDescription("Belwe Bd BT %dpx" % (obj["height"] * 1.3))
	lyt.set_font_description(font)
	lyt.set_text(text, -1) # force length calculation

	# lyt.set_height(obj["height"])
	# lyt.set_width(obj["height"])
	# PangoCairo.update_layout(ctx, lyt)

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
		draw_crosshair(ctx, obj["x"], obj["y"], 20, (1, 1, 1))


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
