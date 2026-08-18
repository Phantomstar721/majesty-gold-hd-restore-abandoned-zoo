# Stock evidence

## Confirmed surviving assets

The Northern Expansion main-data archive contains three complete building art
families with no corresponding shipped XML description:

| Level | Stock image ID | Restored unit |
| --- | --- | --- |
| 1 | `ABn1` | `Zoo1` |
| 2 | `ABn2` | `Zoo2` |
| 3 | `ABn3` | `Zoo3` |

All three contain normal building animation/state data. Their appearance is a
fortified animal compound that becomes progressively larger and more ornate.

The recovered images live only in `DataMX/mx_maindata.cam`. A standalone
`base="Any"` package must carry them into Original rules just as the Haunt
carries its own `maindata.cam`. Majesty addresses CAM TILE records by section
position, so the restoration retains the complete stock MX TILE and SPLT tables
and exposes only the three Zoo IMAG records. A menu row can exist without this
art, but the stock placement lifecycle cannot create its construction ghost.

`ABn1`–`ABn3` are art identifiers, not recovered unit-description IDs. Stock
already owns the case-adjacent description ID `ABN1` for Sewer Entrance, whose
art is independently selected as `BBN1`. Following that stock separation and
the Haunt's global-ID contract, this mod uses private description IDs
`ZOO1`–`ZOO3`, recovered art IDs `ABn1`–`ABn3`, and shipped GPL prototype names
`Zoo1`–`Zoo3`.

`DataMX/mx_textdata.cam` also contains the `SMNU/MX09` building menu and its
matching `STRT/MX09` strings. The panel calls the building `ZOO`, exposes the
normal visitors, repair, tax, track, help, reward, and status controls, and has
obvious Blacksmith placeholder prose in two strings.

## Stock reward-placement dispatch

The abandoned `MX09` Place Reward control is visually complete but sends
command `0x2293`. Its native controller dispatch slot points to the generic
building handler at `0x004BD280`, which immediately delegates to the base panel
handler. That handler recognizes the common `0x1F42`-series building controls,
but not `0x2293`; this is why the surviving button has no action.

The stock Palace `AP39` REWARDS control sends command `0x1389`. The Palace
controller handler at `0x004A5440` intercepts exactly that command and opens
the stock `AP41` Palace Rewards panel. Unrecognized commands tail-call the same
base handler used by `MX09`. The restoration copies AP39's literal four-byte
command into the existing MX09 control. A private dispatcher at MX09's
controller-dispatch vtable entry intercepts only `0x1389`, substitutes private
dialog ID `ZC01`, and otherwise jumps to the literal Palace handler. Visitors,
upgrade, destroy, help, tracking, and navigation consequently retain their
existing fallback path.

Majesty's dialog factory normally returns no controller for an unknown ID.
The private factory hook runs immediately after the stock function prologue
and compares only `ZC01`; matching calls enter the unchanged allocation and
constructor block used by `AP41` at `0x0050AF8F`, while every other ID resumes
the stock binary-search dispatcher at `0x0050AC26`. This hook is separate from
the established unknown-`CGxx` fallback, so the custom-guild route remains
byte-identical and install order does not couple the two patches.

`SMNU/ZC01` is a complete AP41 clone. Shipped panels such as `AP50` provide the
stock static hiding mechanism: they preserve complete control records but place
intentionally hidden controls at `(1500,1500)`, outside the dialog. ZC01 copies
that stock form for Explore reward +/- (`0x1388`/`0x1389`), Explore placement
(`0x138B`), Explore amount (`0x138C`), and its icon (`0x1B5A`). The controller
can still resolve and update every expected control, but those five records
cannot paint or receive clicks onscreen. The Attack placement, dynamic amount,
+/- controls, gold display, Attack icon, and back control are otherwise
byte-identical to AP41.

The first offscreen build used `0x0234` as the Explore-placement record start.
A live trace at the stock `CYDialogStream` rejection path recorded invalid
opcode `0x5DC` at ZC01 stream offset `0x023C`: that boundary included the prior
record's terminating `-1`, so adding eight bytes overwrote the placement
record's stock opcode `2` rather than its x coordinate. The corrected stock
record begins at `0x0238`; its coordinates are the dwords at `0x0240` and
`0x0244`. The trace hook was removed immediately after capture.

The lower disabled button, amount box, and +/- shapes that remained visible
after those controls moved offscreen are not additional controls. They are
painted directly into `IMAG/INBgbuilding dialog` set 1019's single 202x245
background TILE in base `Data/interfacedata.cam`. Stock contains no one-row
variant of that reward backing, so suppressing those shapes requires a private
art resource rather than another dialog-stream change.

The custom presentation follows the already proven Alchemist Brewing-panel
resource pattern. The complete stock `INBgbuilding dialog` IMAG is cloned as
private `ZOBGbuilding dialog`; every TILE reached by the private IMAG is cloned
to appended private positions, and only set 1019's backing is replaced. The
private `SMNU/ZC01` changes its one background token from `INBg` to `ZOBG`.
Stock AP41, every other `INBg` consumer, and all functional AP41 control records
remain unchanged.

The literal AP41 controller owns the rest of the lifecycle. On entry it
validates each stored reward amount against the player's available gold. An
unset value is initialized from
the stock `#RewardDelta`, which is 100 gold. Its ATTACK control (`0x138A`)
passes the selected amount and stock Attack descriptor `Fl00` to the engine's
existing reward-placement mode. The engine retains target validation, cursor
placement, gold handling, right-click/Escape cancellation, and panel return.
Successful placement creates the ordinary `Flag_Attack`/`RewardFlag`; shipped
birth, poll, target-death callback, manual flag-death cleanup, hero-task reset,
and UI refresh remain unchanged. This milestone adds no Zoo flag prototype,
placement state, timer, callback, cancellation branch, or reward accounting.

AP41 does not store reward amounts on the dialog object. Stock routine
`0x004A9100` reads Attack from process-global `0x007C17A4` and Explore from
`0x007C17A8`, normalizes negative values to `#RewardDelta`, rounds/caps them
against available gold, enables the four +/- controls, and paints amount
controls 8 and `0x138C`. Stock handler `0x004A92F0` mutates those same slots
for controls 10/11 and `0x1388`/`0x1389`, then passes the selected value to
`SetFlagMode`. Reusing AP41 unchanged therefore made ZC01 and Palace Attack
share `0x007C17A4` even though their modes and flag prototypes were private.

The private data section now exposes a second DWORD initialized to -1, matching
stock AP41's unset-value contract. Only ZC01's cloned activation vtable entry
and private 10/11 handler initially scoped that DWORD through stock Attack's
slot while the complete shipped activation/refresh/adjustment call ran. Live
testing showed the numeric value remained private but its painted control later
returned to Palace's amount until the next Capture click. The second stock AP41
vtable refresh at `0x004A94A0` independently calls `0x004A9100` for APPA
updates after activation. ZC01 now scopes that complete callback through the
same swap as well, copying its four arguments and preserving its `RET 0x10`
contract. Direct Capture and ZCF0 re-arm paths push the private DWORD. No stock
AP41 code or Palace vtable entry changes; Capture still inherits stock's
100-gold initialization, rounding, affordability, button state, text refresh,
and `SetFlagMode` order.

## Private Capture Flag placement clone

`Fl00` is the stock Attack Flag placement-mode token, not the flag's unit ID.
The AP41 handler sends that token and the current reward to `0x00454E70`. The
engine registers `Fl00` during its normal placement-mode initialization with
the stock validation callback at `0x0045D360` and completion callback at
`0x0045D400`. The completion callback eventually passes the literal prototype
name `Flag_Attack` to the stock creation path at `0x0045CC90`.

The private clone preserves both halves of that lifecycle. At the same stock
registration boundary, it appends mode `ZCF0` with the same parameters and a
relocated byte-for-byte completion callback. The sole completion-callback
substitution is its prototype-name pointer:
`Flag_Attack` becomes `Restore_Capture_Flag`. Target validation, mouse state,
gold checks, successful placement, cancellation, and panel return remain in
stock order.

The private validation callback first calls the complete stock Fl00 validator
at `0x0045D360` and returns its insufficient-gold or invalid result unchanged.
Only after stock returns a valid target does the callback read the selected
agent from the placement-mode field at `+0x60`. This is the exact field written
by Fl00's stock target check at `0x0045D2D0-0x0045D314`; the `+0x08` member of
the object returned by `0x0045E900` is the picker object used to perform that
check, not the selected agent. The callback then combines two shipped
classifications:

- the stock runtime display-category classifier at `0x00508510` reads shipped
  `subtype`, `type`, and `original_type` metadata and returns categories used
  by stock interface dispatch. A focused live trace of an ordinary monster
  returned category `4`. This is not the raw GPL `GetUnitType` result; the
  earlier category-`0` inference was disproved by the runtime trace.
- the stock GPL `GetUnitPlayerNumber` wrapper at `0x00432140` resolves its unit
  and invokes vtable slot `+0x1C`. The private validator calls that identical
  slot after category 4 and accepts only shipped `Monster_Player` value 7.
  This current-ownership test distinguishes a hostile monster from the same
  underlying unit class after Priestess or Cultist control.

The same live target returned structural subtype `3`. Their intersection is
the observed engine shape of a normal monster: display category `4` +
`Character`. A target failing either stock classification returns the same
invalid-placement result (`1`) used by Fl00. No prototype names or stock
monster roster are hardcoded. Palace Fl00 continues to point directly at its
original validator.

Stock target authorization continues through `0x0045CBF0`. Its final test asks
the selected target's relation table at `+0xA4` for key `ARA2`, the Attack
Flag's shipped unit-description ID, and rejects an already attached relation
owned by the placing player. That is stock's pre-creation duplicate guard.
Stock Attack uses `ARA2` for both description and art, making those identities
ambiguous until the private clone separated them. A focused live test proved
that private art key `ZCA2` does not find an attached Capture Flag, while
private description key `ZCF0` does. The private validator repeats the same
relation-table lookup at `0x005A7730` with only the description key privatized
from `ARA2` to `ZCF0`. Capture placement belongs only to the player's Zoo,
making any attached `ZCF0` the private equivalent of stock's same-player
match. This check runs in both the
hover validator and the independent completion authorization, before reward
deduction or flag creation. Palace Fl00 retains its literal `ARA2` test.

Fl00 also reports its ordinary placement-ready state before the cursor has an
agent selected. The wrapper preserves that stock mode initialization but maps
the empty selected-agent slot to invalid result `1`; it never dereferences the
slot. This is target validation only and does not add a new placement state.

Stock completion does not trust the hover validator as an authorization gate.
The Fl00 completion callback independently calls `0x0045D2D0` at
`0x0045D4AC`, receives either the selected-agent pointer or zero, and only then
enters reward deduction and flag creation. The relocated private completion
callback redirects that single internal call to a private check with the same
two-argument shape and pointer/zero return contract. The check calls the full
stock `0x0045D2D0` first, returns zero on any stock rejection, and returns the
stock pointer only when that agent also passes category `4` plus
`Monster_Player` ownership.
Every subsequent completion instruction remains the relocated stock clone.
This prevents creation on non-monsters even if the UI attempts completion;
Palace Fl00's callback continues to call `0x0045D2D0` directly.

Only the private ZC01 AP41 object receives a cloned primary vtable whose command
handler substitutes `ZCF0` for `Fl00` on Capture placement and on the two live
reward-adjustment paths. All unmodified commands tail-call the stock AP41
handler. Palace AP41 retains its stock vtable and all three literal `Fl00`
paths, so Palace Attack Flags are isolated from Zoo capture.

The stock Fl00 registration constructor receives eight arguments. Its second
argument is cursor selector 5; adjacent Fl01 passes selector 6 with otherwise
the same cursor-selection shape. `CUR1Tactical Cursor` maps those selectors to
animation sets 1005 and 1006, which reference Attack TILE 27 and Explore TILE
26 respectively in all three cursor states. CUR1 already contains selectors
through 31. The private registration therefore changes only its cloned second
argument to selector 32, while a literal CUR1 clone appends set 1032 by copying
set 1005's three-state record and redirecting its TILE reference to the private
Capture cursor. All 28 original sets retain their original TILE numbers; the
package populates those exact positional entries with byte-for-byte stock TILEs
rather than relocating cursor art to appended indices. CUR1 TILEs mix embedded
palettes with references into `interfacedata.cam`'s seven-entry `PALT` section,
so the private interface CAM carries that literal table as well. This preserves
the index-sensitive cursor mask path used when flag placement returns control
to interface or window chrome; only set 1032 uses an appended TILE.

`Restore_Capture_Flag` clones the stock overlay description and GPL
`Flag_Attack` prototype. It retains shipped `AP46`,
`RewardFlag` type, internal `Flag_Attack` title, and hero bookkeeping fields.
Keeping the internal title is required because shipped hero reward evaluation
recognizes attack work by testing `flag.title == "flag_attack"`. Its birth,
poll, target-death callback, and manual-death functions are private clones of
the abandoned Zoo lifecycle so a lethal event attempts capture rather than
paying the ordinary Attack Flag bounty. Stock `Flag_Attack` and
`attack_flag_birth` are not overridden.

## Private Capture Flag art clone

Base `Data/maindata.cam` contains both complete flag image families:

| Resource | Special | Minimap | Interface |
| --- | ---: | ---: | ---: |
| `ARA2flag attack` | 12 frames, TILE 16655–16666 | 4 frames, TILE 16667–16670 | 4 player-color directions, TILE 16671–16674 |
| `ARA4Flag Explore` | 12 frames, TILE 16675–16686 | 4 frames, TILE 16687–16690 | 4 player-color directions, TILE 16691–16694 |

Both resources use the same three-set overlay topology: animation set 64 for
the world flag, set 300 for the minimap, and set 1000 for the interface image.
The world and minimap records are indexed-v3 TILEs; the interface records are
100x100 RGB565 v1 TILEs. Attack is a red pennant with crossed blades; Explore
is a pale green banner with an eye.

Private `ZCA2Capture flag` is an exact IMAG-topology clone of ARA2. Every one of
its twenty referenced TILEs is redirected to appended private slots beginning
after the complete 17,224-entry retail table. The original positional slots are
empty fall-through entries, following the same proven private-art pattern used
by the Alchemist and Haunt packages. The private world frames preserve ARA2's
canvas, hotspots, frame order, and wave motion while selecting stock palette
793, which already contains the Explore family's green, gold, and player-blue
range. The minimap frames preserve their 7x7 canvases; the four interface
directions preserve ARA2's player-color order: blue, green, orange, magenta.
Indexed-v3 render art requires its palette table in the emitting maindata
package. Following the proven Alchemist and Haunt packaging shape, the private
CAM therefore carries literal base palettes 0–793 and loads before the MX Zoo
CAM. The later MX package remains the final provider for its own 0–287 palette
range, while private palette 793 remains available to ZCA2. No `ARA2` or
`ARA4` IMAG record is emitted by the private CAM.

The AP41 Capture-row icon is not supplied by ARA2's Interface set. Stock
`SMNU/AP41` command `0x1B59` paints `INTCItem Icons` set 1011, whose sole frame
is embedded-palette V1 TILE 92 at 25x25. ZC01 changes only that icon control's
resource token to private `ZCIC`; every other AP41 control remains byte-for-byte
stock. `ZCICItem Icons` retains the complete stock INTC set table and redirects
only set 1011 to one appended private TILE. Stock INTC and all its consumers
remain unchanged.

The private birth originally converted the monster immediately. The restored
front half instead keeps ZCA2 attached while the monster remains hostile and
uses the abandoned `zoo_flag_poll` seeker cleanup. The target's death callback
remains untouched; the private overlay's stock-native engine callback owns the
capture attempt and flag cleanup.

## Confirmed GPL prototypes

`SDK/OriginalQuests/GPLMx/mx_Building_Data.dat` defines `Zoo1`, `Zoo2`, and
`Zoo3` as ordinary `Building` prototypes. All three use:

- `basic_birth`;
- `Building_Birth`;
- `building_death`;
- `basic_upgrade`.

Levels 1 and 2 also contain `Visited_Script Upgrade_Equipment`. This exactly
matches Blacksmith behavior and agrees with the Blacksmith placeholder prose in
`MX09`; this repository records it as unfinished copied scaffolding.

Those prototypes were not merely left as SDK source: expansion bytecode
`DataMX/MX_Data.bcd` contains `Zoo1`, `Zoo2`, and `Zoo3`. A standalone
`base="Any"` mod cannot rely on that expansion-only registration when Original
rules are selected, and it must not duplicate those names when expansion rules
are selected. Following the proven Haunt package, this mod carries literal
private clones named `Restore_Zoo1`–`Restore_Zoo3`.

## Confirmed capture source

`SDK/OriginalQuests/GPLMx/TaskModules/Buildings/Zoo.gpl` preserves most of a
capture lifecycle:

- a Zoo flag points at a target monster;
- its chance is `50 * sqrt((reward / 20) / target max HP)`, capped at 95%;
- a successful death interception restores one third of the monster's HP;
- the nearest living hero inside the stock radius receives control;
- the flag is deleted after the attempt;
- cancellation and polling clean pursuing heroes' tasks.

That module does not provide a working player-facing dispatcher, flag unit
description, private placement wiring, or completed UI control. The private
Capture Flag now supplies those missing front-end pieces and scopes lethal
interception to only its current target.

The earlier Reward Flag binding probe proved the conversion seam when it was
temporarily attached to `attack_flag_birth`. The private
`Restore_Capture_Flag_Birth` now carries the exact gate that passed live
testing: `$ListObjects` from the flag, type `Building`, followed by
`#MyPlayer`, title `Zoo`, and `FirstStageBuilt == 1` in stock Mausoleum order.
The shipped `attack_flag_birth` binding is no longer replaced.

The active trigger restores GPLMx's `monster_gravestone` interception at the
same point as the abandoned source. Its failure branch is the literal stock
gold, Dead-type, thread-resume, `be_dead_2`, interval, and `basic_death` tail.
An earlier global attempt entered missing expansion-only fields and aborted,
leaving monsters half-dead; the current gate never reads those fields.

The direct `zoo_agent` read is recovered, not inferred, but it cannot be used
under Original rules: `Monster` there declares no such field. The compatibility
clone instead performs stock RewardFlag enumeration at the earlier
`monster_gravestone` boundary and selects only subtype `Capture_Flag` whose
engine-owned `TargetID` resolves to the dying monster. This adds no persistent
state. Its `Flag_Attack` title remains unchanged because stock hero evaluation
checks that title. The later overlay callback is the literal abandoned
`zoo_flag_death_callback` and only deletes the flag.

The surviving `Set_Subdue_Chance` contains a definite field-name mismatch: it
writes `subdue_percentage`, while `zoo_flag_check` reads
`charm_percentage` and `mx_prototype.gpl` declares only the latter on
`RewardFlag`. Original declares neither field. The focused `ZooTrace.GMP` save
contained the private flag and its Birth/Death functions but neither missing
field nor the target callback, proving that the first expansion-only write
aborted Birth. The active clone now computes the unchanged RewardCost/MaxHP
formula and 95% cap directly at the lethal event. The one-shot attached-flag
lookup is the required Original-rules compatibility repair around the recovered
check.

The abandoned success branch sets one-third HP before calling the actual stock
`Control_Monster`. It does not call `ClearEngineDeathFlags`, Agrela, Phoenix, or
any resurrection path. Failure runs the literal stock gravestone tail; success
suppresses it exactly as GPLMx `monster_gravestone` intended.
The private seam
then changes only the controlled target's eventual BackScript so the completed
stock delayed-control transition enters the already-proven Hooligan-to-Zoo
delivery lifecycle.

`TaskModules/Subtasks/mx_Control_Monster.gpl` supplies the stock protection
lifecycle for a creature changing sides. `Control_Monster` comments that its
temporary setup exists so other units stop attacking the target, assigns
`Type = Hidden`, transfers the target to the controller's player, and runs
`fake_wander`. After the shipped 3300 ms `Charm_Delay_Time`,
`Become_Controlled` exposes the allied Hero type and clears Hostiles. The Zoo
now calls that actual stock function. Its private BackScript runs only after
stock completion, deletes the infinite `Charm_icon`, releases the temporary
`Num_Followers` increment using stock controlled-monster death cleanup, and
changes the final Controlled state to Hooligan arrest.

This also matches the target-selection path used by Priestess familiars and
charmed monsters: `list_enemies_seen` lists only Hero and Monster agents on
`#NotMyTeam`. Hidden invalidates an already-selected target; player allegiance
plus the final Hooligan type keep it out of subsequent minion enemy lists.

The Wizard's Curse quest supplies the isolated test contract.
`Be_Dumb`/`Hooligan_Check` assigns a hero stock `Arrest_Hooligan`, which keeps
the hero near its moving target while retaining low-HP and danger evaluation.
`Hooligan_Basic` recognizes that targeting hero, marks itself found, and hands
its own movement to `Hooligan_Goto_Palace`. The target independently enters the
first Palace and is consumed. This milestone privately clones those two
monster-side functions and substitutes an available completed Zoo for
the first Palace. The stock `Hide`, notification, deletion, and quest flag
lifecycle is retained; pacing and reset ownership are the private seams noted
below.

`Generate_Character_Attributes` installs `Be_Dumb` as a quest-wide Wizard's
Curse wrapper. The actual successful arrest branch is smaller:
`Hooligan_Check` writes the intent and Target, then `Be_Dumb` writes Counter 0
and ActiveScript `Arrest_Hooligan`. Installing the whole quest wrapper at
runtime in an unrelated scenario left it owning the hero's reset lifecycle.
The mod now copies only those successful-branch writes and leaves every native
hero script field unchanged.

`#intent_arresting_hooligan` is stock intent number 117. The matching indexed
record is `STRT/AITX[117]`, whose shipped text is “Arresting a hooligan.” The
mod packages the complete stock AITX table with only that record's text changed
to “Capturing a monster”; the GPL continues to call the same stock intent.

The abandoned Zoo's shipped `zoo_flag_poll` treats a hero as having abandoned
its monster when `hero.Target` no longer equals the flag target; it removes that
hero from the seeker list. The private Hooligan return uses the same target-loss
signal to clear the single-owner claim and re-enter its existing Hooligan Basic
lifecycle, where one different hero can receive the stock arrest handoff.

The shipped Hooligan unit description declares `Speed 5`, but GPL uses
`ATTRIB_Speed` for threat and escape comparisons. Actual travel remains tied
to the unit's movement attachment and `MovementRateModifier`; changing the AI
rating did not change a converted Harpy's live pace. There is no stock
Hooligan speed-sync path. Stock war-party followers instead compare distance
to their declared `leader` and change movement state around a formation radius.
The private Zoo arrival applies that closest stock pacing shape with the
existing `#Arrest_Hooligan_Dist` of 50, stopping the Hooligan until its paired
hero catches up and then resuming the same `Hide` trip.

Stock Palace arrival resets heroes whose Active or Back script is
`Arrest_Hooligan` only when the globally last Hooligan arrives. That global
cleanup is insufficient after privatizing each Hooligan to one `leader`: a
specific hero may otherwise retain a delivered target while unrelated
Hooligans remain. The Zoo arrival therefore applies stock `Reset_Tasks` to its
exact owner on every delivery after its reservation has become a stored
occupant.

Stock expansion `Check_Mausoleum` queries completed player-owned Mausoleums,
copies each building's generic `Occupants` list, compares `$ListSize` with
`#Mausoleum_Limit`, and uses the first legal building. Zoo admission now copies
that exact query/list/first-legal shape. The requested Zoo values replace the
fixed Mausoleum constant: the stock building `Level` field selects 4, 6, or 8
visitors at levels 1, 2, or 3.

Mausoleum interment hides and stores synchronously, but a Zoo captive travels
with a hero. The captive uses its already-declared Monster `Target` field for
the selected Zoo. Pending capacity requires the complete stock arrest ownership
shape: a valid living `leader`, that hero's `Target` still naming the captive,
and `Arrest_Hooligan` active or stored as its back task. Hidden/Hooligan agents
without that live pairing remain queued and do not consume capacity. Before a
queued captive receives a hero, assignment compares `Occupants` plus those real
pairings against the level limit. This latch definition is Zoo integration, not
recovered stock functionality, but adds no watcher, thread, counter, or
prototype field.

`Check_Mausoleum` performs its `Occupants < limit` comparison immediately before
the synchronous storage step. Zoo arrival repeats that exact comparison before
`Enter_Building`; a late delivery that no longer has room releases its owner and
returns to the existing unlatched Hooligan lifecycle. This final stock boundary
prevents reservation drift or controlled-unit crossover from overfilling the
generic occupant list.

Stock monster birth assigns `ATTRIB_Zoo_Legal_Target`, documenting it as the
Zoo flag interface's legality channel. The private `ZCF0` gate reuses that
stock attribute on the selected Zoo as its current capacity bit. Stock
`Building_Birth` remains first in the completion callback; the mod refreshes
the bit afterward. Stock `building_upgraded` dispatches `upgradescript` when
construction starts, before `BuildingReachedMaxHP` calls
`UpgradeAgentAttributes` and installs the new prototype `Level`. The shipped
Palace handles this boundary by having `palace_upgrade` queue the upgrade and
schedule `upgradescript2`, while `palace_upgrade2` reschedules itself at
`#palace_upgrade_check` until `CurrentStageBuilt == 1`.

The focused `ZooTrace.GMP` checkpoint showed a real level-two Zoo with four
occupants and a false capacity bit. Its serialized GPL fields contained
`birthScript2` and `upgradescript` but no `upgradescript2`: generic stock
`Building` does not declare that Palace/Outpost-only field, so the DAT compiler
discarded the attempted assignment and the completion poll never ran. The Zoo
now copies the same Palace timing and test through its declared `birthScript2`
slot. That callback still runs ordinary `Building_Birth` on initial completion;
when scheduled after an upgrade begins, it reschedules at the same stock
interval until `CurrentStageBuilt == 1`, then substitutes only the Zoo capacity
refresh for Palace's guard/tax/peasant restarts. Reservation, delivery, and
captive death refresh the same bit.
Both native target-authorization passes require this bit before the already
proven category-4 Character test, so a full Zoo rejects clicks before flag
creation while Palace `Fl00` remains untouched.

The private Capture-button wrapper also reads that bit before it tail-calls the
unchanged stock `SetFlagMode`. On a full Zoo it instead copies Majesty's native
placement-failure alert sequence: `0x0046ABE0` selects the standard alert
presentation and shipped helper `0x0046ACE0` constructs, posts, and destroys a
literal engine string. The completion check retains the same alert branch for
the narrow race where capacity becomes full after the cursor was armed. No
custom message queue, timer, or UI controller is introduced.
`SetFlagMode` normally returns with `RET 8`, consuming the mode and reward
arguments pushed by AP41. Because the full-Zoo branch deliberately bypasses
that callee, it performs the identical eight-byte return cleanup before the
private panel handler restores its registers.

The generic Visitors-menu control is restored independently: MX09 already
contains the Visitors strings, rectangle, command ID `0x1F55`, and the first
0x84 bytes of AP02's stock control, but its record ends 16 bytes early. The mod
replaces only that truncated record with AP02's complete 0x98-byte control.
On delivery, the captive is already a valid agent hidden inside the
destination. The arrival then calls stock `Enter_Building`, whose complete
functional body plays `Spawneffect_In` and appends the agent once to the
building's `Occupants` list, before stopping the stored agent's active thread.
The call is deliberately not used for travel: stock `Enter_Building` has no
active movement or `Hide` statement. It does not copy hero-specific death,
guild, intent, resurrection, or home logic.

Stock occupants do not require a visitor-specific text formatter. Both
`TaskModules/Buildings/Gambling_Hall.gpl` and
`TaskModules/Buildings/Lived_In.gpl` write the occupant's
`ATTRIB_AIIntentionString` through `SpecifyIntent` as part of the ordinary
`Enter_Building` lifecycle; the visitor row then renders that stored intent.
`Lived_In` uses the exact order needed here: enter the building, specify the
inside-building intent, then schedule the occupant's next lifecycle step. The
Zoo delivery copies that order, specifying its private intent after
`Enter_Building` and before stopping the captive's active thread.

`DataMX/mx_gpltext.cam` ships indexed `STRT/AITX` records 177 through 199 as
literal `empty` placeholders. The Zoo assigns placeholder 199 to
`#intent_waiting_in_zoo` and changes only that reserved record's text to
“waiting in the zoo.” The stock row supplies “is,” yielding the requested
“is waiting in the zoo” display without a Zoo branch in the generic painter.

Live inspection confirmed that each delivered monster remains a valid
`VehicleRec`, appears in the Visitors controller's unit vector, and owns a
selectable row whose stored agent ID opens the correct monster primary panel.
Static tracing proved that the blank display was the native row painter's
category gate, not formatting or occupant ownership. The standalone Generic
Visitor Lists patch now routes that discarded category through the stock hero
row and calls the shipped `IX92`/`IX94` monster-icon resolver.

That resolver's stock caller runs only where expansion interface resources are
already loaded and assumes its atlas exists. Deal with a Demon does not load
`DataMX/mx_interfacedata.cam`; calling the resolver there without its resource
faulted in the stock atlas-list accessor. The Zoo therefore exposes literal
`IX92` and `IX94` IMAG records through `restore_zoo_interfacedata.cam`, together
with the complete 785-entry positional TILE table from the same stock archive.
With that prerequisite loaded through the ordinary `base="Any"` dataset, live
testing rendered the correct Harpy and Troll icons and preserved row selection.

Stock `Hooligan_Check` uses `Is_Free_Task`; the latter has
`#is_free_task_max_heroes 2`, an inclusive allowance check, and a closer-hero
takeover rule. For single ownership, the current milestone instead copies the
abandoned Zoo's one-hero selection and stock `Control_Monster`'s declared
`Monster.leader` link. The shipped arrest task and all later behavior are
unchanged; the private assignment applies its normal successful entry state to
only that linked hero. The subsequent stock `Control_Monster` Hidden delay and
player-allegiance transfer protect the captive from allied minions before the
Hooligan state becomes active.

## Original-design interview

In the archived June 12, 2001 Cyberlore chat, Jay Adan reads the Zoo entry from
the 1996 original design guide: three levels, player-set capture rewards,
higher Zoo levels for higher-level monsters, income based on contained monster
types, and a danger that monsters might escape. He cautions that this may not
match the later expansion implementation. The same chat describes the Theater
as a one-level building whose selected plays would alter hero-class behavior,
with additional plays unlocked by elves and kingdom events.

Source: <https://archive.kontek.net/majesty.strategyplanet.gamespy.com/iv20010613.shtml>

## Closest stock analogue

The Blacksmith is the closest evidenced three-level shell, not merely a
thematic guess: the abandoned Zoo's visit field and dialog prose were copied
from it. Missing XML values are consequently cloned from Blacksmith levels
1–3, with deviations listed in `invented-content.md`.

The stock Palace construction dispatcher also requires every buildable or
upgradeable description ID to have a row in `DATA/BDEP`. Blacksmith levels
`ABC1`, `ABC2`, and `ABC3` each use the table's empty/no-prerequisite form. The
restored Zoo mirrors that lifecycle with rows for `ZOO1`, `ZOO2`, and `ZOO3`.
Without those rows the Zoo can appear in the menu, but the Build button rejects
the request before placement mode begins.

Majesty retrieves only one effective `DATA/BDEP` record. It does not combine
records from multiple enabled mods. The Zoo package contains a complete stock
table plus its own rows and has no runtime dependency on Haunt or Alchemist.
