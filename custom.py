def multiply(t1, t2):
	a = tuple(i / 255 for i in t1)
	b = tuple(i / 255 for i in t2)
	c = (a[0]*b[0], a[1]*b[1], a[2]*b[2], a[3]*b[3])
	return tuple(int(i * 255) for i in c)

def sub(t1, t2):
	a = tuple(i / 255 for i in t1)
	b = tuple(i / 255 for i in t2)
	c = (a[0]-b[0], a[1]-b[1], a[2]-b[2], a[3]-b[3])
	return tuple(int(i * 255) for i in c)

def add(t1, t2):
	a = tuple(i / 255 for i in t1)
	b = tuple(i / 255 for i in t2)
	c = (a[0]+b[0], a[1]+b[1], a[2]+b[2], a[3]+b[3])
	return tuple(int(i * 255) for i in c)

def scalar(t1, s):
	x = tuple((i / 255) * s for i in t1)
	return tuple(int(i * 255) for i in x)

def multiply2(b, f):
	b = tuple(i / 255 for i in b)
	x = (b[0] * f[0], b[1] * f[1], b[2] * f[2], b[3] * f[3])
	return tuple(int(i * 255) for i in x)

def get_image_name(type, premium, race, set):
	name = [type]
	if premium:
		name.append("_premium")
	if race:
		name.append("_race")
	name.append("_")
	name.append(set)
	return "".join(name)


def draw_image(ctx, file, x, y):
	import cairo
	# TODO could have a common draw image in drawing?
	ctx.save()
	img = cairo.ImageSurface.create_from_png(file)
	ctx.translate(x, y)
	ctx.set_source_surface(img)
	ctx.paint()
	ctx.restore()


def set_watermark(ctx, comp, data):
	''' Create the set watermark that appears on regular Hearthstone cards. '''

	from PIL import Image
	from os import listdir, makedirs
	from os.path import isfile, isdir, join
	import cardgen
	from hearthstone import enums

	race_offset = -16 # in respect to y coordinate only
	cache_dir = ".cache" # store generated images here for reuse
	file_ext = ".png" # set icon file extension

	card = data["card"]
	theme_dir = data["dir"]
	has_race = card.race != enums.Race.INVALID
	is_premium = data["premium"]
	card_type = data["cardtype"]

	# do nothing for non-craftable sets
	if not card.card_set.craftable:
		return
	set_name = card.card_set.name.lower()

	if not isdir(cache_dir):
		makedirs(cache_dir)

	# get the name for the generate image
	image_name = get_image_name(card_type, is_premium, has_race, set_name)
	image_path = join(cache_dir, "{}{}".format(image_name, file_ext))

	# load the data
	base_image = cardgen.Image(comp.custom["image"])
	set_region = cardgen.Region(
		comp.custom["region"]["x"],
		comp.custom["region"]["y"],
		comp.custom["region"]["width"],
		comp.custom["region"]["height"])

	# if there is a cached version of the image use it
	if isfile(image_path):
		draw_image(ctx, image_path, base_image.x, base_image.y)
		return

	# calc set offset within base
	offset = {
		"x": set_region.x - base_image.x,
		"y": set_region.y - base_image.y
	}
	# if a minion has a race, need offset watermark
	if has_race:
		offset["y"] += race_offset

	# check the icon exists for this set
	set_icon_path = join(theme_dir, comp.custom["setIcons"], "{}{}".format(set_name, file_ext))
	if not isfile(set_icon_path):
		print("ERROR: set icon missing for {}".format(set_name))

	# resize the set icon to the correct size
	set_org = Image.open(set_icon_path)
	set_resize = set_org.resize((set_region.width, set_region.height), Image.BILINEAR)
	set_img = Image.new("RGBA",
		(base_image.width, base_image.height),
		(0, 0, 0, 0))
	set_img.paste(set_resize, (offset["x"], offset["y"]))
	set_org.close()
	set_resize.close()

	# open base image
	base_img = Image.open(join(theme_dir, base_image.assets["default"]))

	# do the blend
	zero_p_five = (0.15, 0.15, 0.15, 0.15)
	intensity = comp.custom["blendIntensity"]
	# TODO better tint rep in json
	tint = comp.custom["tint"][card_type]
	tint = (tint["r"], tint["g"], tint["b"], tint["a"])
	r0_data = set_img.getdata()
	r1_data = base_img.getdata()

	# TODO not really necessary now
	if len(r0_data) != base_img.width * base_img.height and len(r0_data) != len(r1_data):
		print("ERROR: data size mismatch")

	out_data = []
	for i in range(len(r0_data)):
		r0 = r0_data[i]
		r1 = r1_data[i]
		if r0[3] == 0: # TODO ignore fully transparent pixels on set?
			out_data.append(r1)
			continue
		r0 = scalar(multiply2(r0, tint), intensity)
		r2 = sub(multiply(r1, r0), r1)
		r0 = add(scalar(r2, r0[3] / 255), r1)
		r0 = (r0[0], r0[1], r0[2], 255)
		out_data.append(r0)

	out = Image.new("RGBA", (base_img.width, base_img.height))
	out.putdata(out_data)
	out.save(image_path)

	draw_image(ctx, image_path, base_image.x, base_image.y)

	out.close()
	base_img.close()
	set_img.close()
