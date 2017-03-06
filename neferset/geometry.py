import math

class Vector4():
	def __init__(self, *args):
		if len(args) == 4:
			self.x = args[0]
			self.y = args[1]
			self.z = args[2]
			self.w = args[3]
		else:
			raise ValueError("Wrong number of arguments ({})".format(len(args)))

	@property
	def r(self):
		return self.x

	@r.setter
	def r(self, value):
		self.x = value

	@property
	def g(self):
		return self.y

	@g.setter
	def g(self, value):
		self.y = value

	@property
	def b(self):
		return self.z

	@b.setter
	def b(self, value):
		self.z = value

	@property
	def a(self):
		return self.w

	@a.setter
	def a(self, value):
		self.w = value

	def __add__(self, o):
		try:
			out = Vector4(self.x + o.x, self.y + o.y, self.z + o.z, self.w + o.w)
		except AttributeError:
			out = Vector4(self.x + o, self.y + o, self.z + o, self.w + o)
		return out

	def __sub__(self, o):
		try:
			out = Vector4(self.x - o.x, self.y - o.y, self.z - o.z, self.w - o.w)
		except AttributeError:
			out = Vector4(self.x - o, self.y - o, self.z - o, self.w - o)
		return out

	def __mul__(self, o):
		try:
			out = Vector4(self.x * o.x, self.y * o.y, self.z * o.z, self.w * o.w)
		except AttributeError:
			out = Vector4(self.x * o, self.y * o, self.z * o, self.w * o)
		return out

	def __rmul__(self, s):
		return Vector4(self.x * s, self.y * s, self.z * s, self.w * s)

	def __iter__(self):
		yield self.x
		yield self.y
		yield self.z
		yield self.w

	def __str__(self):
		return "({:.2f}, {:.2f}, {:.2f}, {:.2f})".format(self.x, self.y, self.z, self.w)

	def __repr__(self):
		return "{}({}, {}, {}, {})".format(self.__class__.__name__, self.x, self.y, self.z, self.w)


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
