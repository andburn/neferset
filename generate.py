#!/usr/bin/env python

import sys
import math
import re
import json
import os.path
from operator import itemgetter, attrgetter

import fire
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from hearthstone.cardxml import load
from hearthstone.enums import (
	CardType, CardSet, MultiClassGroup, Locale, get_localized_name
)

from neferset.curved import CubicBezier, CurvedText, curved_text
from neferset.drawing import (
	rectangle, rect_ellipse, draw_png_asset, text, text_block
)
import neferset.custom
from neferset.component import (
	ComponentType, ShapeType, Region, Shape, Image, Text, Clip, Curve,
	Component, ComponentData
)

OUT_DIR = "./out"
ART_DIR = "./art"
ASSET_DIR = "./assets/styles"
DB_XML = "./hsdata/CardDefs.xml"
THEME_JSON = "data.json"
PREM_SUFFIX = "_premium"


def as_shape(obj):
	if "type" in obj:
		if obj["type"] == "curve":
			return CubicBezier()
		else:
			return Shape(obj["type"], obj["x"], obj["y"], obj["width"], obj["height"])
	else:
		return obj


def draw_clip_region(ctx, obj):
	if obj.type == ShapeType.ellipse:
		rect_ellipse(ctx, obj.x, obj.y, obj.width, obj.height, False, 0.01)
	elif obj.type == ShapeType.rectangle:
		rectangle(ctx, obj.x, obj.y, obj.width, obj.height, False, 0.01)
	else:
		raise ValueError("Unable to use a {} as a clipping region.".format(obj.type.name))



def render_component(context, art_dir, theme_dir, loc_code, component, data):
	clipped = False
	# first check if there is a clipping region
	if component.clip:
		draw_clip_region(context, component.clip)
		context.clip()
		clipped = True
	# draw image
	if component.image and data.override:
		draw_png_asset(context, component.image, art_dir, data.override)
		if clipped:
			context.reset_clip()
			clipped = False
	elif component.image and data.key in component.image.assets:
		draw_png_asset(context, component.image, theme_dir, data.key)
		if clipped:
			context.reset_clip()
			clipped = False
	# draw text
	if component.text and component.font and data.text:
		if component.font.type == "textBlock":
			text_block(context, component.text, data.text, component.font, loc_code)
		else:
			text(context, component.text, data.text, component.font, loc_code)
	# draw curved text if any
	if component.curve and component.font and data.text:
		curved_text(context, component.curve, data.text, component.font)
	# custom handling, use named function of custom module
	if component.custom:
		if hasattr(neferset.custom, component.custom["name"]):
			func = getattr(neferset.custom, component.custom["name"])
			func(context, component, data.obj)


def plural_index(num, locale):
	if locale == Locale.ruRU:
		mod = num % 100
		if mod in range(11, 15):
			return 2
		else:
			mod = num % 10
			if mod == 1:
				return 0
			elif mod in range(2, 5):
				return 1
			else:
				return 2
	elif locale == Locale.plPL:
		if num == 1:
			return 0
		elif num == 0:
			return 2
		else:
			mod = num % 100
			if mod in range(11, 15):
				return 2
			else:
				mod = num % 10
				if mod in range(2, 5):
					return 1;
				else:
					return 2;
	elif num <= 1:
		return 0
	return 1


def format_plurals(text, locale):
	pattern = re.compile(r"(\d+)(.*?)(\|4\(([^,]+(,[^,]+?)*)\))")
	match = pattern.search(text)
	while match:
		num = int(match.group(1))
		words = match.group(4).split(",")
		idx = plural_index(num, locale)
		text = text[:match.start(3)] + words[idx] + text[match.end(3):]
		match = pattern.search(text, match.end(3))
	return text


def clean_description_text(text, locale):
	"""Remove the non-markup tags from the card description text.

	$, #	positive, negative multipliers (removed)
	_ 		non-breaking space (removed)
	[x]		disable automatic wrapping, can occur mid text (handled)
	[d]		indicates hyphenation is possible, deDE only (removed)
	[b]		unknown, jaJP and thTH only, maybe line break is allowed (removed)
	|4()	plurals
	@		dynamic/in-game text appears before the @, static text after
	"""
	if "@" in text:
		text = text.split("@")[1]
	text = format_plurals(text, locale)
	idx = text.find("[x]")
	if idx == 0:
		text = text.replace("[x]", "")
	elif idx > 0:
		text = re.sub(r"\n", " ", text[:idx + 3]) + text[idx + 3:]
		text = re.sub(r"\s*\[x\]", "\n", text)
	text = re.sub(r"[$#]|\[b\]|\[d\]", "", text)
	text = re.sub(r"[_ ]+", " ", text)
	return text


def setup_context(width, height):
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	ctx = cairo.Context(surface)
	ctx.set_source_rgba(0, 0, 0, 0) # transparent bg
	ctx.paint()
	return (ctx, surface)


def generate(
		art_dir=ART_DIR, out_dir=OUT_DIR, id=None, locale="enUS",
		style="default", premium=False, fonts=None, collectible=False,
		card_set=None):
	loc = locale_converter(locale)
	loc_code = locale_as_code(loc)
	# load cards
	cards = load_cards(locale, id, card_set_converter(card_set), collectible)
	print("Generating {} cards".format(len(cards)))
	# load theme data, from hearthforge submodule
	theme_dir = os.path.join(ASSET_DIR, style)
	if not os.path.isdir(theme_dir):
		raise FileNotFoundError("Asset dir not found ({})".format(theme_dir))
	with open(os.path.join(theme_dir, THEME_JSON)) as f:
		theme_data = json.load(f)
	# render cards, the standard card first then the premium if required
	import time
	st = time.process_time()
	for c in cards:
		render(c, loc, loc_code, False, theme_data, theme_dir, art_dir, out_dir)
		if premium:
			render(c, loc, loc_code, True, theme_data, theme_dir, art_dir, out_dir)
	ed = time.process_time()
	print(ed - st)


def locale_converter(locale_str):
	"""Covnert locale string to hearthstone.enums.Locale."""
	loc = Locale.UNKNOWN
	if locale_str and len(locale_str) == 4:
		try:
			loc = Locale[locale_str]
		except KeyError:
			pass
	return loc


def locale_as_code(locale):
	"""Covnert hearthstone.enums.Locale to pango lang code."""
	return "{}-{}".format(locale.name[:2], locale.name[2:])


def card_set_converter(card_set):
	"""Convert a card set string to a hearthstone.enums.CardSet."""
	cset = CardSet.INVALID
	if card_set:
		try:
			cset = CardSet[card_set]
		except KeyError:
			pass
	return cset


def load_cards(locale_str, id, card_set, collectible):
	"""Load card data from XML.

	locale_str -- the hearthstone.enums.Locale data to load
	id -- a card id, takes precedence over set and collectible
	card_set -- restrict generation to a hearthstone.enums.CardSet
	collectible -- when True only generate collectible cards
	"""
	db, xml = load(DB_XML, locale_str)
	cards = []
	if id == None:
		for card in db.values():
			include = True
			if collectible:
				if card.collectible:
					include = True
				else:
					include = False
			if card_set == card.card_set:
				include = include and True
			else:
				include = include and False
			if include:
				cards.append(card)
	elif id in db:
		cards.append(db[id])
	else:
		raise ValueError("Unknown card id {}".format(id))

	return cards


def render(card, locale, loc_code, premium, theme_data, theme_dir, art_dir, out_dir):
	card_type = card.type.name.lower()
	if premium:
		card_type += PREM_SUFFIX
	if card_type in theme_data:
		data = theme_data[card_type]
	else:
		print("{} : '{}' is unsupported in '{}' theme".format(
			card.id, card_type, theme_data["name"]))
		return
	# sort the components by the layer attribute
	components = []
	for ct in ComponentType:
		obj = data.get(ct.name)
		if obj:
			cp = Component(data[ct.name], ct)
			components.append(cp)
	components.sort(key=attrgetter("layer"))

	ctx, surface = setup_context(data["width"], data["height"])
	rendered_comps = 0

	for c in components:
		cdata = None
		# match each component to a known type
		if c.type == ComponentType.name:
			cdata = ComponentData(text=card.name)
		elif c.type == ComponentType.elite and card.elite:
			cdata = ComponentData()
		elif (c.type == ComponentType.rarity
				and card.rarity.craftable
				and card.card_set != CardSet.CORE):
			cdata = ComponentData(card.rarity.name.lower())
		elif (c.type == ComponentType.multiClass
				and card.multi_class_group != MultiClassGroup.INVALID):
			cdata = ComponentData(card.multi_class_group.name.lower())
		elif c.type == ComponentType.classDecoration:
			cdata = ComponentData(card.card_class.name.lower())
		elif c.type == ComponentType.cost:
			cdata = ComponentData(text=str(card.cost))
		elif c.type == ComponentType.health:
			health = str(card.health)
			if card.type == CardType.WEAPON:
				health = str(card.durability)
			cdata = ComponentData(text=health)
		elif c.type == ComponentType.attack:
			cdata = ComponentData(text=str(card.atk))
		elif c.type == ComponentType.race and card.race.visible:
			cdata = ComponentData(text=get_localized_name(card.race, locale.name))
		elif c.type == ComponentType.portrait:
			cdata = ComponentData(None, None, card.id + ".png")
		elif c.type == ComponentType.base:
			cdata = ComponentData()
		elif c.type == ComponentType.description:
			cdata = ComponentData(text=clean_description_text(card.description, locale))
		elif c.type == ComponentType.cardSet:
			cdata = ComponentData(
				obj={
					"card": card,
					"dir": theme_dir,
					"premium": premium,
					"cardtype": card.type.name.lower()
				}
			)
		# render any component matched
		if cdata:
			render_component(ctx, art_dir, theme_dir, loc_code, c, cdata)
			rendered_comps += 1
	# save the image to file if any components have been rendered
	if rendered_comps > 0:
		surface.flush()
		filename = "{}{}.png".format(card.id, PREM_SUFFIX if premium else "")
		surface.write_to_png(os.path.join(out_dir, filename))


if __name__ == "__main__":
	fire.Fire(generate)
