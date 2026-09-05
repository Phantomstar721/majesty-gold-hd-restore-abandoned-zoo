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
- `ActiveScript`, `BackScript`, and `BasicScript` to the Zoo's narrow
  patrol-entry wrapper, which delegates immediately to stock `Guardian`.

Stock `Guardian` wanders around `coord_home`, evaluates enemies with the normal
monster combat helpers, pursues a target only within its guardian radius, and
returns home afterward. Tame Beast copies this state literally and uses the
player's Palace as `coord_home`, making the creature a kingdom-core guardian
instead of tethering it to the Zoo grounds. The Zoo is used only if no valid
Palace exists. It preserves player ownership and the existing charm effector,
restores full health, and starts the stock-delegating patrol at `#Normal_Cycle`.

The quest Varg overrides `Guardian_Mod` to `2`, but that special leash proved
too small when applied to arbitrary Zoo monsters. Expansion Monster Data uses
`Guardian_Mod = 5` for nearly every ordinary monster, including the Varg's
native White Wolf prototype, so the tame role uses that generic stock value.
`Guardian` acquires enemies using unmodified `SightRange`, not `Guardian_Mod`.
The expansion also spawns Palace guards with sight 250; Tame Beast applies that
stock combat-guard value as a minimum while preserving monsters with stronger
native sight. The movement, target selection, pursuit, casting, and return-home
logic remain stock `Guardian`.

A paused `ZooTrace.GMP` exposed one stock lifecycle gap after a tamed Vampire
had pursued a Daemonwood. Vampire agent 719 retained Daemonwood agent 957 as
its valid `Target`, while `ActiveScript`, `BackScript`, and `BasicScript` had
all returned to `Guardian` and `Hostiles` was empty. Stock
`Guardian_Attack_Object` returns to `BasicScript` when a target crosses the
home leash but leaves `Target` intact. On later patrol ticks,
`Guardian_Eval_Enemies` changes to its attack task only when the closest enemy
differs from the stored target, so the same enemy can remain selected without
combat resuming.

Stock `Returning_Guardian_Attack_Object` clears `Target` at its equivalent
return-home boundary. The Zoo applies that exact cleanup intent through a
single private patrol-entry wrapper: whenever a tame re-enters its basic
patrol, the wrapper clears the stale target once and calls stock `Guardian`.
It does not scan, choose a target, replace combat, alter Hostiles, add a timer,
or create another task.

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
of the monster's stock `ATTRIB_LevelXP` combat bounty. This is the
player-facing permanent-guardian price; hero rental uses its own lower curve.
