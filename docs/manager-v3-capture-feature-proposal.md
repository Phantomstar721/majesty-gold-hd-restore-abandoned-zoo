# Generic schema-v3 Capture-panel feature contract

## Status

The CAM Merge Manager implements the Zoo's native requirements as two reusable
schema-v3 records. The manager accepts the shipping Zoo definition and the
matching retained example in
[`examples/mod-definition-v3-manager-candidate.json`](examples/mod-definition-v3-manager-candidate.json).

The proposed records contain no Zoo UUID, package name, executable address,
private DLL, command, callback hook, or filesystem path. Logical keys remain
package-local and are owner-qualified by the manager.

## Correct stock control facts

The implementation reference is the shipped `MX09` Zoo parent panel, Palace
`AP41` reward controller, and stock `Fl00` Attack Flag mode.

AP41's Attack half uses these literal controls:

- action control `5002` (`0x138A`);
- amount control `8`;
- decrease control `10`;
- increase control `11`; and
- gold display control `8013` (`0x1F4D`).

Controls `5000` (`0x1388`) and `5001` (`0x1389`) belong to AP41's Explore half;
they are not the Capture amount buttons. The Zoo parent reuses command `5001`
only as the stock-shaped command that opens its package-owned reward panel.

The private placement mode and the attached Overlay Description ID are both
`ZCF0`. The stock Fl00 creation shape resolves that Overlay Description and
derives its `Restore_Capture_Flag` prototype name; the schema does not need a
second unit ID or a success callback.

## Stock lifecycle retained by the feature

1. The parent building controller receives one declared open command and opens
   a package-owned secondary panel.
2. The secondary panel is constructed through literal AP41 activation, amount
   initialization and refresh, increment/decrement, placement arm,
   cancellation, and return navigation.
3. Placement registers a package-private mode beside Fl00 while retaining the
   stock constructor, state ownership, cursor selection, target validation,
   reward debit, Overlay attachment, completion, and cancellation order.
4. The hostile-monster policy is the reusable typed target restriction. An
   optional availability attribute is read at the same stock arm and final
   completion seams. A false value posts the paired literal alert and spends
   no gold.
5. Cleanup remains stock-owned. No package callback, timer, watcher, polling
   thread, or arbitrary predicate is introduced.

The detailed evidence is in [`stock-evidence.md`](stock-evidence.md).

## Published two-record contract

The parent/secondary-panel record is:

```json
{
  "type": "stock.mx09-ap41-reward-panel.v1",
  "panel_key": "capture-rewards",
  "parent_building": "Restore_Zoo",
  "source_dialog_id": "ZC01",
  "open_command_id": 5001
}
```

The private target-mode record is:

```json
{
  "type": "stock.ap41-fl00-hostile-monster-flag.v1",
  "panel_key": "capture-rewards",
  "action_key": "capture",
  "private_mode": "ZCF0",
  "private_flag_id": "ZCF0",
  "cursor_ordinal": 38,
  "availability_attribute_id": "AZ0",
  "unavailable_alert_text": "Couldn't place reward flag, Zoo is full"
}
```

`availability_attribute_id` and `unavailable_alert_text` are a nullable pair.
Other users of the generic flag recipe may set both to `null` when they need no
availability gate.

## Validation and collision rules

- `panel_key` and `action_key` are package-local and owner-qualified.
- `parent_building` names one building declared by the same schema-v3 package;
  the manager infers and allocates its final panel identity.
- `source_dialog_id` identifies exactly one package-owned `SMNU`/`STRT` pair
  and is relocated by the manager. It never reserves a final `CGxx` ID.
- `open_command_id` is validated against the parent controller and must not
  collide with another secondary panel on that parent.
- `private_mode` and `private_flag_id` are printable FourCCs, cannot claim stock
  identities, and must be globally collision-free. For the Zoo they are
  intentionally the same `ZCF0`, matching stock Fl00 mode-to-Overlay creation.
- `cursor_ordinal` must resolve to a typed package-owned CUR1 set and cannot
  replace a stock cursor. CUR1 composition is by audited animation-set
  identity, not last-writer-wins replacement.
- Availability fields are either both null or both present. The attribute is a
  bounded engine attribute ID and the alert is bounded non-NUL Windows-1252
  text; neither field can contain code or a callback.
- Missing panels, Overlay Descriptions, cursor art, availability attributes, or
  non-identical cross-owner claims fail closed before launch.
- No UUID, display name, compatibility priority, or hardcoded Zoo identity may
  select or alter this behavior.

## Required acceptance tests

1. One conforming package composes without a compatibility adapter.
2. Two unrelated packages using distinct keys and IDs compose in either order
   and preserve both panels, modes, cursors, and Overlay creation paths.
3. Stock Palace AP41/Fl00 and AP41 Explore controls remain unchanged.
4. Invalid target, duplicate target, unavailable capacity, cancellation,
   successful placement, and panel close/reopen follow stock cleanup.
5. Unknown fields, missing paired availability data, missing resources, and
   every global collision fail closed before launch.
