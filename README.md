# Majesty Gold HD: Restore Abandoned Zoo

Restores the abandoned three-level Zoo using the artwork, dialog layout, and
GPL building lifecycle left in *Majesty Gold HD*.

The current local-test milestone restores the building, the abandoned stock
Zoo capture attempt, and the proven Wizard's Curse Hooligan delivery lifecycle:

- the Zoo appears in the stock service-building construction menu;
- it carries private `Restore_Zoo1`–`Restore_Zoo3` clones of the stock Zoo GPL
  prototypes and upgrades through stock art levels `ABn1`–`ABn3`;
- it packages literal copies of the three stock Zoo IMAG records with their
  position-preserving MX TILE and palette tables, so Original rules can create
  the construction placement ghost;
- it uses the literal stock `MX09` building controller and corrects its obvious
  Blacksmith placeholder prose;
- its surviving **Place Reward** control now opens a private `ZC01` clone of
  the stock Palace Rewards panel;
- that clone retains only the Attack placement path, labels it **Capture
  Flag**, and uses the stock 100-gold initial increment;
- Capture reward pricing has its own private channel: the Zoo panel runs the
  unchanged stock AP41 activation and secondary-refresh normalization, +/-
  button, amount-text, and placement lifecycle against that channel without
  changing Palace Attack's amount;
- only that private clone selects a Zoo-themed `ZOBG` backing, which retains
  the stock Capture controls and removes the baked-in appearance of the hidden
  Explore row without changing controller behavior;
- its Capture button selects private `ZCIC` set 1011 art, retaining the stock
  25x25 button frame while replacing the crossed-blade flag with the Zoo paw;
- its Capture control selects a private `ZCF0` placement-mode clone, whose
  completion callback creates private `Restore_Capture_Flag` reward flags;
- `ZCF0` preserves the complete stock Attack Flag placement validator, then
  accepts only Majesty's stock runtime display category `4` and stock
  `Monster_Player` ownership—the generic stock shape of a currently hostile
  monster—so Capture Flags cannot be placed on heroes, henchmen, buildings,
  effects, Priestess minions, or Cultist/other controlled monsters;
- stock Attack placement rejects a duplicate by looking for its attached
  `ARA2` description relation on the selected target; the private validator
  repeats that exact lookup for Capture description relation `ZCF0`, both while
  hovering and again at click completion, so one monster can carry at most one
  Capture Flag;
- that placement clone selects private tactical-cursor selector 38, backed by
  an appended `CUR1` set 1038 repaint of stock Attack cursor set 1005;
- the private flag retains the stock Attack Flag animation topology but selects
  private `ZCA2` Zoo art: a forest-green flag with an aged-gold paw emblem,
  four stock-shaped player-color interface variants, and private minimap art;
- it retains the stock Attack Flag panel, internal `Flag_Attack` title, and hero
  reward evaluation, while private Zoo poll/death callbacks preserve the
  abandoned capture attempt instead of paying an ordinary attack bounty;
- it uses the nearest evidenced stock configuration for missing economy and
  durability values;
- the capture trigger runs at the literal GPLMx `monster_gravestone` boundary,
  before the stock corpse transition; Original's missing `Monster.zoo_agent`
  field is replaced inside the same direct boolean Zoo check by a one-shot
  stock RewardFlag/TargetID lookup for the still-attached private Capture Flag;
- the abandoned reward formula is active: `50 * sqrt((reward / 20) / MaxHP)`,
  capped at 95%, and is evaluated directly at capture time so it works without
  GPLMx-only flag fields under Original rules;
- Palace Attack Flags now remain completely stock and cannot trigger Zoo
  capture behavior;
- success restores one-third HP and calls stock `Control_Monster`, then its
  delayed `fake_wander -> Become_Controlled` lifecycle enters the proven
  Hooligan-to-Zoo delivery/storage handoff; failure follows the rest of the
  target's saved stock or quest-specific death callback;
- shipped `Arrest_Hooligan` and `Hooligan_Death` remain unchanged; private
  Hooligan clones change the destination and enforce one arresting hero per
  Hooligan;
- each Hooligan retains shipped `Hide` travel but pauses whenever it moves more
  than the stock arrest distance ahead of its selected hero;
- the Hooligan returns to its selected Zoo and is stored as a valid hidden agent
  in the Zoo's stock `Occupants` list, with a private clone of the stock
  Guardhouse occupant task left running to govern eventual release;
- Zoo admission uses the stock Mausoleum capacity pattern, with requested
  visitor limits of 4 at level 1, 6 at level 2, and 8 at level 3; stored
  visitors and captives actually latched to a live arresting hero consume
  capacity, while flags and successfully subdued but unlatched Hooligans do
  not; delivery repeats the stock Mausoleum's immediate capacity comparison
  before storage, and a queued Hooligan retries the existing arrest assignment
  from its stock Basic lifecycle when room opens; the private Capture Flag gate refuses to arm
  once those real commitments fill the Zoo and posts “Couldn't place reward
  flag, Zoo is full” through Majesty's native system-alert path;
- delivered monsters use the stock occupant-intent field so their visitor rows
  read “is waiting in the zoo” rather than the default “is Thinking”;
- each completed Zoo runs the stock Fairgrounds revenue-thread shape once per
  minute and deposits `40 * Threat Rank` gold per valid stored occupant into its own
  coffers for ordinary Tax Collector pickup; Threat Rank reads the monster's
  stock `LevelXP` bounty through the same generic bands used by Generic Visitor
  Lists, with no per-monster table;
- the abandoned Zoo panel's truncated `Visitors` control is completed with the
  missing bytes from the stock Blacksmith control and displays delivered
  monsters from the generic occupant list;
- it loads the literal stock `IX92`/`IX94` monster-icon records with their
  complete positional interface TILE table so the generic visitor renderer can
  use Majesty's shipped monster-icon resolver in Original-rules quests;
- Deal with a Demon starts with one completed level-one Zoo as a temporary,
  deterministic test fixture;
- the mod applies only the successful stock Hooligan-check handoff to one hero,
  leaving that hero's native Basic/Starting scripts untouched so delivery can
  reset cleanly;
- if combat or fleeing changes that hero's target, the stock Zoo flag
  abandonment test releases the Hooligan and assigns one different hero;
- stock attack and spell reactions still call `release_occupants`, but the
  private Zoo is identified by its private revenue function and follows the
  shipped living-Mausoleum exception, retaining its
  captives while standing; stock `building_death` reaches the same boundary
  after marking the Zoo dead, at which point every captive is restored to full
  HP through stock `Reset_Controlled` and `Exit_Building` as a hostile monster;
- every stored captive uses the stock Guardhouse random-exit shape once per
  minute with an effective 5% breakout chance; a successful roll
  restores full HP and hostile stock behavior, while ordinary damage to a
  living Zoo still releases nobody;
- successfully capturing a quest-critical monster suppresses
  that monster's stock death callback, exactly like the abandoned expansion
  hook, and may therefore prevent a quest's expected death event.

See [stock evidence](docs/stock-evidence.md), the [capture stock-clone
contract](docs/capture-stock-clone.md), the [visitor stock trace](docs/visitor-stock-trace.md),
and the complete [invented-content ledger](docs/invented-content.md) before
changing gameplay.

## Build

Requires Python 3.9+ and a local Majesty Gold HD installation.

```powershell
python scripts/build_mod.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The ready-to-install mod is written to `dist/RestoreAbandonedZoo`. Copy that
directory into the game's `Mods` directory, or pass `--output-root` to build
somewhere else.

## Local Steam test install

Build, validate, and install into the default Steam user's local Majesty mod
directory with one command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Install-LocalMod.ps1
```

The installed package is
`Documents\My Games\MajestyHD\Mods\RestoreAbandonedZoo`. Re-running the command
replaces only that exact package and verifies every deployed file by SHA-256.
The executable dispatcher explicitly supports both maintained Steam builds:
default Public `1.5.2.24` and beta2 Multiplayer Support `1.5.2.28`. It selects
the profile from the executable's stock PE timestamp and validates the complete
profile-specific reward-panel and Attack Flag byte guards before writing. An
unknown or mismatched executable fails closed.
The same command also installs a private read/execute `.mzoo` code section and
a four-byte, non-executable read/write `.mzdt` state section. Two
guarded redirects let only `MX09` open `ZC01` and let only `ZC01` use Majesty's
literal AP41 controller constructor. A third stock-boundary redirect appends
private `ZCF0` beside the shipped flag-placement modes; ZC01 alone receives a
private vtable selecting it. Its private validator calls the full stock Fl00
validator before applying the selected Zoo's capacity bit and the stock
monster-class plus `Monster_Player` ownership intersection. The Capture button and independent placement
completion check repeat that same capacity test; a full-Zoo attempt uses the
stock literal-string alert helper and does not arm or spend gold. The stock
Palace `AP41`/`Fl00`, the existing
`CGxx` custom-guild route, and unrelated QOL patches remain untouched. Restore
only the Zoo redirects, mode registration, and private sections with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Restore-ZooRewardDispatcher.ps1
```

Enable **Restore Abandoned Zoo** in Majesty's Mods screen before starting a new
game. Workshop metadata and publishing are intentionally not part of this local
development setup.

## CAM Merge Manager status

The package is compatible with the CAM Merge Manager's schema-version-3
contract. It does not reserve a `CGxx` DialogID or require the manager to
special-case the Zoo's UUID, name, or shipped `MX09` identity. Its complete
BDEP, GPL, Descriptions, private intent strings, consolidated main/interface
art, `ZC01` Capture panel, and `ZCF0` flag-placement mode are composed through
the manager's generic semantic pipeline.

The shipped definition declares the reusable
`stock.mx09-ap41-reward-panel.v1` and
`stock.ap41-fl00-hostile-monster-flag.v1` recipes. Their stock lifecycle and
package contract are recorded in
[`docs/manager-v3-capture-feature-proposal.md`](docs/manager-v3-capture-feature-proposal.md),
and the retained example definition mirrors the shipping manifest in
[`docs/examples/mod-definition-v3-manager-candidate.json`](docs/examples/mod-definition-v3-manager-candidate.json).

For a local package that will be launched through the CAM Merge Manager, deploy
content without the standalone executable dispatcher:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Install-LocalMod.ps1 -ContentOnly
```

## Validate

```powershell
python scripts/validate_mod.py dist/RestoreAbandonedZoo
```

The executable profile regression test installs and restores the dispatcher on
both real branch fixtures and requires each restored SHA-256 to match its input:

```powershell
powershell -ExecutionPolicy Bypass -File tests\Test-ZooRewardDispatcherProfiles.ps1 `
  -PublicExe <path-to-public-1.5.2.24-MajestyHD.exe> `
  -Beta2Exe <path-to-beta2-1.5.2.28-MajestyHD.exe>
```

The validator checks the package structure, XML links, private standalone GPL,
stock dialog resources, and all documented first-milestone boundaries. It
does not replace an in-game construction and upgrade test.

## Regenerate the Zoo rewards art

The build consumes the checked-in, packed
`assets/generated/interface/zoo-rewards-panel.tile`, so Pillow is not required
for an ordinary mod build. To regenerate it from the source master, use a
Python environment with Pillow installed:

```powershell
python scripts/generate_zoo_rewards_art.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The generator derives the exact 202x245 geometry and functional chrome from
stock `INBg` set 1019, composites the Zoo-themed backing, and packs it back into
Majesty's embedded-palette V1 TILE format.

## Regenerate the Capture Flag art

The ordinary build consumes the checked-in TILEs under
`assets/generated/capture-flag`. To regenerate them from the two source
masters, use the workspace Python environment with Pillow installed:

```powershell
..\.tools\python\Scripts\python.exe scripts\generate_capture_flag_art.py `
  --game-path "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD"
```

The generator traces stock `ARA2flag attack` and retains its 12 Special, four
Minimap, and four player-color Interface frames. It repaints those exact world
and minimap canvases, packs all twenty frames in their stock TILE formats, and
produces review previews beside them. It also repaints stock `INTC` set 1011's
25x25 Attack button and `CUR1` set 1005's 39x40 tactical cursor as matching
green-and-gold paw flags. The build clones the ARA2 IMAG as private
`ZCA2Capture flag`, clones the button resource as private `ZCICItem Icons`, and
appends CUR1 set 1038. Existing ARA2 Attack, ARA4 Explore, INTC, and CUR1 sets
remain visually and behaviorally unchanged.
