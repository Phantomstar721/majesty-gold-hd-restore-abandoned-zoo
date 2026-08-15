# Visitor storage stock trace

## Panel control

The ordinary building Visitors button is the stock Blacksmith `SMNU/AP02`
control, not the Mausoleum's `LIST OF DEAD` control. It dispatches command
`0x1F55` into Majesty's existing visitor-window lifecycle and reads the
building's existing occupant list. The same control has already been proven on
the Alchemist Laboratory with heroes added by stock `Enter_Building`.

The abandoned Zoo `SMNU/MX09` resource already contains `VISITORS`, its tooltip,
the same rectangle and command, and a byte-for-byte AP02 prefix. Its record is
0x88 bytes instead of AP02's complete 0x98 bytes. This restoration substitutes
only the complete AP02 record; it does not add an interface controller or new
visitor data source.

## What is hero-specific

The Mausoleum's `Check_Mausoleum` and resurrection lifecycle is specifically
for heroes. It excludes certain hero titles, cancels guild membership, marks
the occupant Dead, calculates cost from hero level, restores StartingScript
and Original_Type, and searches for a new hero guild on resurrection. That
lifecycle is not a suitable monster-storage clone.

The Mausoleum's use of the building `Occupants` list is not hero-specific.
`Building.Occupants` is a generic list of agents. Stock `enter_building` accepts
an agent and building without checking Type or SubType, appends the agent once,
and stock `exit_building` removes it. Generic `release_occupants` likewise
iterates agents and branches only on validity and death.

## Required future monster handoff

The closest stock storage lifecycle for a delivered monster is therefore the
generic building path, not Mausoleum resurrection:

1. let the current stock `Hide` trip finish;
2. keep the valid hidden monster agent instead of deleting it;
3. append it once to `zoo.Occupants`, matching `enter_building`;
4. stop or replace the delivered Hooligan active ownership so it cannot run
   arrival repeatedly;
5. define Zoo-destruction behavior using stock `release_occupants` semantics;
6. remove the agent from `Occupants` before any later deletion or release.

There is no GPL Hero filter in the generic occupant list or Visitors control.
However, the stock shipped scenarios do not place Monster/Hooligan agents in
the ordinary Visitors window, so portrait/list rendering for a stored monster
still requires a live test before capture delivery is changed.

At this milestone the Visitors control exists, but the Zoo occupant list stays
empty because delivery still resets the paired hero and deletes the Hooligan.
