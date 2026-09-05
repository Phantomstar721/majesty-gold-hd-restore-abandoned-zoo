# Hero rental stock clone

## Open/closed state

Expansion dialog `SMNU/MX22` contains two overlapping controls for the Embassy:
command `0x22AB` is shown while closed and opens the Embassy; command `0x22AC`
is shown while open and closes it. The native controller stores that state on
the selected building in `ATTRIB_EmbassyActiveFlag` and swaps the controls on
refresh. The same native order also owns Embassy recruitment, so calling it for
a Zoo would incorrectly spawn foreign heroes.

The Zoo asks the CAM Merge Manager for only that generic per-building
state/visibility lifecycle. For the narrower Zoo layout, it copies the complete
93x26 secondary-panel action from base-game `SMNU/AP10`: one clone replaces the
abandoned wide Place Reward control, while two overlapping clones occupy the
right half with private commands `0x2A31`/`0x2A32`. The RENT pair selects
`INBb` set `1004`, the stock gold-framed HEROES family. REWARD retains AP10's
set `1009` topology through private `ZCBB`, changing only its tiny glyph to the
Capture Flag. No Embassy recruit order, timer, cost, or spawn callback is
reused.

## Shopping priority and visit

Every stock expansion hero tree evaluates `Purchase_Equipment` after rest and
then evaluates `Purchase_Bazaar`. The equipment chain checks structural and
magical gear, poison, potions, rings, the level-3 Market item, and finally
`Stat_Boost_Check`. `Purchase_Bazaar` then checks each researched Magic Bazaar
item before reaching its final false return.

The generic Manager Bazaar-tail recipe appends `Restore_Zoo_Rental_Check` at
that final false boundary. The callback copies
the stock intelligence-modified building search, considers only completed
player-owned Zoos whose open-state attribute is set, and returns true only when
one contains an affordable captive. It sets the normal `Target`, `TaskName`,
and intent fields; the composed Bazaar function assigns `Use_Building` for a
successful callback just as stock shopping does. This keeps every equipment,
upgrade, and Magic Bazaar choice ahead of rental and avoids package-owned hero
decision-tree replacements.

`Use_Building` performs ordinary travel, hiding, and occupant registration,
then invokes the Zoo's `Visited_Script`. `Restore_Zoo_Visited` copies
`Upgrade_Equipment`'s visit-duration handoff. Its completion callback rechecks
that rentals are still open, the hero has no follower, an affordable captive
still exists, and the Zoo is alive before calling stock `Spend_Gold`. A final
task copies `Done_Enhancing_Equipment`'s `Exit_Building` reset.

## Purchased follower

The selected captive leaves storage through `Mausoleum_Resurrect_Begin`'s
engine-death clear, occupant removal, and unhide ordering. A Zoo captive is not
identical to an interred hero: its periodic occupant task is still running at
the 60-second breakout interval, while Mausoleum burial killed the hero's task.
Stock timed-building handoffs set the existing task interval before replacing
`ActiveScript`, and stock `Control_Monster` redirects an already-running monster
task without creating a new one. Rental therefore resets the captive's existing
task to `Normal_Cycle` immediately before calling the shipped expansion
`Control_Monster(buyer, captive)`; it neither kills nor duplicates that thread.

That stock Cultist function increments `buyer.Num_Followers`, transfers player
ownership, creates the charm effector, records the hero in `leader`, and begins
`fake_wander`. The default `Controlled_Monster` task only wanders near the
buyer and scans around the follower. The same shipped module also defines
`Monster_follow`: when the leader has a valid target within the monster's stock
pursuit range, it copies that exact target into `monster_attack_object`; when
the target is farther away, it closes on the leader; otherwise it resumes the
ordinary near-leader wander.

Rental preserves the stock charm delay and changes only the eventual
`BackScript` selected by `Become_Controlled`. A private one-function seam keeps
`Controlled_Monster`'s stock `leader_dead` cleanup gate, then dispatches to
stock `Monster_follow`. `Controlled_Monster_Death` remains the death callback,
so follower counts, charm cleanup, speed cleanup, and hostile reversion retain
their existing owners.

Original Majesty's `Control_Monster` also sets `Enemytype = Monster`; GPLMx
omits that one assignment while retaining `monster_eval_enemies`, whose
EnemyType query has no team filter. A paused-save trace showed the consequence:
a rented Harpy retained its native `Enemytype = hero` and selected a
player-owned Priestess Skeleton as its target. The private rental handoff
restores the original stock assignment immediately after `Control_Monster`, so
both rulesets use the intended controlled-monster target class.

The stock `Monster_follow` pursuit test is follower sight multiplied by
`#Mon_Atck_Obj_Pursuit_Range_Mod` (2). Stock Harpies and Trolls have only 175
and 180 sight while a Ranger has 260, so rentals retain the expansion Palace
guard's 250-point minimum already used by Tame Beast. The effective support
handoff therefore reaches a buyer target within 500 units while preserving any
stronger native sight value. No target scanner, timer, or attack task is
invented.

A focused paused-save trace caught the failure mode directly: the rented Troll
was still `Hidden`, its `ActiveScript` was `fake_wander`, its counter was zero,
and that active task still serialized the 60,000 ms Zoo breakout interval. The
normal-cycle handoff above prevents the stock 3.3-second charm transition from
being stretched across many one-minute ticks.

## Rental follower movement

Stock `Control_Monster` does not synchronize a controlled monster's movement
with its leader. It only calls `wander_near_leader`, which chooses destinations
within 300 units of that leader. Stock `Speed_Monster` proves the actual speed
operation: a negative `ATTRIB_MovementRateModifier` adjustment makes a unit
move faster and the positive inverse removes that exact adjustment.

The package therefore declares the Manager's generic
`stock.controlled-follower-speed-sync.v1` lifecycle with a `-100` adjustment
per missing Speed tier. Its eligibility callback accepts only the moment when
the `Rent_Beast` buyer still targets the private Zoo and the new follower names
that buyer as its leader. The stock visit target owns that transaction across
Enter_Building, payment, and the hidden-unit control handoff; the callback
therefore consumes that target directly rather than rediscovering it through
the buyer's transient container state. The Manager bounds both stock Speed
values to 1–5, applies and privately marks one movement-rate step for
each positive `Leader - Follower` tier after stock `Control_Monster` succeeds,
and applies no boost when the follower is already as fast or faster. Up to four
independent private markers let it remove exactly the applied `+100` steps
immediately before stock `Controlled_Monster_Death` or the stock `leader_dead`
Charm cleanup. Ordinary Cultist charms, the Zoo capture-control bridge, tame
Guardians, and hostile monsters fail the callback and remain unchanged.

No rental-specific follower timer, combat scanner, polling controller, or
per-monster table is introduced. The only private task is the cleanup-preserving
one-call seam between stock `leader_dead` and stock `Monster_follow`.
