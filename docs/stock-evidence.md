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
description, placement wiring, or UI control. It is therefore deliberately not
added to the stock bytecode used by this milestone.

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
