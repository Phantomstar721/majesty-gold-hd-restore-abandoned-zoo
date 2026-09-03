# Tame Beast stock clone

## Interface lifecycle

The expansion Mausoleum is the stock model for selecting one agent from a
building-owned `Occupants` list and purchasing an action for that agent.

- `SMNU/MX04` opens `SMNU/MX05` from its `LIST OF DEAD` control.
- `MX05` binds list control `0x1388` to the parent building's occupants.
- Selecting a row refreshes the selected-agent cost field `0x1F46`.
- Action control `0x138B` checks/deducts the displayed gold cost and dispatches
  `Mausoleum_Resurrect_Begin` for the selected agent.
- The GPL callback obtains the containing building, removes the selected agent
  from `Occupants`, unhides it, and begins the stock resurrection lifecycle.

The private Zoo panel retains that ordering and substitutes only private
resource/command identities, Zoo text, the cost callback, and the selected
occupant action callback. The CAM Merge Manager owns the generic executable
dispatch needed to keep those substitutions data-driven and merge-safe.

## Released-beast lifecycle

The controlled Varg setup in expansion `Epic_Quest_Scripts.gpl` is the closest
stock match for a friendly monster that independently guards an area. It sets:

- `Type = Hero` and `SubType = Controlled`;
- `EnemyType = Monster`;
- `Guardian_Mod = 2`;
- `ActiveScript`, `BackScript`, and `BasicScript` to stock `Guardian`.

Stock `Guardian` wanders around `coord_home`, evaluates enemies with the normal
monster combat helpers, pursues a target only within its guardian radius, and
returns home afterward. Tame Beast copies this state literally and uses the
player's Palace as `coord_home`, making the creature a kingdom-core guardian
instead of tethering it to the Zoo grounds. The Zoo is used only if no valid
Palace exists. It preserves player ownership and the existing charm effector,
restores full health, and starts `Guardian` at `#Normal_Cycle`.

The private child dialog retains MX05's own list/action backing and chrome.
Only its resource identity and text are private. Reusing the Capture rewards
backing here is invalid because that set paints its amount field and plus/minus
buttons underneath MX05's visitor rows.

This avoids a custom patrol timer, watcher, target scanner, or combat state
machine. The monster's original `StartingScript` remains intact for the stock
uncontrolled/reset path.

## Invented balance

Majesty contains no surviving Zoo taming-price table. The first playable curve
is linear: `500 * Threat Rank`, producing costs from 500 gold at rank 1 through
4000 gold at rank 8. Threat Rank itself is the existing display-only grouping
of the monster's stock `ATTRIB_LevelXP` combat bounty.
