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
  `MX09`. Its orphaned Place Reward command is replaced with the literal stock
  AP39 REWARDS command. Private dialog ID `ZC01`, the `.mzoo` executable-section
  name, its two guarded redirects, and substituting ZC01 for AP41 only on an
  MX09 reward click are new integration glue. ZC01 uses the literal AP41
  constructor; the 100-gold initial increment, placement state, cancellation,
  flag construction, callbacks, and cleanup are stock.
- The private ZC01 resource moves AP41's five Explore controls to the shipped
  hidden-control position `(1500,1500)` demonstrated by AP50. The earlier
  experimental layouts are not retained; the live parser trace used to correct
  the Explore-placement record boundary was diagnostic only. “Capture Flag,”
  its related Capture tooltips, “Capture,” and the Zoo return tooltip are
  newly written presentation text. All control records and internal Attack Flag
  IDs remain stock, so this step changes no placement behavior or flag type.
- The Zoo-themed rewards backing is newly created presentation art, not a
  recovered Cyberlore asset. Its warm stucco, terracotta roof, dark timber,
  stone courtyard, iron enclosure, greenery, and restrained gold motifs are
  inferred from the surviving Zoo building/profile art. The source master was
  produced with built-in image generation and then reduced beneath stock AP41
  chrome. The generator deliberately preserves the title band, functional
  Capture row, outer frame, and navigation strip from stock set 1019 while
  replacing the baked-in unused Explore half. It recolors the stock title fill
  as dark Zoo timber and supplies a near-black green amount-field backing,
  because the stock amount field uses transparent palette index 0 and normally
  borrows its darkness from the Palace panel beneath it.
- `ZOBGbuilding dialog`, the `ZOBG` resource token, the generated 202x245
  backing TILE, and `restore_zoo_rewards_interfacedata.cam` are new private art
  integration. Their scope is only `SMNU/ZC01`; the stock `INBg` resource and
  all other dialogs are untouched. This is presentation-only and does not
  alter reward values, flag placement, callbacks, or cleanup.
- The Capture Flag's `ZCA2` art family is newly created presentation art; no
  finished Zoo flag artwork survives in stock resources. Its forest-green
  cloth, aged-gold paw emblem, dark timber, cream edging, and reuse of the
  owner's blue/green/orange/magenta trim colors are invented from the surviving
  Zoo building and panel palette. The 100x100 interface master and transparent
  world-sprite concept were produced with built-in image generation. The
  generated frame pipeline uses those concepts for the emblem and palette, but
  copies stock `ARA2flag attack` geometry and ordering exactly: 12 Special
  animation frames, four 7x7 Minimap frames, and four 100x100 Interface
  directions. The private `ZCA2Capture flag` IMAG redirects all twenty frames
  to appended TILE slots. Its indexed frames carry literal stock base palettes
  0–793 in the same proven form as other private maindata packages; the Capture
  CAM loads before the recovered MX Zoo CAM so the latter's palette range stays
  authoritative for the building. Stock ARA2 Attack and ARA4 Explore resources
  are not replaced.
- The Zoo Capture button's `ZCICItem Icons` resource and 25x25 paw-flag TILE
  are new private presentation art. Stock AP41 paints its Attack icon through
  `INTCItem Icons` set 1011/TILE 92; ZC01 changes only that control's four-byte
  resource token to `ZCIC`. The private IMAG retains the complete stock INTC
  set table and redirects only set 1011 to one appended embedded-palette V1
  TILE. The stock teal button frame is preserved while its tiny red
  crossed-blade flag is repainted green with a gold paw.
- The Capture placement cursor's selector 32, `CUR1` set 1032, and 39x40
  green-and-gold paw-flag TILE are new private presentation content. Stock
  `Fl00` passes selector 5, which maps to CUR1 set 1005/TILE 27; stock `Fl01`
  passes selector 6, mapping to set 1006/TILE 26. Because the tactical cursor
  renderer fixes the resource token to `CUR1`, the mod emits a complete literal
  CUR1 clone with only set 1032 appended and changes only ZCF0's cloned cursor
  argument from 5 to 32. Because a CAM-local IMAG cannot safely refer through
  empty positional TILE slots, every stock TILE referenced by CUR1 is populated
  at its original index with literal stock bytes; all 28 original CUR1 sets
  retain their original TILE numbers. Only set 1032 points to appended new art.
  The same CAM carries the literal seven stock `PALT` entries required by
  non-embedded CUR1 TILEs. Palace selectors and their rendered art remain
  unchanged. This is the narrow stock-shaped extension necessary for a Zoo-only
  cursor rather than a recovered Zoo design.
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

- `ZCF0`, `Restore_Capture_Flag`, its XML description, GPL prototype, placement
  registration, relocated completion callback, private ZC01 vtable, and
  `Restore_Capture_Flag_Birth` are new private integration. The exact private
  identifiers are invented; no finished Capture Flag resource survives in
  stock data. `ZCA2` changes only its private image selection; the placement
  and reward lifecycle remain the already-tested stock clone.
- The private placement mode is a literal clone of stock `Fl00`: the same
  registration parameters, mouse lifecycle, reward amount, cancellation, gold
  accounting, and completion code are used. Its private validation wrapper
  first calls the complete shipped Fl00 validator, then adds the invented
  Capture-only policy of requiring the intersection of two shipped classes:
  runtime display category `4` and XML unit subtype `Character`. A focused
  live trace established that pair for an ordinary monster. The intersection
  is generic and rejects heroes, henchmen, buildings, and non-character
  resources without per-monster definitions. The wrapper also maps Fl00's
  placement-ready state with no selected agent to the stock invalid result
  before applying either classification.
- Because stock Fl00 independently reacquires its target during completion,
  the relocated private completion callback redirects only that stock call to
  a pointer/zero wrapper. It calls the original acquisition first and returns
  its selected pointer only for the same invented category-`4` + `Character`
  policy; reward deduction, creation, cancellation, and cleanup remain stock
  order.
  The completion callback changes only the created prototype-name pointer from
  `Flag_Attack` to `Restore_Capture_Flag`. The private flag then retains stock
  `RewardFlag` type, `Flag_Attack` subtype/title, AP46 panel, and hero reward
  evaluation. Its poll and death callbacks are private Zoo clones because an
  ordinary Attack Flag callback would pay a lethal bounty instead of attempting
  capture.
- The active trigger restores GPLMx's global `monster_gravestone` Zoo gate and
  literal stock failure tail. An earlier attempt aborted inside missing
  expansion-only fields and left every monster half-dead; this version does not
  touch those fields. After the recovered Zoo check succeeds, the existing
  private `Control_Monster` BackScript seam activates the proven
  Hooligan-to-Zoo delivery. No watcher or deferred controller is active.
- Original declares neither `Monster.zoo_agent` nor
  `RewardFlag.charm_percentage`. A focused saved-state trace proved that the
  first missing-field write aborted private flag Birth. A second focused trace
  proved RewardFlag enumeration loses the overlay by the later engine overlay
  callback. The earlier stock `monster_gravestone` boundary now performs a
  one-shot stock RewardFlag enumeration and matches the engine-owned TargetID;
  this is the sole invented replacement for `Monster.zoo_agent`. The new private
  `Capture_Flag` subtype distinguishes the clone while its `Flag_Attack` title
  remains stock for hero evaluation. The recovered chance formula is evaluated
  directly at the lethal event. No timer, watcher, resurrection, custom
  registry, or borrowed monster field is introduced.
- The overlay callback is the literal abandoned Zoo callback and only calls
  `DeleteGamePiece`; it does not perform or retry capture.
- The enable gate copies the stock completed-building query shape used by the
  Mausoleum and other MX systems: player-owned `Building`, title `Zoo`, and
  `FirstStageBuilt == 1`, called from the flag with the exact argument order
  that passed the earlier live test. Any completed Zoo level qualifies.
  Without one, the private Capture Flag retains the cloned Attack Flag
  lifecycle and its target remains unchanged.
- The target receives the behavior-relevant fields from stock `[Hooligan]` and
  shipped `Hooligan_Death`. It retains its original monster art because no
  unit-description transformation is made.
- `Restore_Hooligan_Basic` is a private literal clone of the shipped function
  with only its next-function reference changed. `Restore_Hooligan_Goto_Zoo`
  retains the stock `Hide`, last-Hooligan detection, message, and quest flag,
  but changes the destination and privatizes escort pacing and reset ownership
  as detailed below.
- The Capture Flag owns only the proven player-Zoo gate. The converted Hooligan
  later uses the private stock destination clone to select the first completed
  Zoo.
- Minion protection now calls the selected ruleset's actual
  `Control_Monster`, including its ownership transfer, `fake_wander`, 3300 ms
  delay, `Become_Controlled`, leader link, follower count, charm effector, and
  hostile-list cleanup. Normalizing Original's temporary `Dead` type to GPLMx's
  corrected `Hidden` type is compatibility glue. The private BackScript then
  deletes the infinite charm effector, decrements the temporary follower count
  using stock controlled-monster death cleanup, substitutes `Hooligan` for
  `Controlled`, and appends the existing arrest handoff.
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
- Visitor registration calls stock `Enter_Building` only after the existing
  `Hide` arrival and paired-owner reset, then kills the stored agent's active
  thread. Applying the ordinary visitor callback to a living Hooligan is new
  integration behavior.
- Visitor capacity is requested invented design: 4 at Zoo level 1, 6 at level
  2, and 8 at level 3. Admission copies stock `Check_Mausoleum`'s completed
  player-building query, `Occupants` size comparison, and first-legal choice.
  Unlike immediate Mausoleum interment, Zoo escort adds travel time, so a
  captured Hooligan records its selected Zoo in the stock Monster `Target`
  field. Pending capacity counts only a real stock arrest pairing: a live
  `leader` hero still targeting that Hooligan with `Arrest_Hooligan` active or
  resumable. Unassigned flagged captives remain queued, and assignment refuses
  another pairing once stored visitors plus real pairings reach the limit.
  This avoids overbooking without adding a new field, counter, timer, or
  watcher.
- The private Capture placement gate uses the otherwise Zoo-specific stock
  `ATTRIB_Zoo_Legal_Target` attribute on the selected Zoo as its refreshed
  has-capacity bit. Repurposing that attribute on a building and retaining the
  originating Zoo pointer in a four-byte, non-executable private data section
  are new integration seams. They change no Palace Attack Flag code or global
  Monster flaggability.
- The visitor-row wording “waiting in the zoo” is invented. Its mechanism is
  stock: after `Enter_Building`, delivery calls `SpecifyIntent`, matching stock
  `Lived_In` occupant ordering. Private `#intent_waiting_in_zoo` uses expansion
  AITX slot 199, one of the shipped `empty` placeholders from 177 through 199;
  no live stock intent/message string and no generic row-painter behavior is
  replaced.
- For repeatable testing only, the mod overrides `DEAL_DEMON` with a literal
  stock copy plus one stock completed-building `SpawnUnit` call for
  `Restore_Zoo1` beside the first Palace. The quest's music, treasure, enemy
  guild, lair, and victory setup remain in stock order. Starting this quest
  with a Zoo is invented test scaffolding, not recovered Zoo design.
- The same focused fixture sets player one's treasury to exactly 90,000 gold
  with the stock `GetPlayerData` plus delta-shaped `AdjustPlayerData` sequence.
  This is testing scaffolding for raising Capture Flag rewards, not recovered
  Zoo balance.
- There is no bounty payment or resurrection. A successful capture suppresses
  the saved death callback exactly like GPLMx `monster_gravestone`; allowing the
  generic monster gate to target quest-critical monsters can therefore suppress
  quest victory/death side effects and is an explicit current risk. Visitor
  income and Zoo destruction cleanup remain absent.

## Surviving placeholder content

- `Visited_Script Upgrade_Equipment` is retained in private levels 1 and 2
  because it is present in the shipped Zoo prototypes. This Blacksmith-derived
  placeholder remains part of the literal stock clone until basic construction
  is proven.

## Still deferred

- displayed capture percentage;
- visitor income, monster-level gates, Zoo destruction cleanup, and random
  breakouts;
- a policy for quest-critical monsters whose native death callback must fire to
  advance or complete a scenario.
