import os
import os.path
from .component import Image, Region
from .geometry import Vector4
from .drawing import draw_png_at
from hearthstone.enums import Rarity, CardSet, Race


def rgb_to_bytes(color):
	"""Convert from fractional rgb values to a tuple of byte values."""
	return tuple(int(round(i * 255)) for i in color)


def rgb_from_bytes(color):
	"""Convert from byte rgb values to a Vector4 of fractional values."""
	return Vector4(*[i / 255 for i in color])


def set_watermark(ctx, comp, data):
	"""Create the set watermark that appears on regular Hearthstone cards."""
	from PIL import Image as ImagePIL

	cache_dir = ".cache" # store generated images here for reuse
	file_ext = ".png" # set icon file extension

	card = data["card"]
	theme_dir = data["dir"]
	has_race = card.race != Race.INVALID
	is_premium = data["premium"]
	card_type = data["cardtype"]
	race_offset = comp.custom["raceOffset"] # in respect to y coordinate only

	# ignore the core set
	if card.card_set == CardSet.CORE:
		return
	set_name = card.card_set.name.lower()

	if not os.path.isdir(cache_dir):
		os.makedir(cache_dir)

	# set the name for the generated image
	name = [card_type]
	if is_premium:
		name.append("_premium")
	if has_race:
		name.append("_race")
	name.append("_")
	name.append(set_name)
	image_name = "".join(name)
	image_path = os.path.join(cache_dir, "{}{}".format(image_name, file_ext))

	# load the data
	base_image = Image(comp.custom["image"])
	set_region = Region(
		comp.custom["region"]["x"],
		comp.custom["region"]["y"],
		comp.custom["region"]["width"],
		comp.custom["region"]["height"])

	# if there is a cached version of the image use it
	if os.path.isfile(image_path):
		draw_png_at(
			ctx, image_path, base_image.x, base_image.y, base_image.width,
			base_image.height)
		return

	# check the set icon exists
	set_icon_path = os.path.join(theme_dir,
		comp.custom["setIcons"], "{}{}".format(set_name, file_ext))
	if not os.path.isfile(set_icon_path):
		print("Warning: set icon missing for '{}'".format(set_name))
		return

	# calc set offset within base
	offset = {
		"x": set_region.x - base_image.x,
		"y": set_region.y - base_image.y
	}
	# if a minion has a race, need offset watermark
	if has_race:
		offset["y"] += race_offset

	# resize the set icon to the correct size
	set_org = ImagePIL.open(set_icon_path)
	set_resize = set_org.resize((set_region.width, set_region.height), ImagePIL.BILINEAR)
	set_img = ImagePIL.new("RGBA",
		(base_image.width, base_image.height),
		(0, 0, 0, 0))
	set_img.paste(set_resize, (offset["x"], offset["y"]))
	set_org.close()
	set_resize.close()

	# open the base image
	descp_img = ImagePIL.open(os.path.join(theme_dir, base_image.assets["base"]))

	# get the blending attributes
	intensity = comp.custom["blendIntensity"]
	tint = comp.custom["tint"]["premium" if is_premium else card_type]
	tint = Vector4(tint["r"], tint["g"], tint["b"], tint["a"])
	r0_data = set_img.getdata()
	r1_data = descp_img.getdata()

	# check nothing strange happened
	assert len(r0_data) == descp_img.width * descp_img.height, "data size mismatch"

	out_data = []
	# run the blending algorithm on each pixel pair
	for i in range(len(r0_data)):
		r0 = rgb_from_bytes(r0_data[i])
		r1 = rgb_from_bytes(r1_data[i])
		# speed up by ignoring fully transparent pixels on the set icon
		if r0.a == 0:
			out_data.append(rgb_to_bytes(r1))
			continue
		r0 = r0 * tint * intensity
		r2 = r1 * r0 - r1
		r0 = r2 * r0.a + r1
		r0.a = 1
		out_data.append(rgb_to_bytes(r0))

	out = ImagePIL.new("RGBA", (descp_img.width, descp_img.height))
	out.putdata(out_data)
	out.save(image_path)

	draw_png_at(
		ctx, image_path, base_image.x, base_image.y, base_image.width,
		base_image.height)

	out.close()
	descp_img.close()
	set_img.close()

SET_SVGS = {}

def set_rarity_svg(ctx, comp, data):
	from lxml import etree
	from gi.repository import Rsvg

	file_ext = ".svg"
	scale = comp.custom["region"]["width"] / 128;
	colors = {
		Rarity.COMMON: "#8C8C8C",
		Rarity.RARE: "#277FFF",
		Rarity.EPIC: "#9828BB",
		Rarity.LEGENDARY: "#FF8800"
	}
	card = data["card"]
	theme_dir = os.path.join(data["dir"], comp.custom["setIcons"])
	set_name = card.card_set.name.lower()

	# first call, populate dict
	if len(SET_SVGS) == 0:
		for s in CardSet:
			name = s.name.lower()
			icon = os.path.join(theme_dir, "{}{}".format(name, file_ext))
			if os.path.isfile(icon):
				SET_SVGS[name] = etree.parse(icon)
		print("{} set icons loaded".format(len(SET_SVGS)))

	# get the position
	set_region = Region(
		comp.custom["region"]["x"],
		comp.custom["region"]["y"],
		comp.custom["region"]["width"],
		comp.custom["region"]["height"])
	# check the svg exists
	if set_name not in SET_SVGS:
		print("Warning: set icon not found for '{}'".format(set_name))
		return
	# get the svg and switch the color
	if card.rarity in colors:
		SET_SVGS[set_name].getroot().attrib["fill"] = colors[card.rarity]
	else:
		print("{}, no color found for rarity {}".format(card.id, card.rarity))
		return

	ctx.save()
	ctx.new_path()
	ctx.translate(set_region.x, set_region.y)
	ctx.scale(scale, scale)
	handle = Rsvg.Handle.new()
	handle.write(etree.tostring(SET_SVGS[set_name]))
	handle.close()
	Rsvg.Handle.render_cairo(handle, ctx)
	ctx.restore();
