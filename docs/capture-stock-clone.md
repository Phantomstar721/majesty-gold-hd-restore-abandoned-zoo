# Stock Hooligan diagnostic contract

This milestone deliberately removes the attempted Zoo capture implementation.
It exists only to prove that an ordinary living monster can be handed to the
complete shipped Wizard's Curse Hooligan lifecycle.

## Trigger

The trigger uses the literal completed-building query previously proven in
game: from the Reward Flag, list `Building` agents with arguments ordered
`#MyPlayer`, `#CheckTitles`, `Zoo`, `#ATTRIB_FirstStageBuilt`, `1`.
Construction sites therefore do not enable the trigger; any completed Zoo
level does. The first completed Zoo becomes the destination.

The private ZCF0 placement validator first runs the complete stock Attack Flag
validator. It then permits only the intersection of the shipped gameplay
display-classifier category `4` and the shipped structural unit-description
subtype `Character`. A focused live trace returned category `4` and structural
subtype `3` for an ordinary monster. This generic stock intersection rejects
heroes/mercenaries, henchmen, buildings/lairs, flags, projectiles, and effects
before a flag can be created without hardcoding monster prototypes.

The shipped completion callback repeats target acquisition separately from its
hover validator. The private relocated callback preserves that ordering: its
target-acquisition call first runs the complete stock check, then returns the
selected pointer only for the same monster intersection. A rejected target
therefore never reaches stock reward deduction or flag creation.

With that placement test and the Zoo gate satisfied, placing the Zoo's private
Capture Flag on a living agent whose current `Type` is `Monster` begins the stock controlled-monster
transition described below. The private flag remains attached to that target
under its cloned stock `attack_flag_poll` and `attack_flag_death` lifecycle.
The trigger does not wait for combat, roll capture chance, or intercept death.

Without a completed player Zoo, a Capture Flag placed on an otherwise eligible
monster retains its cloned stock Attack Flag lifecycle. Non-monsters are
rejected during placement; the GPL `Type == Monster` test remains as a
defensive conversion guard. Palace Attack Flags always retain the literal
shipped validator and `attack_flag_birth` lifecycle and never enter this file's
conversion seam.

While placing the private flag, ZCF0 uses tactical-cursor selector 32. The
loaded `CUR1Tactical Cursor` is a literal stock clone with one appended set
1032, derived from Attack cursor set 1005 but repainted with the Zoo paw flag.
Stock selectors 5/1005 and 6/1006 remain unchanged for Palace Attack and
Explore placement.

## Monster handoff

The bridge copies the complete target-protection lifecycle from stock
`Control_Monster`, `fake_wander`, and `Become_Controlled` before activating the
Hooligan behavior:

1. stop the target and clear its Hostiles;
2. make its active script the private stock `fake_wander` clone;
3. temporarily set `Type` to `Hidden` so attackers treat the target as invalid;
4. transfer the target to the Capture Flag's player with
   `SetUnitPlayerNumber`, matching stock control/charm;
5. wait the shipped `Charm_Delay_Time` of 3300 ms;
6. change `Type` to `Hooligan`, clear Hostiles again, and activate the proven
   Hooligan arrest lifecycle.

Player-controlled minions use `list_enemies_seen`, which lists only Hero and
Monster agents on `NotMyTeam`. The temporary Hidden state cancels an attack
already underway; the ownership transfer and final Hooligan type prevent the
same minion from reacquiring the captive afterward.

The final handoff applies the stock Hooligan data values that behavior depends
on and assigns:

- private literal `Restore_Hooligan_Basic` to Starting, Basic, Active, and Back
  scripts;
- `Hooligan_Death` to its engine death callback;
- `Type` and `SubType` `Hooligan`;
- `EnemyType hero`, `basic_idle`, `do_nothing`, Guardian modifier 3, current
  location as `coord_home`, `Special_Boolean FALSE`, the stock Hooligan
  non-flaggable/non-spell-target attributes, and the Henchman cycle interval.

No task thread is killed or created during conversion. The target's existing
active thread owns the same counter-based delayed transition as stock
charm/control; completion switches that thread to the literal Hooligan clone.

## Destination substitution

`Restore_Hooligan_Basic` preserves shipped `Hooligan_Basic` statement order,
radius query, Player 1 restriction, target check, message, and
`Special_Boolean` handoff. Its only functional change is assigning
`Restore_Hooligan_Goto_Zoo` instead of `Hooligan_Goto_Palace`.

`Restore_Hooligan_Goto_Zoo` preserves the shipped destination and arrival
shape, with the adaptations required by private single-owner arrests:

- use the first completed player Zoo admitted by the stock Mausoleum-shaped
  occupancy check;
- call `Hide` only while the Hooligan is not moving and its assigned hero is
  within the stock arrest distance;
- stop the Hooligan when it gets farther than that distance from its owner;
- after it becomes hidden, check whether this was the last Hooligan;
- emit the stock completion message and set quest flag 2 for the last one;
- reset the exact paired owner on every arrival;
- call stock `Enter_Building` only after `Hide` has completed, then stop the
  hidden Hooligan's active thread so it remains in the Zoo's `Occupants` list.

The flag-side query uses the Capture Flag's player ownership and copies stock
`Check_Mausoleum`: list completed buildings, inspect each generic `Occupants`
list, and take the first one below its limit. The limit comes from the stock
building `Level` field and is 4 / 6 / 8 for Zoo levels 1 / 2 / 3. Because Zoo
delivery is delayed while Mausoleum interment is immediate, an admitted
Hooligan keeps its selected Zoo in the ordinary Monster `Target` field. That
reservation is counted until `Enter_Building` creates the occupant entry, then
cleared. This prevents simultaneous escorts from overbooking a Zoo without a
new thread, timer, building counter, or per-monster definition.

The Zoo refreshes the shipped `ATTRIB_Zoo_Legal_Target` attribute after stock
construction, through the stock `building_upgraded` -> `upgradescript` seam,
and whenever reservations or occupants change.
The private Capture placement validator and its independent completion check
both read that capacity bit before applying their existing monster-only test.
If the selected Zoo is full or fully reserved, clicking a Monster is rejected
by exactly the same private gate that rejects a Hero or building; no flag is
created and no gold is spent.
Stock resets all arresting heroes only when the globally last quest Hooligan
arrives. The private one-owner system instead uses the same `Reset_Tasks`
cleanup on the delivered Hooligan's `leader` before storing the target.

There is no visitor income, breakout, or Zoo-destruction-specific cleanup in
this storage test.

## Hero handoff

Wizard's Curse installs the quest-wide `Be_Dumb` wrapper during `hero_birth`.
That wrapper calls `Hooligan_Check`; on success the two functions together set
the arrest intent, target, Counter 0, and ActiveScript `Arrest_Hooligan`.

This mod must not install the rest of the quest-wide curse merely to reach that
successful branch. `Restore_Assign_Hooligan` therefore applies those four
stock statements directly to one already-living hero. It does not replace the
hero's StartingScript, BasicScript, BackScript, or QuestScript. On delivery,
the stock arrival reset returns the hero directly to its unchanged native
BasicScript; if the target disappears first, stock `Arrest_Hooligan` performs
the same invalid-target reset itself.

## Single-hero ownership

Stock `Hooligan_Check` calls `Is_Free_Task`. Stock sets
`#is_free_task_max_heroes` to 2, uses an inclusive `<=` comparison, and permits
a closer hero to accept a target already owned by a farther hero. Multiple
heroes escorting one Hooligan is therefore expected stock behavior.

The abandoned Zoo already provides a literal single-owner mechanism. It builds
`valid_heroes`, chooses `$ListMember(valid_heroes, 1)`, and passes only that
hero to `Control_Monster`; stock `Control_Monster` records the relationship in
the Monster prototype's declared `leader` field. The conversion copies that
selection and leader link, and directly gives only that hero the stock arrest
handoff. Heroes whose ActiveScript or BackScript is already `Arrest_Hooligan`
are excluded, so one hero cannot own two captures.

The surviving Zoo's `zoo_flag_poll` defines abandonment as a living seeker
whose `Target` is no longer the flagged monster. The Zoo return applies that
same test in the Hooligan's existing active cycle. When combat, healing, or
fleeing changes the owner's target, the Hooligan stops, clears
`Special_Boolean`, returns to `Restore_Hooligan_Basic`, and offers the arrest to
one different eligible hero. The previous owner remains excluded until a
replacement accepts it. There is no new thread, watcher, timer, or controller.

## Escort pacing

Stock `Hooligan_Goto_Palace` calls `Hide` on the Hooligan, so the captive moves
independently; stock `Arrest_Hooligan` makes the hero chase it but contains no
speed synchronization. A converted monster also retains its original movement
attachment. `ATTRIB_Speed` is used by GPL threat/escape evaluation and changing
it does not replace that attachment's actual movement timing; the prior
speed-rating copy was therefore removed.

Stock monster formations manage differing movement profiles by testing the
distance to a linked leader and changing movement state. The Zoo return uses
that formation pattern inside its existing Hooligan active cycle: while its
assigned hero is alive, the Hooligan stops whenever their separation exceeds
the shipped `#Arrest_Hooligan_Dist` of 50 and resumes the same stock `Hide`
trip after the hero catches up. This adds no thread or independent watcher and
does not guess per-species movement-rate modifiers.

## Expected stock result

1. Place a Palace Attack Flag on a monster. It remains an ordinary stock bounty
   whether or not the player owns a Zoo.
2. Complete any level of Zoo, open its Capture panel, then place a Capture Flag
   on a living monster.
3. The flag remains attached and visible under the stock Attack Flag overlay
   lifecycle; conversion itself pays no bounty. For the stock 3300 ms control
   delay, the target is Hidden and transferred to the player's allegiance so
   existing player-minion attacks terminate.
4. After that delay, one selected hero receives the stock arrest intent, target, counter, and
   `Arrest_Hooligan` ActiveScript; every other hero retains normal behavior.
   The Hooligan pauses if it gets more than 50 units ahead of that hero.
5. The literal Hooligan Basic clone sees the targeting hero and switches itself
   to the literal Zoo-arrival clone.
6. The Hooligan enters its selected Zoo through stock `Hide`; its active thread
   is stopped and the valid hidden agent is appended to `Zoo.Occupants`.
7. Arrival resets the paired hero to its unchanged native BasicScript before
   storing the target.
8. If the hero changes targets before delivery, the Hooligan becomes available
   and one different hero receives the same stock arrest handoff.
9. If an owner dies or loses the target, the captive can be reassigned.

Monster birth, monster death, Zoo destruction-specific cleanup,
Agrela/Phoenix resurrection, and separate movement machinery are absent. The
Zoo substitutes the Palace destination, adds a stock formation-style escort-
distance gate, privatizes stock arrival cleanup to the paired owner, and uses
the stock Mausoleum storage tail to retain the hidden occupant.
