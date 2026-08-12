# Majesty Gold HD: Restore Abandoned Zoo

Restores the abandoned three-level Zoo using the artwork, dialog layout, and
GPL building lifecycle left in *Majesty Gold HD*.

This first milestone intentionally restores only the building shell:

- the Zoo appears in the stock service-building construction menu;
- it carries private `Restore_Zoo1`–`Restore_Zoo3` clones of the stock Zoo GPL
  prototypes and upgrades through stock art levels `ABn1`–`ABn3`;
- it packages literal copies of the three stock Zoo IMAG records with their
  position-preserving MX TILE and palette tables, so Original rules can create
  the construction placement ghost;
- it uses the stock `MX09` building controller and corrects its obvious
  Blacksmith placeholder copy;
- it uses the nearest evidenced stock configuration for missing economy and
  durability values;
- it does **not** yet expose the unfinished monster-capture dispatcher or Zoo
  flag.

See [stock evidence](docs/stock-evidence.md) and the complete
[invented-content ledger](docs/invented-content.md) before changing gameplay.

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
