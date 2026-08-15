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

That module does not provide the missing player-facing dispatcher, flag unit
description, placement wiring, or UI control. The current milestone does not
attempt to restore its death interception or charm lifecycle. An ordinary
Attack Flag is used solely as an immediate trigger for an isolated stock
Hooligan test, enabled by the standard stock completed-building query for a
player-owned Zoo.

The Reward Flag binding probe proved the mod's `attack_flag_birth` override was
active. The rollback restores the exact gate that had already passed live
testing: `$ListObjects` from the flag, type `Building`, followed by
`#MyPlayer`, title `Zoo`, and `FirstStageBuilt == 1` in stock Mausoleum order.

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
exact owner on every delivery before the stock Hooligan deletion step.

The attempted visitor registration and `Occupants` capacity remain removed.
The generic Visitors-menu control is now restored independently: MX09 already
contains the Visitors strings, rectangle, command ID `0x1F55`, and the first
0x84 bytes of AP02's stock control, but its record ends 16 bytes early. The mod
replaces only that truncated record with AP02's complete 0x98-byte control.
Capture still performs no `Occupants` write and retains delete-on-delivery.

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
