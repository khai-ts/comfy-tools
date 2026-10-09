# Mochi Room

A tiny Pou-style pet room made with Godot 4.5: one cat, four foods, two meters. It's the first room
of a cat cafe that should grow into a zoo.

## Run

```bash
godot --path games/mochi-room            # play
godot --path games/mochi-room -- --demo  # scripted showcase (feeding, petting, dragging, "I'm full!")
```

Or open `project.godot` in the Godot 4.5 editor and press F5. It uses the Compatibility renderer, so it
also runs in a browser or on a phone.

## How to play

- **Tap a food** to toss it into Mochi's mouth, or **drag it** onto Mochi. Mochi watches the food and opens
  wide as it gets close, then chews, hops and throws hearts.
- **Tap Mochi** to pet it. Pet it 5 times quickly for a purring "Love!" combo.
- Hunger and happiness drain over time (fast, for testing: see `HUNGER_DECAY` in `scripts/main.gd`).
  When hungry, Mochi frowns and a thought bubble appears. When full, Mochi refuses food.

## Files

| Path | What |
|---|---|
| `scripts/main.gd` | room, UI, feeding and petting logic, sounds, particles, demo |
| `scripts/pet.gd` | the cat: breathing, squash and stretch, chewing, hops, refusing |
| `scripts/face.gd` | the face drawn in code (blinks, looks at food, chews, happy and squint eyes) |
| `scripts/food_button.gd`, `stat_bar.gd`, `fx_bit.gd` | squishy buttons, meters, hearts/stars/crumbs |
| `art/` | Z-Image Turbo renders from `image.py`, cut out with `cutout.py` |
| `sfx/` | Stable Audio Open effects and an ACE-Step music loop from `audio.py`, trimmed with `sound.py` |
| `fonts/` | Fredoka (SIL Open Font License, see `OFL.txt`) |
