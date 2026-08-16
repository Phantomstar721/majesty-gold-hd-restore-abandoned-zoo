# Majesty Gold HD: Restore Abandoned Zoo

Restores the abandoned three-level Zoo using the artwork, dialog layout, and
GPL building lifecycle left in *Majesty Gold HD*.

The current local-test milestone restores the building and isolates the stock
Wizard's Curse Hooligan lifecycle:

- the Zoo appears in the stock service-building construction menu;
- it carries private `Restore_Zoo1`–`Restore_Zoo3` clones of the stock Zoo GPL
  prototypes and upgrades through stock art levels `ABn1`–`ABn3`;
- it packages literal copies of the three stock Zoo IMAG records with their
  position-preserving MX TILE and palette tables, so Original rules can create
  the construction placement ghost;
- it uses the literal stock `MX09` building controller and corrects its obvious
  Blacksmith placeholder prose;
- its surviving **Place Reward** control now opens a private `ZC01` clone of
  the stock Palace Rewards panel;
- that clone retains only the Attack placement path, labels it **Capture
  Flag**, and uses the stock 100-gold initial increment;
- only that private clone selects a Zoo-themed `ZOBG` backing, which retains
  the stock Capture controls and removes the baked-in appearance of the hidden
  Explore row without changing controller behavior;
- its Capture button selects private `ZCIC` set 1011 art, retaining the stock
  25x25 button frame while replacing the crossed-blade flag with the Zoo paw;
- its Capture control selects a private `ZCF0` placement-mode clone, whose
  completion callback creates private `Restore_Capture_Flag` reward flags;
- `ZCF0` preserves the complete stock Attack Flag placement validator, then
  accepts only Majesty's stock runtime display category `4` plus
  unit-description `Character` intersection—the generic stock shape observed
  for a normal monster—so Capture Flags cannot be placed on heroes, henchmen,
  buildings, or effects;
- that placement clone selects private tactical-cursor selector 32, backed by
  an appended `CUR1` set 1032 repaint of stock Attack cursor set 1005;
- the private flag retains the stock Attack Flag animation topology but selects
  private `ZCA2` Zoo art: a forest-green flag with an aged-gold paw emblem,
  four stock-shaped player-color interface variants, and private minimap art;
- it retains the stock Attack Flag panel, internal `Flag_Attack` title, hero
  evaluation, poll, target-death callback, payout, cancellation, task reset,
  and cleanup lifecycle;
- it uses the nearest evidenced stock configuration for missing economy and
  durability values;
- while its player owns a completed Zoo, placing a private Capture Flag on a
  living monster begins the shipped controlled-monster handoff into Hooligan
  behavior while the flag remains attached under its stock poll/death lifecycle;
- Palace Attack Flags now remain completely stock and cannot trigger Zoo
  capture behavior;
- the stock 3.3-second `Control_Monster` transition temporarily hides the
  target and transfers it to the flag player's allegiance, forcing Priestess
  skeletons and charmed monsters to drop existing attacks before arrest begins;
- shipped `Arrest_Hooligan` and `Hooligan_Death` remain unchanged; private
  Hooligan clones change the destination and enforce one arresting hero per
  Hooligan;
- each Hooligan retains shipped `Hide` travel but pauses whenever it moves more
  than the stock arrest distance ahead of its selected hero;
- the Hooligan returns to its selected Zoo, stops its active lifecycle, and is
  stored as a valid hidden agent in the Zoo's stock `Occupants` list;
- delivered monsters use the stock occupant-intent field so their visitor rows
  read “is waiting in the zoo” rather than the default “is Thinking”;
- the abandoned Zoo panel's truncated `Visitors` control is completed with the
  missing bytes from the stock Blacksmith control and displays delivered
  monsters from the generic occupant list;
- it loads the literal stock `IX92`/`IX94` monster-icon records with their
  complete positional interface TILE table so the generic visitor renderer can
  use Majesty's shipped monster-icon resolver in Original-rules quests;
- Deal with a Demon starts with one completed level-one Zoo as a temporary,
  deterministic test fixture;
- the mod applies only the successful stock Hooligan-check handoff to one hero,
  leaving that hero's native Basic/Starting scripts untouched so delivery can
  reset cleanly;
- if combat or fleeing changes that hero's target, the stock Zoo flag
  abandonment test releases the Hooligan and assigns one different hero;
- there is currently no capacity, capture roll, combat/death hook,
  resurrection, visitor income, Zoo-destruction-specific handling, or breakout
  behavior.

See [stock evidence](docs/stock-evidence.md), the [capture stock-clone
contract](docs/capture-stock-clone.md), the [visitor stock trace](docs/visitor-stock-trace.md),
and the complete [invented-content ledger](docs/invented-content.md) before
changing gameplay.

## Build

Requires Python 3.9+ and a local Majesty Gold HD installation.

```powershell
python scripts/build_mod.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The ready-to-install mod is written to `dist/RestoreAbandonedZoo`. Copy that
directory into the game's `Mods` directory, or pass `--output-root` to build
somewhere else.

## Local Steam test install

Build, validate, and install into the default Steam user's local Majesty mod
directory with one command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Install-LocalMod.ps1
```

The installed package is
`Documents\My Games\MajestyHD\Mods\RestoreAbandonedZoo`. Re-running the command
replaces only that exact package and verifies every deployed file by SHA-256.
The same command also installs one private `.mzoo` executable section. Two
guarded redirects let only `MX09` open `ZC01` and let only `ZC01` use Majesty's
literal AP41 controller constructor. A third stock-boundary redirect appends
private `ZCF0` beside the shipped flag-placement modes; ZC01 alone receives a
private vtable selecting it. Its private validator calls the full stock Fl00
validator before applying the stock monster-class intersection. The stock
Palace `AP41`/`Fl00`, the existing
`CGxx` custom-guild route, and unrelated QOL patches remain untouched. Restore
only the Zoo redirects, mode registration, and section with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Restore-ZooRewardDispatcher.ps1
```

Enable **Restore Abandoned Zoo** in Majesty's Mods screen before starting a new
game. Workshop metadata and publishing are intentionally not part of this local
development setup.

## Validate

```powershell
python scripts/validate_mod.py dist/RestoreAbandonedZoo
```

The validator checks the package structure, XML links, private standalone GPL,
stock dialog resources, and all documented first-milestone boundaries. It
does not replace an in-game construction and upgrade test.

## Regenerate the Zoo rewards art

The build consumes the checked-in, packed
`assets/generated/interface/zoo-rewards-panel.tile`, so Pillow is not required
for an ordinary mod build. To regenerate it from the source master, use a
Python environment with Pillow installed:

```powershell
python scripts/generate_zoo_rewards_art.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The generator derives the exact 202x245 geometry and functional chrome from
stock `INBg` set 1019, composites the Zoo-themed backing, and packs it back into
Majesty's embedded-palette V1 TILE format.

## Regenerate the Capture Flag art

The ordinary build consumes the checked-in TILEs under
`assets/generated/capture-flag`. To regenerate them from the two source
masters, use the workspace Python environment with Pillow installed:

```powershell
..\.tools\python\Scripts\python.exe scripts\generate_capture_flag_art.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The generator traces stock `ARA2flag attack` and retains its 12 Special, four
Minimap, and four player-color Interface frames. It repaints those exact world
and minimap canvases, packs all twenty frames in their stock TILE formats, and
produces review previews beside them. It also repaints stock `INTC` set 1011's
25x25 Attack button and `CUR1` set 1005's 39x40 tactical cursor as matching
green-and-gold paw flags. The build clones the ARA2 IMAG as private
`ZCA2Capture flag`, clones the button resource as private `ZCICItem Icons`, and
appends CUR1 set 1032. Existing ARA2 Attack, ARA4 Explore, INTC, and CUR1 sets
remain visually and behaviorally unchanged.
