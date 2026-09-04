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

The selected captive leaves storage using the two stock Mausoleum boundaries:
`Mausoleum_Resurrect_Begin` clears engine death state, removes the occupant,
and unhides it; `Mausoleum_Resurrect_Finish` starts the newly assigned active
task in a fresh thread. Between those boundaries the Zoo calls the shipped
expansion `Control_Monster(buyer, captive)`.

That stock Cultist function increments `buyer.Num_Followers`, transfers player
ownership, creates the charm effector, records the hero in `leader`, and begins
`fake_wander`. After the stock charm delay, `Become_Controlled` installs
`Controlled_Monster`, whose existing `wander_near_leader` and
`monster_eval_enemies` behavior follows the buyer and assists in combat.
`Controlled_Monster_Death` and the stock leader-loss path own follower cleanup
and eventual hostile reversion.

No rental-specific follower timer, combat scanner, polling controller, or
per-monster table is introduced.
