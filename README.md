![header](header.png)

A cairo based python card renderer for Hearthstone.

---

 ## Setup and Usage
See the [Vagrantfile](./Vagrantfile) for setup and requirements.

```
python generate.py <options>

--art-dir     location of the card artwork files
--out-dir     location to save the generate cards
--id          specify a card id to generate a single card
--locale      the locale the generated cards should be in
--style       the HearthForge style/theme to use
--premium     flag to include premium card images (if supported by theme)
--collectible only generate collectible cards
--card_set    generate all cards from a set (currently must be enum names)
```
