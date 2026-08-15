# Invented and inferred content ledger

Nothing in this file is claimed as recovered Cyberlore design. This is the
complete ledger for the current milestone.

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

- The restored building uses the literal stock dialog/controller payload
  `MX09`; no private dialog command is added.
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

## Isolated Hooligan diagnostic choices

- A normal Attack Flag is used only as a convenient player-facing trigger.
  When its player owns a completed Zoo, placing it on a living `Monster`
  immediately removes the flag and begins a stock control transition into the
  Wizard's Curse Hooligan lifecycle. This is diagnostic glue, not recovered
  Zoo design.
- The enable gate copies the stock completed-building query shape used by the
  Mausoleum and other MX systems: player-owned `Building`, title `Zoo`, and
  `FirstStageBuilt == 1`, called from the flag with the exact argument order
  that passed the earlier live test. Any completed Zoo level qualifies.
  Without one, the original Attack Flag remains untouched.
- The target receives the behavior-relevant fields from stock `[Hooligan]` and
  shipped `Hooligan_Death`. It retains its original monster art because no
  unit-description transformation is made.
- `Restore_Hooligan_Basic` is a private literal clone of the shipped function
  with only its next-function reference changed. `Restore_Hooligan_Goto_Zoo`
  retains the stock `Hide`, last-Hooligan detection, message, and quest flag,
  but changes the destination and privatizes escort pacing and reset ownership
  as detailed below.
- The Attack Flag owns only the proven player-Zoo gate. The converted Hooligan
  later uses the private stock destination clone to select the first completed
  Zoo.
- Minion protection copies stock `Control_Monster`, whose source explicitly
  sets `Type = Hidden` so other units stop attacking, transfers the target to
  the controller's player, waits `Charm_Delay_Time`, and then activates the
  controlled type. The private completion substitutes `Hooligan` for
  `Controlled` and appends the existing single-hero arrest handoff. That
  substitution is new integration behavior; the Hidden state, ownership
  transfer, 3300 ms counter timing, and hostile-list cleanup are stock.
- The stock intent remains `#intent_arresting_hooligan` (numeric slot 117), but
  this mod replaces only its `STRT/AITX` display string, “Arresting a
  hooligan,” with the invented Zoo-facing wording “Capturing a monster.” No
  intent number or GPL behavior changes.
- Wizard's Curse reaches `Arrest_Hooligan` through a quest-wide `Be_Dumb`
  wrapper. Installing that wrapper permanently on a normal scenario hero was
  an incorrect integration choice and stranded heroes after delivery. The mod
  now applies only the successful stock branch's four writes: intent, Target,
  Counter 0, and ActiveScript `Arrest_Hooligan`. The hero's native Starting,
  Basic, Back, and Quest scripts are never replaced.
- Single-hero ownership copies the abandoned Zoo and `Control_Monster` seam:
  filter living native heroes, choose valid list member 1, and store that hero
  in the Monster prototype's declared `leader` field. Only that selected hero
  receives the direct stock arrest handoff. Heroes already running or returning
  to `Arrest_Hooligan` are excluded. Applying this ownership to the Hooligan
  return path is integration glue, but the ownership fields and selection shape
  are stock.
- Interruption recovery copies the abandoned Zoo's `zoo_flag_poll` ownership
  test: a hero whose Target is no longer the monster has abandoned it. The
  Hooligan stops, clears its stock `Special_Boolean`, returns to its existing
  Basic lifecycle, and selects one different eligible hero. Applying that flag
  cancellation rule to a Hooligan and choosing a replacement are new
  integration behavior; no separate polling thread or controller is added.
- Stock Hooligans travel independently through `Hide`; stock contains no
  escort-speed synchronization. `ATTRIB_Speed` is an AI comparison rating, not
  a replacement for the unit's movement attachment, so the ineffective
  hero-speed copy has been removed. The return script now copies the stock
  formation pattern of checking distance to the declared `leader`: it stops
  the Hooligan beyond the stock 50-unit arrest distance and resumes stock
  `Hide` when the hero catches up. Applying that formation gate to a Hooligan
  is new integration behavior, but it runs in the existing active lifecycle
  without a new thread, watcher, timer, or guessed species-specific modifier.
- Stock arrival resets every hero still running `Arrest_Hooligan`, but only
  when the globally last quest Hooligan reaches the Palace. One-owner arrests
  require per-delivery cleanup, so the Zoo clone now applies the same stock
  `Reset_Tasks` operation directly to that Hooligan's `leader` before storing
  the target. This ownership substitution is new integration behavior.
- Visitor registration copies the permanent-storage tail of
  `Check_Mausoleum`: after the existing `Hide` arrival and paired-owner reset,
  kill the stored agent's active thread and append it to the Zoo's generic
  `Occupants` list. Applying those statements to a living Hooligan is new
  integration behavior. There is intentionally no capacity; the prior invented
  4/8/12 limits remain removed.
- For repeatable testing only, the mod overrides `DEAL_DEMON` with a literal
  stock copy plus one stock completed-building `SpawnUnit` call for
  `Restore_Zoo1` beside the first Palace. The quest's music, treasure, enemy
  guild, lair, and victory setup remain in stock order. Starting this quest
  with a Zoo is invented test scaffolding, not recovered Zoo design.
- Beyond serving as the stock `Hide` destination and generic occupant container there
  is deliberately no capture probability, bounty payment, lethal event,
  resurrection, carrier pairing, visitor income, or Zoo destruction cleanup.

## Surviving placeholder content

- `Visited_Script Upgrade_Equipment` is retained in private levels 1 and 2
  because it is present in the shipped Zoo prototypes. This Blacksmith-derived
  placeholder remains part of the literal stock clone until basic construction
  is proven.

## Still deferred

- the complete abandoned Zoo capture design, including its missing dispatcher;
- a lethal-event handoff that does not corrupt the monster's engine state;
- carrier-death handling, income, monster-level gates, displayed capture
  percentage, Zoo destruction cleanup, and random breakouts.
