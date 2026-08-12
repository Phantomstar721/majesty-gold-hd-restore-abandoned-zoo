# Invented and inferred content ledger

Nothing in this file is claimed as recovered Cyberlore design. This is the
complete ledger for the first milestone.

## Inferred from the Blacksmith shell

The stock files contain no Zoo XML descriptions. The following values are
copied literally from Blacksmith levels 1–3 because the abandoned Zoo GPL and
dialog both demonstrably use Blacksmith scaffolding:

| Property | Level 1 | Level 2 | Level 3 |
| --- | ---: | ---: | ---: |
| Cost / upgrade cost | 500 | 600 | 800 |
| Max HP | 250 | 300 | 400 |
| Sight range | 100 | 100 | 100 |
| Multiplier | 1.0 | 1.0 | 1.0 |
| Income type | 2 | 2 | 2 |
| Income amount | 40 | 40 | 40 |

The same stock build-menu category (`Menu 2`), player ownership, terrain
placement flags, HP bar, gold tooltip, upgrade linkage, and level 2–3
`NotBuildable` flags are also reused.

The missing `DATA/BDEP` entries use the Blacksmith's exact no-prerequisite row
shape for all three Zoo levels. The table integration is required stock
dispatcher plumbing; choosing no Palace or building prerequisite is inferred
from the Blacksmith scaffold rather than recovered Zoo design.

## Newly chosen or written

- The restored building uses stock dialog/controller ID `MX09`; no private
  dialog-controller behavior is assumed.
- `ZOO1`, `ZOO2`, and `ZOO3` are private unit-description IDs. This avoids the
  existing stock Sewer Entrance ID `ABN1`; recovered `ABn1`–`ABn3` remain art
  references only.
- `Restore_Zoo1`, `Restore_Zoo2`, and `Restore_Zoo3` are private GPL prototype
  names. Their fields are literal clones of shipped Zoo1–Zoo3, renamed so the
  mod works under Original rules without colliding under Expansion rules.
- Help IDs `hZ01`, `hZ02`, and `hZ03` and all text stored under them are new.
- The broken stock sentence “The Blacksmith forges…” is replaced with a neutral
  description of the currently restored building shell.
- “Destroy this Blacksmith” is corrected to “Destroy this Zoo.”
- `Fairground` is used as the default sound because no Zoo sound descriptor is
  present and it is the closest stock civic-entertainment building sound. This
  is a thematic guess.
- The mod name, GUID, package filenames, and explanatory metadata are new.

## Surviving placeholder content

- `Visited_Script Upgrade_Equipment` is retained in private levels 1 and 2
  because it is present in the shipped Zoo prototypes. This Blacksmith-derived
  placeholder remains part of the literal stock clone until basic construction
  is proven.

## Deferred, not invented yet

- no monster-capture dispatcher;
- no Zoo flag description or interface icon;
- no rules for which Zoo level unlocks capture;
- no initial reward, placement restrictions, valid-target filter, or player
  feedback for capture;
- no revenue, visitors, or exhibited-animal simulation beyond generic stock
  building behavior.
