import sys
import math
import cairo
import drawing


class Point:
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y

	def __add__(self, p):
		return Point(self.x + p.x, self.y + p.y)

	def __sub__(self, p):
		return Point(self.x - p.x, self.y - p.y)

	def __mul__(self, s):
		return Point(self.x * s, self.y * s)

	def __rmul__(self, s):
		return Point.__mul__(self, s)

	def __div__(self, s):
		return Point(self.x / s, self.y / s)

	def distance(self, p):
		return math.sqrt((p.x - self.x) ** 2 + (p.y - self.y) ** 2)

	def clone(self):
		return Point(self.x, self.y)

	def __iter__(self):
		yield self.x
		yield self.y

	def __str__(self):
		return "({0:.2f}, {1:.2f})".format(self.x, self.y)

	def __repr__(self):
		return "{0}({1}, {2})".format(self.__class__.__name__, self.x, self.y)


class CubicBezier:
	def __init__(self, *args):
		if len(args) == 8:
			self._from_coords(*args)
		elif len(args) == 4:
			self._from_points(*args)
		else:
			raise ValueError("Wrong number of arguments")
		self._arc_lengths = []
		self._length = 0

	def _from_points(self, p0, p1, p2, p3):
		self.p0 = p0
		self.p1 = p1
		self.p2 = p2
		self.p3 = p3
		self.a, self.e = p3 - p2 * 3 + p1 * 3 - p0
		self.b, self.f = 3 * p2 - 6 * p1 + 3 * p0
		self.c, self.g = 3 * p1 - 3 * p0
		self.d, self.h = p0

	def _from_coords(self, x0, y0, x1, y1, x2, y2, x3, y3):
		self._from_points(Point(x0, y0), Point(x1, y1), Point(x2, y2), Point(x3, y3))

	@property
	def arc_lengths(self):
		if len(self._arc_lengths) <= 0:
			self._length = self.estimate_length()
		return self._arc_lengths

	@property
	def length(self):
		if self._length <= 0:
			self._length = self.estimate_length()
		return self._length

	def evaluate(self, t):
		return Point(
			self.a * t ** 3 + self.b * t ** 2 + self.c * t + self.d,
		 	self.e * t ** 3 + self.f * t ** 2 + self.g * t + self.h)

	def tangent(self, t):
		return Point(
			3 * self.a * t ** 2 + 2 * self.b * t + self.c,
			3 * self.e * t ** 2 + 2 * self.f * t + self.g)

	def parametrize(self, u):
		table_len = len(self.arc_lengths)
		target_len = u * self.arc_lengths[table_len - 1]
		index, best = 0, 0
		# TODO could make this faster search, binary
		for i, v in enumerate(self.arc_lengths):
			if i >= table_len - 1:
				break
			if v < target_len and v > best:
				best = v
				index = i

		if self.arc_lengths[index] == target_len:
			t = index / (table_len - 1)
		else:
			lb = self.arc_lengths[index]
			la = self.arc_lengths[index + 1]
			seg_len = la - lb
			seg_frac = (target_len - lb) / seg_len
			t = (index + seg_frac) / (table_len - 1)

		return t

	def estimate_length(self, segments=100):
		max = segments + 1
		prev = self.evaluate(0)
		self._arc_lengths = [0]
		sum = 0
		for i in range(1, max + 1):
			p = self.evaluate(i / max)
			sum += prev.distance(p)
			prev = p
			self._arc_lengths.append(sum)
		return sum

	def __str__(self):
		return "{0}t^3 + {1}t^2 + {2}t + {3}".format(self.a, self.b, self.c, self.d)

	def __repr__(self):
		return "{0}({1}, {2}, {3}, {4})".format(
			self.__class__.__name__, self.p0, self.p1, self.p2, self.p3)


class CurvedText:
	def __init__(self, bezier, font, size, text):
		self.curve = bezier
		self.font = font
		self.size = size
		self.text = text

	def draw_curve(self, context):
		context.save()
		context.move_to(self.curve.p0.x, self.curve.p0.y)
		context.curve_to(self.curve.p1.x, self.curve.p1.y,
			self.curve.p2.x, self.curve.p2.y, self.curve.p3.x, self.curve.p3.y)
		context.set_line_width(2.0)
		context.set_source_rgb(1, 0, 0)
		#context.stroke()
		drawing.path_with_control_points(context)
		context.restore()

	def draw(self, context):
		context.save()

		# reduce the font size, until its <= the curve length
		# TODO could use some estimate to speed this up
		size_step = 1
		size = self.size
		while True:
			path, extents = drawing.text_path(context, self.font, size, self.text)
			if extents.width > self.curve.length:
				size -= size_step
			else:
				break

		width = extents.width
		# Centre when shorter than curve length
		length = self.curve.length
		if width < length:
			r = width / float(length)
			half = r / 2
			minr = 0.5 - half
			maxr = 0.5 + half
			rng = (minr, maxr)
			print(rng)
		else:
			rng = (0, 1)

		context.new_path()
		for ptype, pts in path:
			if ptype == cairo.PATH_MOVE_TO:
				x, y = self._fit(width, pts[0], pts[1], rng)
				context.move_to(x, y)
			elif ptype == cairo.PATH_LINE_TO:
				x, y = self._fit(width, pts[0], pts[1], rng)
				context.line_to(x,y)
			elif ptype == cairo.PATH_CURVE_TO:
				x, y = self._fit(width, pts[0], pts[1], rng)
				u, v = self._fit(width, pts[2], pts[3], rng)
				s, t = self._fit(width, pts[4], pts[5], rng)
				context.curve_to(x, y, u, v, s, t)
			elif ptype == cairo.PATH_CLOSE_PATH:
				context.close_path()

		context.set_source_rgb(0, 0, 0)
		# TODO stroke width needs to scale with font size
		context.set_line_cap(cairo.LINE_CAP_ROUND)
		context.set_line_join(cairo.LINE_JOIN_ROUND)
		context.set_line_width(6)
		context.stroke_preserve()
		context.set_source_rgb(1, 1, 1)
		context.fill()
		context.restore()

	def _fit(self, width, x, y, range=(0, 1)):
		r = x / width
		nmin, nmax = range
		nrng = nmax - nmin
		nt = r * nrng + nmin

		t = self.curve.parametrize(nt)
		sx, sy = self.curve.evaluate(t)

		tx, ty = self.curve.tangent(t)
		px = -ty
		py = tx

		mag = math.sqrt(px ** 2 + py ** 2)
		px = px / mag
		py = py / mag

		px *= y
		py *= y

		fx = px + sx
		fy = py + sy

		return (fx, fy)


def draw_uniform_t(ctx, num, curve):
	ctx.save()
	ctx.set_source_rgb(0.2, 0.8, 0.4)
	for i in range(1, num):
		t = i / num
		sx, sy = curve.evaluate(t)
		ctx.arc(sx, sy, 2, 0, 2 * math.pi)
		ctx.fill()
	for t in (0, 0.5, 1):
		sx, sy = curve.evaluate(t)
		ctx.arc(sx, sy, 4, 0, 2 * math.pi)
		ctx.fill()
	ctx.restore()


def draw_uniform_p(ctx, num, curve):
	ctx.save()
	ctx.set_source_rgb(0.2, 0.8, 0.4)
	for i in range(1, num):
		u = i / num
		t = curve.parametrize(u)
		sx, sy = curve.evaluate(t)
		ctx.arc(sx, sy, 2, 0, 2 * math.pi)
		ctx.fill()
	for u in (0, 0.5, 1):
		t = curve.parametrize(u)
		sx, sy = curve.evaluate(t)
		ctx.arc(sx, sy, 4, 0, 2 * math.pi)
		ctx.fill()
	ctx.restore()


def main():
	WIDTH = 1024
	HEIGHT = 1024

	title_text = "Sample Text"
	if len(sys.argv) > 1:
		title_text = sys.argv[1]

	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
	ctx = cairo.Context(surface)
	ctx.set_source_rgb(1, 1, 1)
	ctx.paint()

	curve = CubicBezier(276, 578, 362, 610, 592, 499, 731, 574)
	text = CurvedText(curve, "Belwe Bd BT", 50, title_text)
	text.draw(ctx)

	draw_uniform_p(ctx, 20, curve)

	surface.flush()
	surface.write_to_png("output/output.png")


if __name__ == "__main__":
	main()
