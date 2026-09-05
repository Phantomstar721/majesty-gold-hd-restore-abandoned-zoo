# Stock Zoo capture and Hooligan delivery contract

The current test checkpoint deploys the abandoned expansion Zoo capture path
directly. Once its stock `Control_Monster` call succeeds, the selected monster
continues through that stock delayed-control lifecycle and enters the proven
Wizard's Curse Hooligan return and Zoo occupant-storage handoff.

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
Capture Flag on a living monster leaves its ordinary AI, allegiance, attacks,
HP, movement, and death callback unchanged. The private flag retains the
`Flag_Attack` title so the shipped
hero reward-evaluation path still sends heroes to fight the monster.

Without an available completed player Zoo, placement is rejected by the native
private gate. Non-monsters are likewise rejected during placement; the GPL
`Type == Monster` test remains a defensive callback guard. Palace Attack Flags
always retain the literal shipped validator, `attack_flag_birth`, payout, and
death lifecycle and never enter this file's capture seam.

Stock Attack placement prevents a duplicate before creation by querying the
target's attached `ARA2` relation. The private target check copies that native
relation lookup with only the private Capture description key `ZCF0`
substituted. A focused live test proved the target table is keyed by unit
description, not the separate private `ZCA2` art identifier.
The hover and completion gates both reject a monster that already carries that
relation, so no second Capture Flag is created and no additional gold is spent.

While placing the private flag, ZCF0 uses tactical-cursor selector 38. The
loaded `CUR1Tactical Cursor` is a literal stock clone with one appended set
1038, derived from Attack cursor set 1005 but repainted with the Zoo paw flag.
Stock selectors 5/1005 and 6/1006 remain unchanged for Palace Attack and
Explore placement.

Capture pricing uses a private unset-initialized DWORD rather than AP41's
global Palace Attack DWORD. ZC01 temporarily swaps that private value through
the stock Attack slot only while shipped AP41 activation, its later APPA
secondary refresh, or +/- handling is on the call stack, then records the
normalized/adjusted result and restores the Palace amount. Capture placement
pushes the private result. Thus both panels retain stock AP41 behavior but
changing one panel's amount does not change the other or repaint Capture with
Palace's value.

## Lethal capture attempt

The active functions copy the abandoned chance formula and `zoo_flag_check`
statement order at the lethal callback boundary:

1. compute `50 * sqrt((RewardCost / 20) / MaxHP)`, capped at 95%;
2. apply the shipped strict `(RandomNumber(100) + 1) < chance` test;
3. list living player-one Hero/Hero units globally so stock
   `Control_Monster` has a temporary controller without requiring that hero to
   be near the lethal event;
4. choose list member 1;
5. restore one third of the target's maximum HP;
6. call the selected ruleset's actual `$Control_Monster(hero, target)`;
7. set the abandoned HealingRateModifier value of 1;
8. on success, replace only the stock controlled monster's eventual
   `BackScript` with the private Hooligan-to-Zoo handoff;
9. resume the engine-paused active thread using the literal operation from the
   stock `monster_gravestone` corpse tail, now that `Control_Monster` has
   redirected it to `fake_wander`;
10. delete the Capture Flag after the attempt.

The abandoned source writes `subdue_percentage` but reads the expansion-only
`charm_percentage` field, and Original `RewardFlag` declares neither. A focused
Original-rules save confirmed that the missing-field write aborts flag Birth.
The private clone therefore evaluates the unchanged formula directly at the
lethal event instead of storing it in an unavailable field.

GPLMx `zoo_flag_check` reads the expansion-only `Monster.zoo_agent`; Original
declares no such field. At the same `monster_gravestone` boundary, the
compatibility clone calls one boolean Zoo check directly, just as GPLMx does.
That check uses stock RewardFlag enumeration and the engine-owned `TargetID`
relation to recover the still-attached private Capture Flag locally. It does
not use an agent-valued helper return at lethal damage, retain a registry, or
write borrowed state onto the monster.

The active `monster_gravestone` is the literal GPLMx Zoo gate followed by the
literal stock monster-death tail. With no matching flag or after a failed roll,
gold, `Type = Dead`, thread resume, `be_dead_2`, interval, and `basic_death`
remain in shipped order. The overlay callback is the literal abandoned
`zoo_flag_death_callback`: it only deletes the flag, because capture is invoked
manually from the monster deathscript.

## Active delivery handoff

On success the bridge preserves the complete target-protection lifecycle from
the real stock `Control_Monster`, `fake_wander`, and `Become_Controlled`:

1. stock creates the infinite `Charm_icon`, records the selected hero as
   `leader`, increments that hero's `Num_Followers`, replaces the target's
   death callback, and transfers player ownership;
2. the private bridge normalizes Original's temporary `Dead` value to GPLMx's
   corrected `Hidden` value;
3. the bridge uses stock `ResumeThread(ActiveScript)` at the lethal boundary,
   allowing the redirected `fake_wander` lifecycle to advance;
4. stock waits the shipped `Charm_Delay_Time` of 3300 ms and runs
   `Become_Controlled`;
5. the target's private BackScript then removes `Charm_icon`, releases the
   temporary follower count and leader link, changes Controlled to Hooligan,
   and activates the proven delivery lifecycle. It receives an arresting hero
   immediately only if a real Zoo slot is available; otherwise its existing
   Hooligan Basic cycle retries assignment when room opens.

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
- repeat the stock Mausoleum capacity comparison on every arrival;
- call stock `Enter_Building` only after `Hide` has completed, reset the exact
  paired owner after its reservation becomes an occupant, then stop the
  hidden Hooligan's active thread so it remains in the Zoo's `Occupants` list.

The flag-side query uses the Capture Flag's player ownership and copies stock
`Check_Mausoleum`: list completed buildings, inspect each generic `Occupants`
list, append every legal candidate during `foreach`, and select the first only
after that loop ends. No function result is returned from inside `foreach`.
The limit comes from the stock
building `Level` field and is 4 / 6 / 8 for Zoo levels 1 / 2 / 3. A captured
Hooligan keeps its selected Zoo in the ordinary Monster `Target` field, but it
consumes pending capacity only after the stock arrest handoff is real: its
`leader` is a live hero, that hero still targets the captive, and
`Arrest_Hooligan` is active or resumable. Undefeated flagged monsters and
successfully controlled but unlatched Hooligans stay unreserved; the latter
remain queued without consuming a visitor slot. Assignment repeats the same
Occupants-plus-latched comparison, so queued captives cannot overbook the Zoo.
The existing Hooligan Basic/Goto lifecycle checks also treat loss of both the
active and resumable arrest task as abandonment, triggering the same reassignment
and capacity refresh instead of leaving the native placement bit stale.

The Zoo refreshes the shipped `ATTRIB_Zoo_Legal_Target` attribute after stock
construction, through the literal Palace upgrade-completion lifecycle, and
whenever hero latches or occupants change. `building_upgraded` first invokes
the Zoo's `upgradescript`, which preserves `basic_upgrade` and schedules the
Zoo's declared `birthScript2` completion slot at `#palace_upgrade_check`.
Generic stock `Building` does not declare the Palace-only `upgradescript2`
field. Initial completion therefore follows `Fairgrounds_Birth`: it calls
`Building_Birth` to start the declared revenue thread, refreshes capacity, and
then repoints the existing function slot to a private `palace_upgrade2` clone.
Later upgrades install and schedule that clone, which preserves the unchanged
`CurrentStageBuilt` reschedule test, reads the upgraded prototype's new `Level`,
restores itself after prototype replacement, and refreshes capacity only when
the test reaches 1. As with stock Marketplace levels two and three, each
upgraded Zoo prototype also runs this private `Building_Birth` wrapper from its
`birthscript`, replacing the declared revenue thread across the prototype
transition.
The private Capture placement validator and its independent completion check
both read that capacity bit before applying their hostile-monster-only test.
If stored visitors plus real hero/captive latches fill the selected Zoo, the
Capture button refuses to arm and posts “Couldn't place reward flag, Zoo is
full” through the native stock system-alert helper. The independent completion
check repeats the same test for a capacity change after arming. No flag is
created and no gold is spent.

The native unit-display classifier reports the underlying Skeleton class as a
monster even after stock `Skeleton_Birth` turns a Priestess summon into a
player-owned `Familiar`/`Controlled` unit. The placement validator and its
independent click-completion check therefore copy stock
`GetUnitPlayerNumber`'s unit-vtable query and require `Monster_Player` after the
generic monster classification. This rejects Priestess summons,
Priestess-controlled undead, Cultist-charmed monsters, and every other
currently controlled monster without a per-title list. The GPL lethal boundary
repeats that ownership condition and explicitly rejects `Familiar`, ensuring a
target controlled after flag placement retains stock `Controlled_Monster_Death`.

Stock `Check_Mausoleum` repeats its `Occupants < limit` comparison immediately
before storing an agent. Zoo delivery now preserves that final admission
boundary as well as its earlier travel reservation. If the Zoo has filled
before a captive arrives, the arresting hero is reset and the captive returns
to the existing unlatched Hooligan queue; `Enter_Building` is not called. A
stale or interrupted reservation therefore cannot create a seventh level-2
occupant.

Stock resets all arresting heroes only when the globally last quest Hooligan
arrives. The private one-owner system instead uses the same `Reset_Tasks`
cleanup on the delivered Hooligan's `leader` after the final admission and
occupant insertion.

Stored captives now provide stock-shaped Zoo revenue and have a destruction
release lifecycle. Every 60-second revenue pulse deposits 40 gold per valid
stored occupant Threat Rank into the Zoo's coffers. Physical or spell damage retains captives
while the private Zoo lives, copying the existing Mausoleum exception in
`release_occupants`. Once stock `building_death` marks the Zoo dead, the same
function applies stock `Exit_Building`, then `Reset_Controlled` and full HP,
to every valid captive. Exit must come first: it restores the pre-hidden
Hooligan state, after which Reset_Controlled installs the final hostile monster
state. The release handoff first reschedules the captive at stock
`Normal_Cycle`, so the restored monster task runs promptly rather than retaining
the one-minute cage interval. While stored, each captive runs a private clone of stock
Guardhouse `Garrison_Scan_Or_Leave`: it obtains its container, makes the same
strict-less-than random roll, and routes success through the same hostile
release helper. The current values are one roll every 60 seconds with threshold
6, which is an effective 5% chance for the stock 1..100 roll. There
is no manual release command in this checkpoint. A saved orphan already running
the breakout task without a building container completes the same stock reset
on its next check; this repairs releases created by the former reversed order.

The generic `monster_birth` lifecycle finishes initialization with
`StartingScript = BasicScript`, which is the immutable task consumed by
`Reset_Controlled`. The shipped `war_party_Birth` exception used by Goblin
Priests omits that final statement. A captured Goblin Priest could therefore
break out as a hostile monster with null `ActiveScript`, `BasicScript`, and
`BackScript` and remain frozen. Immediately before stock `Control_Monster`, the
Zoo now performs the missing stock initialization whenever `StartingScript` is
invalid. It copies the monster's current valid `BasicScript` exactly as
`monster_birth` does; only a malformed custom monster with no valid basic task
falls back to stock `wandering`. The release helper repeats the `wandering`
fallback for captives already stored in older saves, whose native task can no
longer be recovered after all three slots were replaced by the cage task. This
is title-independent and requires no per-monster table.

Delivery clears the completed `leader` / `Special_Boolean` arrest pairing and
installs the occupant function in `BasicScript`, `BackScript`, and
`ActiveScript`. This closes a persistent-integration hole absent from stock
Hooligans, which are deleted at Palace delivery: a generic task reset could
otherwise restart `Restore_Hooligan_Basic` for a monster already registered in
the Zoo. The first occupant check uses the stock timed-building ordering—set
the current task interval first, then replace `ActiveScript`—so a new visitor
cannot make its first breakout roll at the instant of admission.

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
the Monster prototype's declared `leader` field. The active compatibility seam
uses that owner only for stock control and then clears the temporary leader
after releasing its follower count. The ordinary Hooligan Basic lifecycle asks
`Restore_Assign_Hooligan` for one available Zoo and one eligible hero. Only that
real arrest pairing consumes pending capacity. Heroes whose ActiveScript or
BackScript is already `Arrest_Hooligan` are excluded, so one hero cannot own two
captures.

The surviving Zoo's `zoo_flag_poll` defines abandonment as a living seeker
whose `Target` is no longer the flagged monster. The Zoo return applies that
same test in the Hooligan's existing active cycle while the captive remains
outside. When combat, healing, or fleeing changes the owner's target before
stock `Hide` completes, the Hooligan stops, clears
`Special_Boolean`, returns to `Restore_Hooligan_Basic`, and offers the arrest to
one different eligible hero. The previous owner remains excluded until a
replacement accepts it. Once `Hide` has completed, stock hidden-arrival
processing takes precedence over abandonment: the hero may naturally clear its
arrest state between GPL cycles without bouncing the captive back outside.
There is no new thread, watcher, timer, or controller.

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
   Re-entering placement cannot attach a second Capture Flag to that monster.
3. The flag remains attached and heroes fight the still-hostile monster
   normally. Reducing it to zero HP makes one stock capture attempt; failure
   deletes the flag and runs the monster's original death behavior.
4. Success restores one-third HP and runs the real stock 3300 ms control delay.
   The target is Hidden and transferred to the selected hero's allegiance so
   existing player-minion attacks terminate.
5. When stock control finishes, the temporary controller is released. If the
   Zoo has a free real slot, one eligible hero receives the stock arrest intent,
   target, counter, and `Arrest_Hooligan` ActiveScript; every other hero retains
   normal behavior. If the Zoo is full, the unlatched Hooligan remains queued
   in the same Basic lifecycle until room opens.
6. The literal Hooligan Basic clone sees the targeting hero and switches itself
   to the literal Zoo-arrival clone. The Hooligan pauses if it gets more than
   50 units ahead of that hero.
7. The Hooligan enters its selected Zoo through stock `Hide`; its active thread
   is stopped and the valid hidden agent is appended to `Zoo.Occupants`.
8. Arrival repeats the stock Mausoleum capacity check, stores the target, then
   resets the paired hero to its unchanged native BasicScript.
9. If the hero changes targets before delivery, the Hooligan becomes available
   and one different hero receives the same stock arrest handoff.
10. If an owner dies or loses the target, the captive can be reassigned.

There is no global monster-birth or monster-death override, target callback
replacement, Agrela/Phoenix resurrection, or separate movement machinery. The
private overlay callback is the stock-native bridge needed because Original
lacks the expansion Zoo hook. Successful capture restores HP before the retail
death lifecycle continues, matching
the abandoned expansion hook; using it on a quest-critical monster may suppress
that quest's expected death event. Zoo destruction-specific cleanup remains
deferred.
