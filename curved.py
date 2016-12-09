import math


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
	def __init__(self, p0, p1, p2, p3):
		self.p0 = p0
		self.p1 = p1
		self.p2 = p2
		self.p3 = p3
		self.a, self.e = p3 - p2 * 3 + p1 * 3 - p0
		self.b, self.f = 3 * p2 - 6 * p1 + 3 * p0
		self.c, self.g = 3 * p1 - 3 * p0
		self.d, self.h = p0
		self._arc_lengths = []
		self._length = 0

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


class TextCurve(object):
	def __init__(self, start, c1, c2, end):
		self.bezier = CubicBezier(start, c1, c2, end)


def main():
	p1 = Point(2, 4)
	p2 = Point(0.3, -1.9)
	print(p1)
	print(p2)
	print(p1 + p2)
	print(p1 - p2)
	print(p1 * 3)
	print(p2 * 0.21)
	print(p1.distance(p2))
	cb = CubicBezier(p1, p1*2, p1*3, p2)
	print(cb)
	tt = cb.evaluate(0.3)
	print(tt)
	print(cb.length)
	print(cb.arc_lengths)
	a, b = p2
	print("{},{}".format(a,b))

if __name__ == "__main__":
	main()
