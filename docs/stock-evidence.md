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

## Private Capture Flag placement clone

`Fl00` is the stock Attack Flag placement-mode token, not the flag's unit ID.
The AP41 handler sends that token and the current reward to `0x00454E70`. The
engine registers `Fl00` during its normal placement-mode initialization with
the stock validation callback at `0x0045D360` and completion callback at
`0x0045D400`. The completion callback eventually passes the literal prototype
name `Flag_Attack` to the stock creation path at `0x0045CC90`.

The private clone preserves both halves of that lifecycle. At the same stock
registration boundary, it appends mode `ZCF0` with the same parameters and
validation callback plus a relocated byte-for-byte completion callback. The
sole callback substitution is its prototype-name pointer:
`Flag_Attack` becomes `Restore_Capture_Flag`. Target validation, mouse state,
gold checks, successful placement, cancellation, and panel return remain in
stock order.

Only the private ZC01 AP41 object receives a cloned primary vtable whose command
handler substitutes `ZCF0` for `Fl00` on Capture placement and on the two live
reward-adjustment paths. All unmodified commands tail-call the stock AP41
handler. Palace AP41 retains its stock vtable and all three literal `Fl00`
paths, so Palace Attack Flags are isolated from Zoo capture.

`Restore_Capture_Flag` clones the stock overlay description and GPL
`Flag_Attack` prototype. It retains shipped `ARA2` art, `AP46` panel,
`Attack_flag_death_callback`, `RewardFlag` type, internal `Flag_Attack` title,
`attack_flag_poll`, and `attack_flag_death`. Keeping the internal title is
required because shipped hero reward evaluation recognizes attack work by
testing `flag.title == "flag_attack"`. Only the prototype identity and birth
function are private. Stock `attack_flag_birth` is no longer overridden.

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
description, private placement wiring, or completed UI control. The current
milestone does not attempt to restore its death interception or charm
lifecycle. The private Capture Flag instead supplies the isolated stock
Hooligan test, enabled by the standard completed-building query for a
player-owned Zoo.

The earlier Reward Flag binding probe proved the conversion seam when it was
temporarily attached to `attack_flag_birth`. The private
`Restore_Capture_Flag_Birth` now carries the exact gate that passed live
testing: `$ListObjects` from the flag, type `Building`, followed by
`#MyPlayer`, title `Zoo`, and `FirstStageBuilt == 1` in stock Mausoleum order.
The shipped `attack_flag_birth` binding is no longer replaced.

`mx_Monster_Births.gpl` and `mx_Monster_Deaths.gpl` are not overridden in this
milestone. Monster spawning and all ordinary lethal events therefore remain
owned by the selected stock ruleset.

The surviving `Set_Subdue_Chance` contains a definite field-name mismatch: it
writes `subdue_percentage`, while `zoo_flag_check` reads
`charm_percentage` and `mx_prototype.gpl` declares only the latter on
`RewardFlag`. That probability path is not active in this milestone.

The abandoned success branch sets HP without complete engine-death and task
ownership. Earlier experiments around that gap have been removed. This
milestone transforms only a still-living agent and contains no resurrection or
death-state manipulation.

`TaskModules/Subtasks/mx_Control_Monster.gpl` supplies the stock protection
lifecycle for a living creature changing sides. `Control_Monster` comments that
its temporary setup exists so other units stop attacking the target, assigns
`Type = Hidden`, transfers the target to the controller's player, and leaves
the target's existing active thread running `fake_wander`. After the shipped
3300 ms `Charm_Delay_Time`, `Become_Controlled` exposes the allied Hero type and
clears the target and Hostiles. The Zoo bridge copies that sequence, changing
only the final exposed type and script from Controlled to Hooligan arrest.

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
exact owner on every delivery before the occupant-storage step.

The prior invented `Occupants` capacity remains removed. The generic
Visitors-menu control is restored independently: MX09 already
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
