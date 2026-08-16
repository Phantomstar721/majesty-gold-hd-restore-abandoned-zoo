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
- it uses the nearest evidenced stock configuration for missing economy and
  durability values;
- while the player owns a completed Zoo, placing an ordinary Attack Flag on a
  living monster begins the shipped controlled-monster handoff into Hooligan
  behavior;
- without a completed Zoo, Attack Flags and monsters remain stock;
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
literal AP41 controller constructor. The stock Palace `AP41`, the existing
`CGxx` custom-guild route, and unrelated QOL patches remain untouched. Restore
only the Zoo redirects and section with:

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
