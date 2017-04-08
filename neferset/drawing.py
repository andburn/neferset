import math
import os
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo


def xheight(pg_ctx):
	pg_ctx.set_text("X", -1)
	return pg_ctx.get_pixel_extents()[0]


def text_path(context, font, size, text, debug=False):
	"""Create a Pango text layout and return it as a Cairo path"""

	context.save()

	pg_layout = PangoCairo.create_layout(context)
	pg_context = pg_layout.get_context()

	font_options = cairo.FontOptions()
	font_options.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
	PangoCairo.context_set_font_options(pg_context, font_options)
	font_descp = "{0} {1:d}".format(font, size)
	pg_layout.set_font_description(Pango.FontDescription(font_descp))
	pg_layout.set_text(text, -1) # force length calculation

	PangoCairo.update_layout(context, pg_layout)
	# TODO watch out for ink & logical, need check
	extents = pg_layout.get_pixel_extents()[0]
	# TODO debug necessary?
	if debug:
		context.set_source_rgb(0, 0, 0)
		PangoCairo.show_layout(context, pg_layout)
		print("text_path: ({0}, {1}, {2}, {3})".format(
			extents.x, extents.y, extents.width, extents.height))
		context.rectangle(extents.x, extents.y, extents.width, extents.height)
		context.set_line_width(1.0)
		context.set_line_join(cairo.LINE_JOIN_MITER)
		context.set_source_rgb(0, 0.8, 0)
		context.stroke()

	#PangoCairo.layout_path(context, pg_layout)
	PangoCairo.layout_line_path(context, pg_layout.get_line(0))
	path = context.copy_path()
	# clear the path
	context.new_path()
	context.restore()
	return (path, extents, xheight(pg_layout).height)


def path_with_control_points(context, preserve=False):
	"""Stroke the current path and draw any curves control points.

	Taken from pango/examples/twisted.c
	"""
	dash = (10, 10)

	context.save()
	context.set_source_rgb(1, 0, 0)

	line_width = context.get_line_width()
	path = context.copy_path()
	context.new_path()

	context.save()
	context.set_line_width(line_width / 3)
	context.set_dash(dash)
	for type, points in path:
		if type == cairo.PATH_MOVE_TO or type == cairo.PATH_LINE_TO:
			context.move_to(*points)
		elif type == cairo.PATH_CURVE_TO:
			x1, y1, x2, y2, x3, y3 = points
			context.line_to(x1, y1)
			context.move_to(x2, y2)
			context.line_to(x3, y3)
	context.stroke()
	context.restore()

	context.save()
	context.set_line_width(line_width * 4)
	context.set_line_cap(cairo.LINE_CAP_ROUND)
	for type, points in path:
		if type == cairo.PATH_MOVE_TO:
			context.move_to(*points)
		elif type == cairo.PATH_LINE_TO:
			context.rel_line_to(0, 0)
			context.move_to(*points)
		elif type == cairo.PATH_CURVE_TO:
			x1, y1, x2, y2, x3, y3 = points
			context.rel_line_to(0, 0)
			context.move_to(x1, y1)
			context.rel_line_to(0, 0)
			context.move_to(x2, y2)
			context.rel_line_to(0, 0)
			context.move_to(x3, y3)
		elif type == cairo.PATH_CLOSE_PATH:
			cairo.rel_line_to(0, 0)
	context.stroke()
	context.restore()

	for type, points in path:
		if type == cairo.PATH_MOVE_TO:
			context.move_to(*points)
		elif type == cairo.PATH_LINE_TO:
			context.line_to(*points)
		elif type == cairo.PATH_CURVE_TO:
			context.curve_to(*points)
		elif type == cairo.PATH_CLOSE_PATH:
			context.close_path()

	context.stroke()

	if preserve:
		context.append_path(path)

	context.restore()


def crosshair(ctx, x, y, length, color=None):
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


def rect_ellipse(ctx, x, y, width, height, draw=True, stroke=0.5, color=(0, 0, 0)):
	"""Draw an ellipse fitting a rectangle."""
	ctx.save()
	ctx.translate(x + width / 2.0, y + height / 2.0)
	ctx.scale(width / 2.0, height / 2.0)
	ctx.arc(0, 0, 1, 0, 2 * math.pi)
	ctx.set_source_rgb(*color)
	ctx.set_line_width(stroke)
	if draw:
		ctx.stroke()
	ctx.restore()


def rectangle(ctx, x, y, width, height, draw=True, stroke=0.5, color=(0, 0, 0)):
	ctx.save()
	ctx.rectangle(x, y, width, height)
	ctx.set_source_rgb(*color)
	ctx.set_line_width(stroke)
	if draw:
		ctx.stroke()
	ctx.restore()


def polygon(ctx, points, draw=True, stroke=0.5, color=(0, 0, 0)):
	if len(points) <= 0:
		return
	ctx.save()
	start = points[0]
	ctx.move_to(start["x"], start["y"])
	for i in range(1, len(points)):
		ctx.line_to(points[i]["x"], points[i]["y"])
	ctx.line_to(start["x"], start["y"])
	ctx.set_source_rgb(*color)
	ctx.set_line_width(stroke)
	ctx.restore()


def text(ctx, obj, text, font, lang="en-US", debug=False):
	ctx.save()

	lyt = PangoCairo.create_layout(ctx)
	pg_ctx = lyt.get_context()
	pg_ctx.set_language(Pango.Language.from_string(lang))

	fo = cairo.FontOptions()
	fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
	PangoCairo.context_set_font_options(pg_ctx, fo)
	font_family = font.family if not font.replace else font.replace
	pg_font = Pango.FontDescription("{} {}px".format(font_family, font.size))
	lyt.set_font_description(pg_font)
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

	if font.outline:
		# set stroke outline
		stroke_width = font.size * 0.066
		stroke_width = 5.0 if stroke_width < 5.0 else stroke_width

		ctx.set_line_width(stroke_width)
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		ctx.set_line_join(cairo.LINE_JOIN_ROUND)
		ctx.set_source_rgb(*font.outline)
		ctx.stroke()

	ctx.set_source_rgb(*font.color)
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
		#crosshair(ctx, obj["x"] + obj["width"] / 2, obj["y"] + obj["height"] / 2, 20, (1, 1, 1))
		crosshair(ctx, obj.x, obj.y, 20, (1, 1, 1))


def text_block(ctx, obj, text, font, lang="en-US", debug=False):
	ctx.save()

	lyt = PangoCairo.create_layout(ctx)
	pg_ctx = lyt.get_context()
	pg_ctx.set_language(Pango.Language.from_string(lang))

	fo = cairo.FontOptions()
	fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
	PangoCairo.context_set_font_options(pg_ctx, fo)
	font_family = font.family if not font.replace else font.replace
	pg_font = Pango.FontDescription("{} {}px".format(font_family, font.size))
	lyt.set_font_description(pg_font)
	lyt.set_markup(text, -1) # force length calculation

	lyt.set_height(obj.height * Pango.SCALE * 1.5) # TODO what?
	lyt.set_width(obj.width * Pango.SCALE)
	lyt.set_alignment(Pango.Alignment.CENTER)
	#PangoCairo.update_layout(ctx, lyt)

	pg_size = lyt.get_pixel_size()
	ink, logical = lyt.get_pixel_extents()

	while ink.height > obj.height and pg_font.get_size() > 0:
		pg_font.set_size(pg_font.get_size() - Pango.SCALE)
		lyt.set_font_description(pg_font)
		ink, logical = lyt.get_pixel_extents()

	#x = obj["x"] - pext.x - pext.width / 2
	#y = obj["y"] - pext.y - pext.height / 2
	x = (obj.x + obj.width / 2) - ((ink.x + ink.width / 2))
	y = (obj.y + obj.height / 2) - ((ink.y + ink.height / 2))
	#x = obj["x"]
	#y = obj["y"]
	if debug:
		print("x,y: %s, %s" % (x, y))
	ctx.translate(x, y)

	PangoCairo.update_layout(ctx, lyt)
	PangoCairo.layout_path(ctx, lyt)
	ctx.set_line_width(9.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.set_line_join(cairo.LINE_JOIN_ROUND)
	ctx.set_source_rgb(*font.color)
	PangoCairo.show_layout(ctx, lyt)

	ctx.new_path()
	ctx.restore()

	if debug:
		rectangle(ctx, ink.x, ink.y, ink.width, ink.height, True, 2.0, (0, 1, 0))
		rectangle(ctx, obj.x, obj.y, obj.width, obj.height, True, 2.0, (0.8, 0.8, 0))


def get_scale(img, w, h):
	return (round(float(w) / img.get_width(), 2), round(float(h) / img.get_height(), 2))


def draw_png_asset(context, image, dir, f):
	file = f
	if f in image.assets:
		file = image.assets[f]
	file_path = os.path.join(dir, file)
	draw_png_at(context, file_path, image.x, image.y, image.width, image.height)


def draw_png_at(context, file, x, y, w, h):
	if not os.path.isfile(file):
		print("File ({}) not found".format(file))
		return
	context.save()
	img = cairo.ImageSurface.create_from_png(file)
	scale = get_scale(img, w, h)
	context.translate(x, y)
	context.scale(*scale) # TODO only scale when no (1, 1)
	context.set_source_surface(img)
	context.paint()
	context.restore()
