import cairo
from gi.repository import Pango
from gi.repository import PangoCairo


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
	if debug:
		PangoCairo.show_layout(context, pg_layout)
		pg_size = pg_layout.get_pixel_size()
		pext = pg_layout.get_pixel_extents()[0]
		print("text_path: {0} x {1} ({2}, {3}, {4}, {5})".format(
			pg_size[0], pg_size[1], pext.x, pext.y, pext.width, pext.height))
		context.rectangle(pext.x, pext.y, pext.width, pext.height)
		context.set_line_width(1.0)
		context.set_line_join(cairo.LINE_JOIN_MITER)
		context.set_source_rgb(0, 0.8, 0)
		context.stroke()

	PangoCairo.layout_path(context, pg_layout)
	path = context.copy_path()
	context.restore()
	return path


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
