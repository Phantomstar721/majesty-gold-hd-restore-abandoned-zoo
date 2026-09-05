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

MX09's bottom full-panel art control selects expansion `IX01` set 1004. A
separate control above it selects `INBgbuilding dialog` set 1000 at rectangle
`(0,0,202,245)`. The indexed V3 `INBg` TILE draws stock outer chrome and uses
transparent plus reserved control-color pixels; changing or re-encoding that
overlay produced literal magenta artifacts and damaged the frame.

Stock AP10 demonstrates the correct two-layer guild contract: its bottom
full-panel control selects `INTIraw textures` set 1029, which resolves to the
ordinary 200x245 raw-texture TILE 474, while its next full-panel control keeps
`INBg` set 1000 as the chrome/mask overlay. The custom Alchemist Laboratory
uses private `ALTI` with its themed 200x245 TILE in that raw layer. The Phantoms
Haunt uses the same arrangement as private `PHTI`, remapping the three stock
guild backing TILEs 466, 474, and 495 to one opaque themed TILE packed from
stock template 466.

The Zoo now copies that established arrangement literally. MX09's existing
bottom control changes from `IX01` set 1004 to private `ZOTI` set 1029. `ZOTI`
is a complete private clone of stock `INTI`; every referenced TILE is moved to
an appended private slot, and only backing TILEs 466, 474, and 495 receive the
Zoo's opaque 200x245 master. MX09's `INBg` set-1000 control and its other
`INBg` control remain byte-for-byte stock, preserving their frame, masks, and
reserved palette behavior. Stock `INTI`, `IX01`, and every unrelated dialog
remain untouched.

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
to appended private positions, and only set 1019's backing is replaced. Private
`SMNU/ZC01` changes its set-1019 background token from `INBg` to `ZOBG`.
Stock AP41, MX09's two `INBg` controls, every other `INBg` consumer, and all
functional control records remain unchanged.

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
against available gold, enables the four +/- controls, and paints Attack amount
control 8, Explore amount control `0x138C`, and gold display control `0x1F4D`
(8013). Stock handler `0x004A92F0` mutates Attack through decrease/increase
controls 10/11 and Explore through controls `0x1388`/`0x1389`; Attack action
control `0x138A` (5002) then passes the selected value to `SetFlagMode`.
Reusing AP41 unchanged therefore made ZC01 and Palace Attack
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

The Fl00 registration begins with `push 0x20` before stock `operator new`; that
literal is the placement-mode allocation size and the private clone preserves
it unchanged. A later `0x20` stack-state marker at registration offset `0x14`
is a different field. The standalone clone advances only that later marker to
`0x22`; it must never be mistaken for permission to allocate a 0x22-byte mode
object.

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
animation sets 1005 and 1006. Their complete stock frame sequences are
`[27, 27, 24, 27, 25]` and `[26, 26, 24, 26, 25]`: the three primary frames
use Attack TILE 27 or Explore TILE 26, while interface transitions share common
state TILEs 24 and 25. CUR1 already contains selectors
through 31. The private registration therefore changes only its cloned second
argument to selector 38, while a literal CUR1 clone appends set 1038 by copying
set 1005's three-state record and redirecting only its three primary TILE-27
references to the private Capture cursor. Its common-state 24/25 references
remain literal. All 28 original sets retain their original TILE numbers; the
package populates every referenced positional entry—including 24 and 25—with
byte-for-byte stock TILEs rather than relocating cursor art to appended
indices. CUR1 TILEs mix embedded
palettes with references into `interfacedata.cam`'s seven-entry `PALT` section,
so the private interface CAM carries that literal table as well. This preserves
the index-sensitive cursor mask path used when flag placement returns control
to interface or window chrome; only set 1038's primary frames use an appended
TILE.

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
Frame references are parsed from Majesty's authoritative end-anchored
frame/lane table, not from a fixed offset after the direction header. This is
material for set 300: its four private Minimap frames resolve to appended TILEs
17236–17239; the older fixed-offset interpretation silently left those typed
fields pointing at TILEs 0, 2, 100, and 0. The package validator repeats the
end-anchored parse and requires the complete private sequence 17224–17243.
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
clone keeps GPLMx's direct boolean call from `monster_gravestone`; inside that
check it performs stock RewardFlag enumeration and selects only subtype
`Capture_Flag` whose engine-owned `TargetID` resolves to the dying monster.
This avoids an agent-valued helper return at the lethal boundary and adds no
persistent state. Its `Flag_Attack` title remains unchanged because stock hero
evaluation checks that title. The later overlay callback is the literal
abandoned `zoo_flag_death_callback` and only deletes the flag.

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

Stock `#intent_arresting_hooligan` remains intent number 117 and its shipped
text remains “Arresting a hooligan.” The mod packages the complete stock AITX
table with expansion placeholder row 198 changed from `empty` to “Capturing a
monster,” declares private `#intent_capturing_monster 198`, and uses that
private intent only for Zoo capture. The merge manager can therefore privatize
the package-added row without replacing stock Hooligan wording globally.

The abandoned Zoo's shipped `zoo_flag_poll` treats a hero as having abandoned
its monster when `hero.Target` no longer equals the flag target; it removes that
hero from the seeker list. The private Hooligan return uses the same target-loss
signal to clear the single-owner claim and re-enter its existing Hooligan Basic
lifecycle, where one different hero can receive the stock arrest handoff, but
only before `Hide` completes. A focused September 3 live trace caught a
Ratman Catapult alternating between hidden and reassigned ownership without
ever reaching `Enter_Building`: `Hide` completed between active-script cycles,
the hero had naturally cleared its arrest state, and the private abandonment
check incorrectly ran before the stock hidden-arrival branch. Stock
`Hooligan_Goto_Palace` gives its completed `Hide` lifecycle priority. The Zoo
clone now does the same; only an outside captive can be abandoned and
reassigned.

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

`Check_Mausoleum` does not return from its `foreach`: it appends each legal
building to `legal_mausoleums`, then selects `$ListMember(..., 1)` after the
loop. `Restore_Find_Available_Zoo` preserves that control flow with
`legal_zoos`. This is required on beta2 because returning a function result
while `foreach` owns the evaluator frame can fault the GPL interpreter.

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
`Building_Birth` remains first in the initial completion callback; this starts
the declared revenue thread before the mod refreshes the capacity bit. Stock
`building_upgraded` dispatches `upgradescript` when
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
now uses the same function-valued `birthScript2` slot for two stock phases. The
initial callback literally calls `Building_Birth`, as `Fairgrounds_Birth` does,
then points that slot at a private `palace_upgrade2` clone. `Restore_Zoo_Upgrade`
also installs that callback before scheduling it, so older saved buildings
enter the corrected upgrade path. The callback reschedules at the stock
interval until `CurrentStageBuilt == 1`, restores itself after the new
prototype is installed, and substitutes only the Zoo capacity refresh for
Palace's guard/tax/peasant restarts. Reservation, delivery, and captive death
refresh the same bit.
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
building's `Occupants` list, before assigning the stored agent a private clone
of the stock Guardhouse occupant task.
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

## Visitor revenue and destruction release

`TaskModules/Buildings/mx_Auto_Revenue.gpl` supplies the closest stock dynamic
income lifecycle. `Fairgrounds_Revenue` validates the true Palace, reads a
building-owned participant list, computes one revenue pulse, and calls
`Give_Gold` on the building. `Building_Birth` starts any declared
`RevenueScript` at its declared `Revenue_Time`. The Zoo declares that same
thread shape at 60,000 ms and substitutes its existing `Occupants` list for
Fairgrounds `combatants`. Each valid occupant is counted directly, without a
second living/dead filter, because the stock capture lifecycle deliberately
keeps a subdued agent hidden in `Occupants`. Its multiplier comes from stock
`ATTRIB_LevelXP`, the designer-authored kill bounty read by normal monster
combat. The seven private rank boundaries are shared with Generic Visitor
Lists; the GPL calculation is independent of that display patch.

An earlier shared initial/upgrade callback tested `FirstStageBuilt` before
calling `Building_Birth`. Stock `BuildingReachedMaxHP` queues `birthScript2`
with a one-tick delay and then sets `FirstStageBuilt = 1`, so that test always
skipped the revenue-thread launch. The corrected initial callback follows
`Fairgrounds_Birth` and calls `Building_Birth` unconditionally. Stock
Marketplace levels two and three put `Building_Birth` in the upgraded
prototype's `birthscript`; the corresponding Zoo levels use the private wrapper
there as well, so each `UpgradeAgentAttributes` transition restarts the declared
revenue lifecycle instead of losing it after an upgrade.

Both physical building attacks in `make_attack` and player-spell reactions in
`react_player_spell` call global `release_occupants` immediately when a
building is hit. `building_death` later sets `Type = Dead` and calls the same
function before rubble and deletion. Northern Expansion already changes that
function so a living building titled `Mausoleum` retains its occupants, while
a dead Mausoleum processes them. The private GPL symbol is a literal copy of
that function with one sibling branch gated by `Title == Zoo` and the stable
private `Restore_Zoo_Revenue` function declared on all three Zoo prototypes.
Because generic occupant-bearing buildings do not all declare the optional
`RevenueScript` field, the private discriminator first copies the stock
`HasAttribute` access pattern before reading it. A focused load trace caught the
unguarded read against `agent#24`; the guard preserves the ordinary stock
branch instead of raising a GPL error.
The earlier `birthScript2` discriminator was not stable because the capacity
upgrade callback intentionally repoints that function slot. The corrected
branch returns without action while that Zoo lives and processes captives only
when the existing stock death call reaches it. Every non-Zoo and Mausoleum
statement remains in stock order.

`Reset_Controlled` is the shipped end-of-charm lifecycle. It restores
`Monster` type, the immutable `StartingScript` to all three task slots,
`Monster_Gravestone`, `Monster_Player`, and clears charm ownership state.
Generic `monster_birth` populates that supposedly immutable field from the
post-override `BasicScript`, but shipped `war_party_Birth` starts its thread
without the assignment. The paused ZooTrace save exposed the consequence on
Goblin Priest agent 68: after breakout it was `Monster / Controlled`, had no
leader or target, and serialized null `StartingScript`, `ActiveScript`,
`BasicScript`, and `BackScript`. Its prototype normally declares `war_party`
in all three live task slots. The Zoo now copies the exact generic
`monster_birth` assignment before `Control_Monster` whenever the field is
missing, with stock `wandering` as the only fallback when no valid basic task
exists. Capture otherwise leaves `StartingScript`, `attack_action`, and the
original idle/guardian behavior untouched. At dead-Zoo release, each valid stored
captive first runs stock `Exit_Building`, which resets tasks, unhides it, and
plays the normal exit effect; it then runs `Reset_Controlled`, receives `MaxHP`,
and clears the two Capture-only target prohibitions. Before that boundary, the
existing stored task is rescheduled at stock `Normal_Cycle`; older saves whose
already-stored captive still lacks `StartingScript` receive stock `wandering`
before `Reset_Controlled`. Stock `Guardhouse_Visited` enters
the visitor and assigns `Garrison_Scan_Or_Leave` to its still-running
`ActiveScript`; that function obtains the containing building through
`GetBuildingContainer`, makes a `RandomNumber(100) + 1` roll, and calls
`Exit_Building` on success. The Zoo clones that active occupant lifecycle and
replaces only the ordinary exit with its already-proven hostile captive release
helper. Killing or suspending the captive task at delivery left correct script
pointers on release but no running monster behavior after `Exit_Building`.
Calling `Reset_Controlled` before `Exit_Building` also failed: the exit restored
the captive's saved Hooligan/breakout task after the reset. The paused ZooTrace
save showed that exact result on Troll agents 13, 24, and 135: all were outside
any building with no leader or target, but retained `Hooligan / Controlled` and
all three task slots still pointed at `Restore_Zoo_Breakout_Check`. The corrected
order exits first and resets second. The breakout task also contains a one-shot
no-container repair so those persisted pre-fix agents re-enter stock hostile
monster control on their next tick.

## Tame Beast

Expansion `SMNU/MX04` opens the Mausoleum's `SMNU/MX05` selected-occupant
panel. `MX05` populates control `0x1388` directly from the parent building's
`Occupants` list with no hero filter, refreshes cost control `0x1F46` from
`Mausoleum_Resurrect_Cost`, and queues the paid action from control `0x138B`
to `Mausoleum_Resurrect_Begin`. The stock GPL action obtains the selected
agent's building container, removes that agent from `Occupants`, unhides it,
then restores live scripts. The private Zoo panel clones this complete flow;
the CAM Merge Manager privatizes its dialog, open command, queued command, and
two GPL callback symbols so stock Mausoleums remain untouched.

Static tracing on beta2 confirms MX05 setup reaches the same shared row painter
used by the ordinary Visitors controller. The existing Generic Visitor Lists
hook therefore supplies monster icon and Threat Rank rendering to both views;
the Tame panel requires no second renderer or monster-title table.

Expansion `Epic_Quest_Scripts.gpl` supplies the released-monster analogue. Its
controlled Varg is classified as `Hero` / `Controlled`, keeps `Monster` as its
enemy type, and assigns stock `Guardian` to all three task slots. `Guardian`
wanders around `coord_home`, uses the normal monster
enemy evaluator and attack functions, and abandons pursuit outside its home
radius. Tame Beast copies those fields and uses the player's true Palace as
`coord_home`, falling back to the Zoo only if that Palace is invalid. The
Palace substitution is Zoo-specific balance; the coordinate field and patrol
lifecycle remain the literal stock Guardian mechanism.

The special quest Varg overrides `Guardian_Mod` to 2, whereas nearly every
entry in expansion `mx_Monster_Data.dat`—including the White Wolf's native
prototype—uses the generic guardian value 5. Tame Beast uses that stock generic
value. `Guardian_Eval_Enemies` searches only raw `#ATTRIB_SightRange`; it does
not multiply acquisition by `Guardian_Mod`. Expansion Epic Quest Palace guards
are spawned with sight 250, so Tame Beast applies 250 as a minimum and leaves
any stronger monster value unchanged. Applying those inputs to all Zoo tames
is balance glue; no Guardian targeting or movement code is replaced.

## Hero rental

Expansion `SMNU/MX22` supplies the exact paired Embassy controls. Its close
record occupies bytes `0x40..0xCC` and dispatches `0x22AC`; its open record
occupies `0x114..0x1A0` and dispatches `0x22AB`. Both are 140-byte records at
rectangle `(7,219,139,21)` and differ only in their label/tooltip fields, one
internal presentation word, and command. The native MX22 controller reads
`ATTRIB_EmbassyActiveFlag` from the selected building, submits order type
`0x16`, and swaps the two controls on refresh. That order also creates or
cancels `GS_EmbassyRecruitOrder`, so the Zoo may clone only the state and
presentation seam—not the order itself.

Base-game `SMNU/AP10` supplies the exact complete action presentation needed
for the Zoo's two-column row. Its secondary-panel record occupies
`0xD2C..0xDF0`, uses rectangle `(103,162,93,26)`, and selects `INBb` set
`1009`. The Zoo clones that full 196-byte control for all three presentations,
changing only rectangle, text indices, art selection, and command. RENT selects
stock `INBb` set `1004`, whose four 93x26 HEROES state tiles are the same
gold/parchment family. REWARD selects private `ZCBB` set `1009`; its IMAG is an
exact private copy of `INBb`, with only stock TILEs 739-742 replaced by
dimension-matched Capture-glyph variants. TAME selects a second exact private
copy, `ZTBB` set `1009`, whose same four TILEs carry a horned-monster glyph.
MX22 still supplies the open/closed state and visibility lifecycle; AP10
supplies only the stock button record and presentation.

All expansion hero decision trees call `Purchase_Equipment` after `rest`, then
call `Purchase_Bazaar`. Within `mx_Purchase_Equipment.gpl`, the final nested
branch is `Stat_Boost_Check`; only after every gear and consumable check has
failed does the tree proceed to the Bazaar. `Purchase_Bazaar` considers all six
researched item slots before its final false return. The rental check is
composed at that later false boundary. Its search distance and
completed-player-building query use the same stock shopping expressions. The
random consideration gate is copied literally from `Stat_Boost_Check`,
including `#Percent_Chance_To_Buy_Stats`.

Stock `Use_Building` travels to the selected target, hides the hero, adds it to
that building's `Occupants`, and dispatches the building's `Visited_Script`.
`Upgrade_Equipment` then supplies the visit-duration handoff;
`Obtain_Upgrade` demonstrates revalidation/payment through `Spend_Gold`; and
`Done_Enhancing_Equipment` exits and resets the hero. The Zoo rental callback
uses the same boundaries, changing only the purchased result.

The result is the literal expansion Cultist path in
`mx_Control_Monster.gpl` and `mx_Controlled_Monster.gpl`.
`Control_Monster` increments `Num_Followers`, transfers player ownership,
creates `Charm_icon`, records the hero as `leader`, and schedules
`fake_wander`. By default, `Become_Controlled` installs `Controlled_Monster`,
which wanders near the leader and calls the normal monster enemy evaluator while
moving. The same shipped module supplies `Monster_follow`: if the leader owns a
valid target inside the follower's `SightRange *
Mon_Atck_Obj_Pursuit_Range_Mod`, it copies that target and dispatches stock
`monster_attack_object`; when the target is farther away it travels back to the
leader; otherwise it resumes the same near-leader wander. Rental changes only
the `BackScript` consumed by `Become_Controlled`, selecting `Monster_follow`
behind a private wrapper that first preserves `Controlled_Monster`'s stock
`leader_dead` gate. Its death callback still decrements the same follower count;
its leader-loss path still removes charm and eventually calls `Reset_Controlled`
to restore the immutable monster `StartingScript` and hostile owner.

That stock follower path does not synchronize movement speed. It only selects
destinations near the leader. The closest stock speed lifecycle is
`Speed_Monster_Begin` / `Speed_Monster_End`: it adjusts
`ATTRIB_MovementRateModifier` negatively to accelerate a unit and restores the
same positive value when the effect ends. The Manager's generic controlled-
follower speed-sync feature bounds the existing stock Speed ratings to 1–5,
then composes one `-100` movement-rate step for each positive leader/follower
tier difference immediately after stock `Control_Monster` ownership transfer.
Four independent generated markers allow the exact applied steps to be removed
immediately before either stock cleanup exit. The Zoo's pure eligibility
callback recognizes only its existing `Rent_Beast` visit targeting a building
whose `RevenueScript` is `Restore_Zoo_Revenue`. The callback uses the visit's
stock-owned `Leader.Target` Zoo directly; that target is already revalidated by
the purchase callback and persists across the hidden building handoff.

Original `Control_Monster.gpl` assigns `Target.Enemytype = "Monster"` before
transferring player ownership. `GPLMx/TaskModules/Subtasks/mx_Control_Monster.gpl`
omits that line even though the shared `monster_eval_enemies` scans every unit
of `EnemyType` without `NotMyTeam`. A paused-save trace captured a rented Harpy
with `Enemytype = hero` and a player-owned Priestess Skeleton as its reciprocal
combat target. Zoo rental restores the original assignment immediately after
the selected ruleset's `Control_Monster` call, preserving original behavior and
repairing the expansion omission without changing ordinary Cultist control.

`Controlled_Monster` delegates acquisition to `monster_eval_enemies`, which
passes the controlled unit's unmodified `ATTRIB_SightRange` to
`list_enemies_seen`; neither the leader's sight nor the 300-unit follow
destination is used as the scan radius. The paused ZooTrace save made the
missing support handoff explicit: Werewolf agent 96 was correctly
`Hero / Controlled`, owned Ranger agent 27 as its leader, and ran
`Controlled_Monster` in all three task slots, but had no target while its leader
was fighting. Stock character descriptions give a Harpy 175 sight, a Troll 180,
and a Ranger 260. Expansion Palace combat guards use sight 250. The rental
handoff therefore applies the same stock 250 minimum already used for a tamed
Guardian. `Monster_follow` multiplies that sight by the shipped pursuit modifier
2, producing a 500-unit leader-target handoff while preserving stronger native
values. Stock attack, leader-loss cleanup, and death paths remain unchanged.

Stock Ranger travel exposes one target shape that `Monster_follow` was never
designed to receive from an ordinary Cultist leader. `Journey_Offmap` sets
`ThisAgent.Target = ThisAgent` while traveling to the farthest map edge. Once
there, `hide_off_map` changes the Ranger to `Hidden` without a building
container until `Return_To_Map` runs. `Monster_follow` checks only that the
leader's target is valid, so it copies the Ranger self-target to the rented
monster and directly starts `monster_attack_object` against its own leader.

A focused autosave trace recorded the resulting reciprocal feud: rented Troll
agent 19 targeted Ranger agent 27 and its `Hostiles` list contained 27; Ranger
27 targeted 19 and its `Hostiles` list contained 19. The post-fight ZooTrace
no longer contained the Troll. Rental therefore keeps enemy targets on literal
stock `Monster_follow`, routes same-team targets through stock
`wander_near_leader`, and waits when a hidden leader has no real building
container. It also subtracts only the paired renter/rental entries from their
respective `Hostiles` lists and resets the renter only if its exact current
target is the rental. This is a narrow compatibility seam for stock Ranger
off-map state; it does not scan for targets or alter unrelated hostiles.

The stored monster's previous breakout task is already running, whereas a
stock Mausoleum occupant's task was killed at interment. A focused paused-save
trace exposed the difference: the rented Troll was `Hidden`, its
`ActiveScript` was stock `fake_wander`, its counter remained zero, and the
serialized active task still had the Zoo's 60,000 ms breakout interval. Stock
`Control_Monster` normally redirects a live monster's existing task and does
not create a new one. Stock timed-building callbacks likewise set the current
task interval before replacing `ActiveScript`. Rental now preserves that
running occupant task, resets it to `Normal_Cycle`, and then calls
`Control_Monster`; it does not kill and recreate the same task slot.

## Executable profiles

The private `ZC01`/`ZCF0` dispatcher is traced independently in both maintained
Steam executables: default Public `1.5.2.24` (PE timestamp `0x5897B72F`) and
beta2 Multiplayer Support `1.5.2.28` (`0x5A8A11D5`). The beta2 map follows the
same stock lifecycle but does not use a blanket address delta: the Palace
command handler, dialog factory, AP41 controller, flag-mode registry,
validation/callback path, display classifier, attached-relation lookup, system
alert path, globals, and vtable slots each use their separately matched beta2
location. Install and restore share one profile table, validate profile-specific
stock byte guards before mutation, and reject unknown timestamps.

`tests/Test-ZooRewardDispatcherProfiles.ps1` copies both real executable
fixtures, installs the private sections and redirects, restores the stock
routes, and requires the final SHA-256 to equal the original fixture. This also
checks that unrelated executable patches survive the round trip.

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
