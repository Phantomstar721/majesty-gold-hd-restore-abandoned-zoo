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

## Monster handoff under test

The implemented storage lifecycle uses the generic building visitor path, not
Mausoleum resurrection:

1. let the current stock `Hide` trip finish;
2. keep the valid hidden monster agent instead of deleting it;
3. repeat stock `Check_Mausoleum`'s final `Occupants < limit` admission test;
4. call stock `Enter_Building` now that delivery is complete; it adds the
   captive once to `zoo.Occupants` and plays the normal entry effect;
5. reset the paired arresting hero after the reservation has become an
   occupant;
6. call stock `SpecifyIntent`, in the same post-entry position used by stock
   `Lived_In`, so the row displays “is waiting in the zoo”;
7. kill the hidden Hooligan's active thread so it remains stored.

There is no GPL Hero filter in the generic occupant list or Visitors control.
Live inspection proved that the controller receives every delivered monster,
creates a selectable row with the correct agent ID, and opens the correct
monster primary panel. Monster rows contain correct parsed titles such as
`Harpy`, `Giant Rat`, `Troll`, and `Werewolf`.

The blank display was native category filtering, not missing row data. During
painting, visitor controller code at `0x004985C0` calls stock classifier
`0x00508510`. Category 1 enters the complete hero row renderer, category 2
enters its alternate renderer, and all other categories jump to cleanup at
`0x00498A91` without drawing. The generic QOL patch changes only that final
branch so otherwise-valid occupants enter the existing category-1 renderer at
`0x004986A5`. Live Zoo testing displays monster level, name, current action,
and HP. No Zoo-specific or per-monster display code is required.

Hero icons normally come from a direct `Interface-02` image on the unit record.
Stock monsters instead use the `IX92`/`IX94` interface atlases and resolver at
`0x004BB0A0`. Because Original-rules quests do not load those expansion
resources, the Zoo's interface CAM carries the two literal stock IMAG records
and their complete positional TILE table. Live Deal with a Demon testing then
displayed the correct Harpy and Troll icons through that resolver. The generic
patch contains no monster-type or Zoo-specific icon table.

Admission now follows stock `Check_Mausoleum`: it compares the Zoo's generic
`Occupants` list plus captives genuinely latched to live arresting heroes with
a limit. Flags and successfully subdued but unlatched Hooligans do not consume
capacity; the latter retry assignment through their existing Basic cycle when
room opens. The requested
limits are 4 / 6 / 8 at Zoo levels 1 / 2 / 3. The selected Zoo exposes whether
that comparison has room through the stock Zoo legality attribute, allowing
the private Capture gate to reject placement before a flag exists and post its
full-Zoo message through the native stock system-alert path.
Zoo revenue now copies stock `Fairgrounds_Revenue` ownership and timing: a
declared `RevenueScript` runs every 60,000 ms, reads the building-owned
participant list, and gives the computed gold to the building so ordinary Tax
Collectors remain authoritative. The Zoo substitutes `Occupants` for
Fairgrounds `combatants` and weights each valid stored occupant by its generic stock
`ATTRIB_LevelXP` Threat Rank. The current invented balance is 40 gold per rank
per pulse; an empty Zoo earns nothing.

Initial completion calls stock `Building_Birth` unconditionally, matching
`Fairgrounds_Birth`, so the declared revenue thread is actually launched.
Like upgraded stock Marketplaces, the level-two and level-three Zoo prototypes
also run `Building_Birth` from their upgrade `birthscript`; this replaces the
revenue thread after `UpgradeAgentAttributes` installs the new prototype.

Ordinary physical and spell attacks call stock `release_occupants` as soon as
a building is struck. Northern Expansion's function already exempts a living
Mausoleum and reaches the same function after `building_death` marks it dead.
The Zoo extends that exact branch shape and uses its private `RevenueScript`
function as stable identity: a living private Zoo does nothing;
when stock `building_death` calls again after setting `Type = Dead`, each valid
captive leaves through stock `Exit_Building`, then runs the shipped
`Reset_Controlled` charm-expiry lifecycle and is healed to `MaxHP`. Delivery assigns a private
clone of the shipped Guardhouse `Garrison_Scan_Or_Leave` occupant task instead
of killing or suspending the captive task thread. That task obtains the Zoo
through `GetBuildingContainer`, makes the stock-shaped random roll, and uses
the same hostile release helper after a successful breakout roll. Other
buildings and the Mausoleum retain the shipped branches. A manual release
command remains absent.
