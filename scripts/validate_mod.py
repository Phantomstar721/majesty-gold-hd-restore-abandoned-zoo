from __future__ import annotations

import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


MAGIC = b"CYLBPC  \x01\x00\x01\x00"
REPO_ROOT = Path(__file__).resolve().parents[1]


def cam_names(path: Path) -> set[tuple[bytes, bytes]]:
    data = path.read_bytes()
    if not data.startswith(MAGIC):
        raise ValueError(f"Not a CAM archive: {path}")
    result: set[tuple[bytes, bytes]] = set()
    section_count = struct.unpack_from("<I", data, 12)[0]
    cursor = 20
    for _ in range(section_count):
        extension = data[cursor : cursor + 4]
        section_offset = struct.unpack_from("<I", data, cursor + 4)[0]
        cursor += 8
        count = struct.unpack_from("<I", data, section_offset)[0]
        entry_cursor = section_offset + 8
        for _ in range(count):
            name = data[entry_cursor : entry_cursor + 20].rstrip(b"\x00")
            result.add((extension, name))
            entry_cursor += 28
    return result


def cam_entry_data(path: Path, wanted_extension: bytes, wanted_name: bytes) -> bytes:
    data = path.read_bytes()
    section_count = struct.unpack_from("<I", data, 12)[0]
    cursor = 20
    for _ in range(section_count):
        extension = data[cursor : cursor + 4]
        section_offset = struct.unpack_from("<I", data, cursor + 4)[0]
        cursor += 8
        if extension != wanted_extension:
            continue
        count = struct.unpack_from("<I", data, section_offset)[0]
        entry_cursor = section_offset + 8
        for _ in range(count):
            name = data[entry_cursor : entry_cursor + 20].rstrip(b"\x00")
            offset, size = struct.unpack_from("<II", data, entry_cursor + 20)
            entry_cursor += 28
            if name == wanted_name:
                return data[offset : offset + size]
    raise ValueError(f"Missing {wanted_extension!r}/{wanted_name!r} in {path}")


def cam_section_entries(path: Path, wanted_extension: bytes) -> list[tuple[bytes, bytes]]:
    data = path.read_bytes()
    section_count = struct.unpack_from("<I", data, 12)[0]
    cursor = 20
    for _ in range(section_count):
        extension = data[cursor : cursor + 4]
        section_offset = struct.unpack_from("<I", data, cursor + 4)[0]
        cursor += 8
        if extension != wanted_extension:
            continue
        count = struct.unpack_from("<I", data, section_offset)[0]
        entry_cursor = section_offset + 8
        result: list[tuple[bytes, bytes]] = []
        for _ in range(count):
            name = data[entry_cursor : entry_cursor + 20].rstrip(b"\x00")
            offset, size = struct.unpack_from("<II", data, entry_cursor + 20)
            entry_cursor += 28
            result.append((name, data[offset : offset + size]))
        return result
    raise ValueError(f"Missing {wanted_extension!r} section in {path}")


def interface_imag_set_tile_index(imag: bytes, set_id: int) -> int:
    set_count = struct.unpack_from("<I", imag, 20)[0]
    for set_index in range(set_count):
        current_id, set_offset = struct.unpack_from("<II", imag, 24 + set_index * 8)
        if current_id != set_id:
            continue
        relative = struct.unpack_from("<i", imag, set_offset + 64)[0]
        direction_offset = set_offset + relative + 4
        return struct.unpack_from("<I", imag, direction_offset + 24)[0] & 0xFFFF
    raise ValueError(f"Interface IMAG has no set {set_id}")


def compact_interface_imag_set_tile_index(imag: bytes, set_id: int) -> int:
    """Return the sole TILE in stock INTC's compact one-frame set layout."""
    set_count = struct.unpack_from("<I", imag, 20)[0]
    for set_index in range(set_count):
        current_id, set_offset = struct.unpack_from("<II", imag, 24 + set_index * 8)
        if current_id != set_id:
            continue
        relative = struct.unpack_from("<i", imag, set_offset + 64)[0]
        direction_offset = set_offset + relative + 4
        if struct.unpack_from("<I", imag, direction_offset)[0] >> 16 != 1:
            raise ValueError(f"Compact interface IMAG set {set_id} is not one frame")
        return struct.unpack_from("<I", imag, direction_offset + 16)[0] & 0xFFFF
    raise ValueError(f"Compact interface IMAG has no set {set_id}")


def tactical_cursor_set_tile_indices(imag: bytes, set_id: int) -> list[int]:
    """Return every frame/lane TILE from one end-anchored CUR1 set."""
    set_count = struct.unpack_from("<I", imag, 20)[0]
    sets = [
        struct.unpack_from("<II", imag, 24 + index * 8)
        for index in range(set_count)
    ]
    for set_index, (current_id, set_offset) in enumerate(sets):
        if current_id != set_id:
            continue
        set_end = sets[set_index + 1][1] if set_index + 1 < len(sets) else len(imag)
        direction_count = struct.unpack_from("<I", imag, set_offset)[0]
        if direction_count <= 0 or direction_count > 32:
            raise ValueError(f"Tactical cursor set {set_id} has invalid states")
        relative_offsets = [
            struct.unpack_from("<i", imag, set_offset + 64 + direction * 4)[0]
            for direction in range(direction_count)
        ]
        anchors = [set_offset + relative for relative in relative_offsets]
        result: list[int] = []
        for direction, anchor in enumerate(anchors):
            direction_end = (
                anchors[direction + 1]
                if direction + 1 < len(anchors)
                else set_end
            )
            count_word = struct.unpack_from("<I", imag, anchor + 4)[0]
            frame_count = count_word >> 16
            lane_count = count_word & 0xFFFF
            total = frame_count * lane_count
            table_start = direction_end - total * 8
            if (
                frame_count <= 0
                or lane_count <= 0
                or total > 256
                or table_start < anchor + 8
                or (table_start - anchor) % 4
            ):
                raise ValueError(
                    f"Tactical cursor set {set_id} state {direction} has an "
                    "invalid end-anchored frame table"
                )
            for field in range(total):
                result.append(
                    struct.unpack_from("<I", imag, table_start + field * 8 + 4)[0]
                    & 0xFFFF
                )
        return result
    raise ValueError(f"Tactical cursor IMAG has no set {set_id}")


def single_direction_imag_tile_indices(imag: bytes) -> list[int]:
    """Return every TILE reached through Majesty's end-anchored IMAG layout."""
    if len(imag) < 24:
        raise ValueError("Overlay IMAG is truncated")
    set_count = struct.unpack_from("<I", imag, 20)[0]
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Overlay IMAG has an invalid set table")
    sets = [
        struct.unpack_from("<II", imag, 24 + set_index * 8)
        for set_index in range(set_count)
    ]
    set_offsets = [offset for _set_id, offset in sets]
    if set_offsets != sorted(set_offsets) or len(set(set_offsets)) != len(set_offsets):
        raise ValueError("Overlay IMAG has invalid set offsets")
    result: list[int] = []
    for set_index, (set_id, set_offset) in enumerate(sets):
        set_end = sets[set_index + 1][1] if set_index + 1 < len(sets) else len(imag)
        direction_count = struct.unpack_from("<I", imag, set_offset)[0]
        direction_table_end = set_offset + 64 + direction_count * 4
        if direction_count <= 0 or direction_count > 32 or direction_table_end > set_end:
            raise ValueError("Overlay IMAG has an invalid direction count")
        relative_offsets = [
            struct.unpack_from("<i", imag, set_offset + 64 + direction * 4)[0]
            for direction in range(direction_count)
        ]
        anchors = [set_offset + relative for relative in relative_offsets]
        if (
            relative_offsets != sorted(relative_offsets)
            or len(set(relative_offsets)) != len(relative_offsets)
            or any(relative <= 0 for relative in relative_offsets)
            or anchors[0] < direction_table_end
            or anchors[-1] >= set_end
        ):
            raise ValueError(f"Overlay IMAG set {set_id} has invalid direction offsets")
        for direction, anchor in enumerate(anchors):
            direction_end = anchors[direction + 1] if direction + 1 < len(anchors) else set_end
            count_word = struct.unpack_from("<I", imag, anchor + 4)[0]
            frame_count = count_word >> 16
            lane_count = count_word & 0xFFFF
            field_count = frame_count * lane_count
            if not (0 < field_count <= 4096 and frame_count > 0 and lane_count > 0):
                if anchor + 36 > direction_end:
                    raise ValueError("Overlay IMAG direction is truncated")
                count_word = struct.unpack_from("<I", imag, anchor + 28)[0]
                frame_count = count_word >> 16
                lane_count = count_word & 0xFFFF
                field_count = frame_count * lane_count
                if not (0 < field_count <= 4096 and frame_count > 0 and lane_count > 0):
                    raise ValueError("Overlay IMAG has an unsupported direction layout")
                minimum = anchor + 32
            else:
                minimum = anchor + 8
            table_start = direction_end - field_count * 8
            if table_start < minimum or (table_start - anchor) % 4:
                raise ValueError("Overlay IMAG has an invalid end-anchored frame table")
            for field in range(field_count):
                encoded = struct.unpack_from("<I", imag, table_start + field * 8 + 4)[0]
                result.append(encoded & 0xFFFF)
    return result


def returns_nested_in_foreach(source: str) -> list[int]:
    """Find GPL returns executed from a foreach body.

    Beta2's GPL evaluator can null-write when a function result is returned
    while foreach owns the active evaluator frame. Stock Check_Mausoleum
    collects legal candidates in-loop and returns only after the loop.
    """

    blocks: list[str] = []
    pending_foreach = False
    bad_lines: list[int] = []
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        code = raw_line.split("//", 1)[0].strip().lower()
        if not code:
            continue
        if code.startswith("foreach "):
            pending_foreach = True
            continue
        if code == "begin":
            blocks.append("foreach" if pending_foreach else "block")
            pending_foreach = False
            continue
        if code.startswith("return"):
            if pending_foreach or "foreach" in blocks:
                bad_lines.append(line_number)
            pending_foreach = False
            continue
        if code.startswith("end"):
            if blocks:
                blocks.pop()
            pending_foreach = False
    return bad_lines


def indexed_strt_record(data: bytes, index: int) -> tuple[int, str]:
    count = struct.unpack_from("<H", data, 0)[0]
    if index >= count:
        raise ValueError(f"STRT index {index} is outside its {count} records")
    offset = struct.unpack_from(f"<{count}I", data, 4)[index]
    string_id = struct.unpack_from("<I", data, offset)[0]
    end = data.index(b"\x00", offset + 4)
    return string_id, data[offset + 4 : end].decode("cp1252")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    required = (
        "RestoreAbandonedZoo.mmxml",
        "mod-definition.json",
        "Data/restore_zoo_units.xml",
        "Data/restore_zoo_maindata.cam",
        "Data/restore_zoo_interfacedata.cam",
        "Data/restore_zoo_miscdata.cam",
        "Data/restore_zoo_textdata.cam",
        "Data/restore_zoo_gpltext.cam",
        "Data/RestoreAbandonedZoo.bcd",
        "GPL/RestoreAbandonedZoo_Building_Data.dat",
        "GPL/RestoreAbandonedZoo_Flag_Data.dat",
        "GPL/RestoreAbandonedZoo_Capture.gpl",
        "GPL/RestoreAbandonedZoo_DealDemon_Test.gpl",
        "GPL/RestoreAbandonedZoo.gplproj",
    )
    for relative in required:
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty: {relative}")

    if errors:
        return errors

    manifest = ET.parse(root / "RestoreAbandonedZoo.mmxml").getroot()
    definition = json.loads((root / "mod-definition.json").read_text(encoding="utf-8"))
    expected_definition = {
        "schema_version": 3,
        "mod_id": "{d45a135f-31ca-4b53-b3e4-776e231a328c}",
        "internal_name": "RestoreAbandonedZoo",
        "display_name": "Restore Abandoned Zoo",
        "custom_buildings": [
            {
                "local_name": "Restore_Zoo",
                "controller_base": "MX09",
                "panel_resource_template": "MX09",
            }
        ],
        "runtime_features": [
            {
                "type": "stock.mx09-ap41-reward-panel.v1",
                "panel_key": "capture-rewards",
                "parent_building": "Restore_Zoo",
                "source_dialog_id": "ZC01",
                "open_command_id": 5001,
            },
            {
                "type": "stock.mx04-mx05-occupant-action-panel.v1",
                "panel_key": "taming",
                "parent_building": "Restore_Zoo",
                "source_dialog_id": "ZT01",
                "open_command_id": 10800,
                "cost_callback_symbol": "Restore_Zoo_Tame_Cost",
                "action_callback_symbol": "Restore_Zoo_Tame_Beast",
            },
            {
                "type": "stock.mx22-building-open-toggle.v1",
                "toggle_key": "hero-rentals",
                "parent_building": "Restore_Zoo",
                "open_command_id": 10801,
                "close_command_id": 10802,
            },
            {
                "type": "stock.gplmx-purchase-bazaar-tail.v1",
                "callback_key": "zoo-rental",
                "callback_symbol": "Restore_Zoo_Rental_Check",
            },
            {
                "type": "stock.ap41-fl00-hostile-monster-flag.v1",
                "panel_key": "capture-rewards",
                "action_key": "capture",
                "private_mode": "ZCF0",
                "private_flag_id": "ZCF0",
                "cursor_ordinal": 38,
                "availability_attribute_id": "AZ0",
                "unavailable_alert_text": "Couldn't place reward flag, Zoo is full",
            },
        ],
    }
    if definition != expected_definition:
        errors.append("mod-definition.json does not match the Zoo schema-v3 standalone metadata")
    candidate_path = (
        REPO_ROOT / "docs" / "examples" / "mod-definition-v3-manager-candidate.json"
    )
    expected_candidate = expected_definition
    if not candidate_path.is_file():
        errors.append("Reviewed schema-v3 manager candidate definition is missing")
    elif json.loads(candidate_path.read_text(encoding="utf-8")) != expected_candidate:
        errors.append("Reviewed schema-v3 manager candidate definition changed")
    units = ET.parse(root / "Data" / "restore_zoo_units.xml").getroot()
    descriptions = units.findall("Description")
    if [item.get("Name") for item in descriptions] != [
        "Restore_Zoo1",
        "Restore_Zoo2",
        "Restore_Zoo3",
        "Restore_Capture_Flag",
    ]:
        errors.append("Unit XML must define the three Zoos and private Capture Flag in order")
    description_ids = [item.get("ID") for item in descriptions]
    if description_ids != ["ZOO1", "ZOO2", "ZOO3", "ZCF0"]:
        errors.append(f"Unexpected private Zoo description IDs: {description_ids}")
    image_ids = [item.find("./Engine/ImageIDBase").get("value") for item in descriptions]
    if image_ids != ["ABn1", "ABn2", "ABn3", "ZCA2"]:
        errors.append(f"Unexpected Zoo image IDs: {image_ids}")
    if any(item.find("./Game/DialogID").get("value") != "MX09" for item in descriptions[:3]):
        errors.append("Every Zoo level must use the stock MX09 panel controller")
    if len(descriptions) == 4:
        capture_flag = descriptions[3]
        if capture_flag.get("subType") != "Overlay":
            errors.append("Private ZCF0 must retain the stock Overlay description type")
        if capture_flag.find("./Game/DialogID").get("value") != "AP46":
            errors.append("Private ZCF0 must use the stock Attack Flag AP46 panel")
        callback = capture_flag.find("./Engine/Script")
        if callback is None or callback.get("GPLFunction") != "Restore_Capture_Flag_Death_Callback":
            errors.append("Private ZCF0 must use the scoped Zoo flag callback")

    load = manifest.find("./Mod/DataConfiguration/Dataset/Load")
    if load is None:
        errors.append("Manifest load block is missing")
    elif load.find("GPL") is None:
        errors.append("Standalone Zoo GPL load block is missing")
    else:
        if [item.text for item in load.findall("Descriptions")] != [
            "Data\\restore_zoo_units.xml"
        ]:
            errors.append("Manifest must load only the Zoo building descriptions")
        if [item.text for item in load.findall("CAM")] != [
            "Data\\restore_zoo_maindata.cam",
            "Data\\restore_zoo_interfacedata.cam",
            "Data\\restore_zoo_miscdata.cam",
            "Data\\restore_zoo_textdata.cam",
            "Data\\restore_zoo_gpltext.cam",
        ]:
            errors.append("Manifest CAM load order does not match the Zoo package contract")
        if [item.text for item in load.find("GPL").findall("Source")] != [
            "GPL\\RestoreAbandonedZoo_Building_Data.dat",
            "GPL\\RestoreAbandonedZoo_Flag_Data.dat",
            "GPL\\RestoreAbandonedZoo_Capture.gpl",
            "GPL\\RestoreAbandonedZoo_DealDemon_Test.gpl",
        ]:
            errors.append("Manifest GPL sources are missing the Deal Demon test fixture")

    text_names = cam_names(root / "Data" / "restore_zoo_textdata.cam")
    if not {
        (b"SMNU", b"MX09"),
        (b"SMNU", b"ZC01"),
        (b"SMNU", b"ZT01"),
        (b"STRT", b"MX09"),
        (b"STRT", b"ZC01"),
        (b"STRT", b"ZT01"),
        (b"STRT", b"UNTN"),
    } <= text_names:
        errors.append(f"Zoo text CAM has unexpected entries: {sorted(text_names)}")
    zoo_menu = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"SMNU", b"MX09"
    )
    if zoo_menu.count(struct.pack("<I", 0x1F55)) != 1:
        errors.append("Zoo panel must contain exactly one stock Visitors command")
    if zoo_menu.count(struct.pack("<I", 0x1389)) != 1:
        errors.append("Zoo panel must contain exactly one stock Palace REWARDS command")
    if zoo_menu.count(struct.pack("<I", 0x2293)) != 0:
        errors.append("Zoo panel must not retain its orphaned Place Reward command")
    if zoo_menu.count(struct.pack("<I", 0x2A30)) != 1:
        errors.append("Zoo panel must contain exactly one private Tame Beast opener")
    if zoo_menu.count(struct.pack("<I", 0x2A31)) != 1:
        errors.append("Zoo panel must contain exactly one private rental-open command")
    if zoo_menu.count(struct.pack("<I", 0x2A32)) != 1:
        errors.append("Zoo panel must contain exactly one private rental-close command")
    if zoo_menu[0x09FC:0x0A00] != b"\xff" * 4:
        errors.append("Zoo panel must preserve the preceding control terminator")
    tame_control = zoo_menu[0x0A00:0x0AC4]
    if (
        len(tame_control) != 0xC4
        or struct.unpack_from("<4I", tame_control, 0x08) != (7, 217, 93, 26)
        or struct.unpack_from("<I", tame_control, 0x30)[0] != 26
        or struct.unpack_from("<I", tame_control, 0x38)[0] != 27
        or tame_control[0x48:0x4C] != b"ZTBB"
        or struct.unpack_from("<I", tame_control, 0x50)[0] != 1009
        or struct.unpack_from("<I", tame_control, 0x88)[0] != 0x2A30
    ):
        errors.append("Zoo Tame Beast opener is not the audited AP10 control clone")
    close_rental_control = zoo_menu[0x0AC4:0x0B88]
    open_rental_control = zoo_menu[0x0B88:0x0C4C]
    rental_specs = (
        (close_rental_control, 0x2A32, 28, 29),
        (open_rental_control, 0x2A31, 30, 31),
    )
    for control, command, label, tooltip in rental_specs:
        if (
            len(control) != 0xC4
            or struct.unpack_from("<4I", control, 0x08) != (100, 190, 93, 26)
            or struct.unpack_from("<I", control, 0x30)[0] != label
            or struct.unpack_from("<I", control, 0x38)[0] != tooltip
            or control[0x48:0x4C] != b"INBb"
            or struct.unpack_from("<I", control, 0x50)[0] != 1004
            or struct.unpack_from("<I", control, 0x88)[0] != command
            or control[-4:] != b"\xff" * 4
        ):
            errors.append(
                f"Zoo rental toggle {command:#x} is not the audited AP10 gold HEROES presentation clone"
            )
    if zoo_menu[-8:] != b"\xff" * 8:
        errors.append("Zoo panel must terminate the rental control and dialog stream")
    if zoo_menu.count(b"\xff" * 8) != 1:
        errors.append("Zoo panel must not terminate before its appended controls")
    if zoo_menu[0x08CC:0x08D0] != struct.pack("<I", 0x1389):
        errors.append("Zoo Place Reward control must dispatch the stock Palace REWARDS command")
    place_reward_control = zoo_menu[0x0844:0x0908]
    if (
        len(place_reward_control) != 0xC4
        or struct.unpack_from("<4I", place_reward_control, 0x08)
        != (7, 190, 93, 26)
        or struct.unpack_from("<I", place_reward_control, 0x30)[0] != 22
        or struct.unpack_from("<I", place_reward_control, 0x38)[0] != 23
        or place_reward_control[0x48:0x4C] != b"ZCBB"
        or struct.unpack_from("<I", place_reward_control, 0x50)[0] != 1009
        or struct.unpack_from("<I", place_reward_control, 0x88)[0] != 0x1389
        or place_reward_control[-4:] != b"\xff" * 4
    ):
        errors.append("Zoo reward opener is not the private Capture AP10 control clone")
    if len(zoo_menu) != 3152:
        errors.append(
            "Zoo panel must contain the restored Visitors, Tame, and rental controls"
        )
    zoo_rewards_menu = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"SMNU", b"ZC01"
    )
    if zoo_rewards_menu.count(b"ZOBG") != 1 or b"INBg" in zoo_rewards_menu:
        errors.append("Private Zoo rewards panel must select only private ZOBG art")
    attack_icon_control = zoo_rewards_menu[0x0660:0x06B8]
    if attack_icon_control.count(b"ZCIC") != 1 or b"INTC" in attack_icon_control:
        errors.append("Private Zoo Capture control must select only private ZCIC art")
    hidden_controls = {
        0x00A0: 0x1388,
        0x0118: 0x1389,
        0x0238: 0x138B,
        0x02E0: 0x138C,
        0x0380: 0x1B5A,
    }
    for offset, hidden_command in hidden_controls.items():
        if zoo_rewards_menu.count(struct.pack("<I", hidden_command)) != 1:
            errors.append(
                f"Private Zoo rewards panel lacks stock Explore control {hidden_command:#x}"
            )
        if struct.unpack_from("<II", zoo_rewards_menu, offset + 8) != (1500, 1500):
            errors.append(
                f"Private Zoo rewards panel does not hide Explore control {hidden_command:#x} at stock off-panel coordinates"
            )
    capture_controls = {
        0x0204: 0x138A,
        0x0448: 0x08,
        0x0550: 0x0A,
        0x05C8: 0x0B,
        0x0640: 0x1F4D,
        0x06A4: 0x1B59,
    }
    for offset, capture_command in capture_controls.items():
        if zoo_rewards_menu[offset : offset + 4] != struct.pack(
            "<I", capture_command
        ):
            errors.append(
                f"Private Zoo rewards panel lacks stock Capture-path control {capture_command:#x} at {offset:#x}"
            )
    if len(zoo_rewards_menu) != 1720:
        errors.append("Private Zoo rewards panel must retain AP41's complete dialog stream")
    zoo_tame_menu = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"SMNU", b"ZT01"
    )
    if len(zoo_tame_menu) != 1452:
        errors.append("Private Zoo tame panel must retain MX05's complete dialog stream")
    if zoo_tame_menu.count(b"ZOBG") != 2 or b"INBg" in zoo_tame_menu:
        errors.append("Private Zoo tame panel must select only private ZOBG art")
    for control_id, label in (
        (0x1388, "occupant list"),
        (0x138B, "selected action"),
        (0x1F46, "selected cost"),
    ):
        if zoo_tame_menu.count(struct.pack("<I", control_id)) != 1:
            errors.append(f"Private Zoo tame panel lacks its stock {label} control")
    zoo_strings = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"STRT", b"MX09"
    )
    expected_zoo_control_strings = {
        22: "REWARD",
        23: "Open the Zoo's Capture reward panel.",
        26: "TAME BEAST",
        27: "Open the Zoo's Tame Beast panel.",
        28: "RENT ON",
        29: "Close the Zoo to hero rentals.",
        30: "RENT OFF",
        31: "Open the Zoo to hero rentals.",
    }
    for index, expected_text in expected_zoo_control_strings.items():
        if indexed_strt_record(zoo_strings, index)[1] != expected_text:
            errors.append(f"Zoo control string {index} is not {expected_text!r}")
    zoo_rewards_strings = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"STRT", b"ZC01"
    )
    expected_zoo_reward_strings = {
        2: "Capture Flag",
        3: "Place a Capture Flag.",
        9: "Current Capture Flag default reward amount in gold",
        10: "Capture",
        11: "Decrease Capture Flag reward amount.",
        12: "Increase Capture Flag reward amount.",
        13: "Return to the Zoo's Main Window.",
    }
    for index, expected_text in expected_zoo_reward_strings.items():
        if indexed_strt_record(zoo_rewards_strings, index)[1] != expected_text:
            errors.append(f"Private Zoo rewards string {index} is not {expected_text!r}")
    zoo_tame_strings = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"STRT", b"ZT01"
    )
    expected_zoo_tame_strings = {
        1: "ZOO",
        6: "CAPTURED MONSTERS",
        7: "TAME BEAST",
        8: "Release the selected monster to guard your kingdom.",
        10: "Cost to tame the selected monster",
    }
    for index, expected_text in expected_zoo_tame_strings.items():
        if indexed_strt_record(zoo_tame_strings, index)[1] != expected_text:
            errors.append(f"Private Zoo tame string {index} is not {expected_text!r}")
    art_names = cam_names(root / "Data" / "restore_zoo_maindata.cam")
    image_names = {name for extension, name in art_names if extension == b"IMAG"}
    for prefix in (b"ABn1", b"ABn2", b"ABn3"):
        if sum(name.startswith(prefix) for name in image_names) != 1:
            errors.append(f"Zoo main-data CAM lacks one stock {prefix.decode()} IMAG record")
    if not any(extension == b"TILE" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the positional stock TILE table")
    if not any(extension == b"SPLT" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the stock palette table")
    capture_art_path = root / "Data" / "restore_zoo_maindata.cam"
    capture_art_names = cam_names(capture_art_path)
    capture_images = {
        name for extension, name in capture_art_names if extension == b"IMAG"
    }
    if b"ZCA2Capture flag" not in capture_images:
        errors.append(
            f"Combined Zoo main-art CAM lacks private ZCA2: {sorted(capture_images)}"
        )
    capture_imag = cam_entry_data(
        capture_art_path,
        b"IMAG",
        b"ZCA2Capture flag",
    )
    capture_tiles = cam_section_entries(capture_art_path, b"TILE")
    capture_palettes = cam_section_entries(capture_art_path, b"SPLT")
    private_start = 17224
    if len(capture_tiles) != private_start + 20:
        errors.append(
            f"Private Capture Flag CAM has {len(capture_tiles)} TILE slots; expected {private_start + 20}"
        )
    else:
        private_tiles = capture_tiles[private_start:]
        if any(not data for _name, data in private_tiles):
            errors.append("Private Capture Flag CAM has an empty private TILE")
        versions = [struct.unpack_from("<H", data, 0)[0] for _name, data in private_tiles]
        if versions != [3] * 16 + [1] * 4:
            errors.append(f"Private Capture Flag TILE versions are unexpected: {versions}")
        indexed_palettes = [
            struct.unpack_from("<I", data, 22)[0]
            for _name, data in private_tiles[:16]
        ]
        if indexed_palettes != [793] * 16:
            errors.append(
                f"Private Capture Flag indexed TILE palettes are unexpected: {indexed_palettes}"
            )
    if len(capture_palettes) != 794 or any(
        not data for _name, data in capture_palettes
    ):
        errors.append(
            "Private Capture Flag CAM must carry complete stock palettes 0-793"
        )
    capture_indices = single_direction_imag_tile_indices(capture_imag)
    if capture_indices != list(range(private_start, private_start + 20)):
        errors.append(
            f"Private ZCA2 IMAG does not retain the stock 20-frame order: {capture_indices}"
        )
    interface_names = cam_names(root / "Data" / "restore_zoo_interfacedata.cam")
    interface_images = {
        name for extension, name in interface_names if extension == b"IMAG"
    }
    for prefix in (b"IX92", b"IX94"):
        if sum(name.startswith(prefix) for name in interface_images) != 1:
            errors.append(
                f"Zoo interface-data CAM lacks one stock {prefix.decode()} IMAG record"
            )
    if not any(extension == b"TILE" for extension, _ in interface_names):
        errors.append("Zoo interface-data CAM lacks the positional stock TILE table")
    rewards_interface = root / "Data" / "restore_zoo_interfacedata.cam"
    rewards_interface_names = cam_names(rewards_interface)
    rewards_interface_images = {
        name for extension, name in rewards_interface_names if extension == b"IMAG"
    }
    rewards_palettes = cam_section_entries(rewards_interface, b"PALT")
    if len(rewards_palettes) != 7 or any(
        not data for _name, data in rewards_palettes
    ):
        errors.append("Zoo rewards interface CAM must carry all seven stock PALT entries")
    if not {
        b"ZOBGbuilding dialog",
        b"ZCICItem Icons",
        b"ZCBBbuilding frame",
        b"ZTBBbuilding frame",
        b"CUR1Tactical Cursor",
    } <= rewards_interface_images:
        errors.append(
            f"Combined Zoo interface CAM lacks private reward art: {sorted(rewards_interface_images)}"
        )
    if not any(extension == b"TILE" for extension, _ in rewards_interface_names):
        errors.append("Zoo rewards interface CAM lacks its private positional TILE table")
    else:
        rewards_imag = cam_entry_data(
            rewards_interface, b"IMAG", b"ZOBGbuilding dialog"
        )
        rewards_tiles = cam_section_entries(rewards_interface, b"TILE")
        rewards_tile = None
        rewards_tile_index = interface_imag_set_tile_index(rewards_imag, 1019)
        tame_tile_index = interface_imag_set_tile_index(rewards_imag, 1013)
        if rewards_tile_index >= len(rewards_tiles):
            errors.append("Private ZOBG set 1019 references a missing TILE")
        else:
            rewards_tile = rewards_tiles[rewards_tile_index][1]
            if len(rewards_tile) < 26 or struct.unpack_from("<H", rewards_tile, 0)[0] != 1:
                errors.append("Private Zoo rewards backing is not a V1 TILE")
            elif struct.unpack_from("<HH", rewards_tile, 2) != (245, 202):
                errors.append("Private Zoo rewards backing is not stock 202x245 geometry")
            elif rewards_tile != (
                REPO_ROOT
                / "assets"
                / "generated"
                / "interface"
                / "zoo-rewards-panel.tile"
            ).read_bytes():
                errors.append("Private Zoo rewards backing does not contain Zoo art")
        if tame_tile_index >= len(rewards_tiles):
            errors.append("Private ZOBG set 1013 references a missing TILE")
        else:
            tame_tile = rewards_tiles[tame_tile_index][1]
            if len(tame_tile) < 26 or struct.unpack_from("<H", tame_tile, 0)[0] != 1:
                errors.append("Private Zoo tame backing is not a V1 TILE")
            elif struct.unpack_from("<HH", tame_tile, 2) != (245, 202):
                errors.append("Private Zoo tame backing is not stock 202x245 geometry")
            elif rewards_tile is not None and tame_tile == rewards_tile:
                errors.append(
                    "Zoo Tame panel must retain MX05 list/action chrome, not Capture-panel art"
                )
        capture_icon_imag = cam_entry_data(
            rewards_interface, b"IMAG", b"ZCICItem Icons"
        )
        capture_icon_index = compact_interface_imag_set_tile_index(
            capture_icon_imag, 1011
        )
        if capture_icon_index >= len(rewards_tiles):
            errors.append("Private ZCIC set 1011 references a missing TILE")
        else:
            capture_icon_tile = rewards_tiles[capture_icon_index][1]
            if len(capture_icon_tile) < 26 or struct.unpack_from(
                "<H", capture_icon_tile, 0
            )[0] != 1:
                errors.append("Private Zoo Capture button icon is not a V1 TILE")
            elif struct.unpack_from("<HH", capture_icon_tile, 2) != (25, 25):
                errors.append("Private Zoo Capture button icon is not stock 25x25 geometry")
            elif struct.unpack_from("<H", capture_icon_tile, 20)[0] != 1:
                errors.append("Private Zoo Capture button icon lacks its embedded palette")
        for art_name, label in (
            (b"ZCBBbuilding frame", "Capture"),
            (b"ZTBBbuilding frame", "Tame"),
        ):
            parent_button_imag = cam_entry_data(
                rewards_interface, b"IMAG", art_name
            )
            parent_button_indices = tactical_cursor_set_tile_indices(
                parent_button_imag, 1009
            )
            if not (
                len(parent_button_indices) == 7
                and parent_button_indices[2:6]
                == [parent_button_indices[2]] * 4
                and len(set(parent_button_indices)) == 4
            ):
                errors.append(
                    f"Private {art_name[:4].decode()} set 1009 changed AP10's "
                    "four-state button topology"
                )
            elif any(
                tile_index < 2624
                or tile_index >= len(rewards_tiles)
                or not rewards_tiles[tile_index][1]
                for tile_index in parent_button_indices
            ):
                errors.append(
                    f"Private {art_name[:4].decode()} set 1009 references a "
                    "missing private TILE"
                )
            else:
                for tile_index in set(parent_button_indices):
                    parent_tile = rewards_tiles[tile_index][1]
                    if (
                        len(parent_tile) < 26
                        or struct.unpack_from("<H", parent_tile, 0)[0] != 3
                        or struct.unpack_from("<HH", parent_tile, 2) != (26, 93)
                    ):
                        errors.append(
                            f"Private {label} action is not stock 93x26 V3 geometry"
                        )
                        break
        cursor_imag = cam_entry_data(
            rewards_interface, b"IMAG", b"CUR1Tactical Cursor"
        )
        cursor_set_count = struct.unpack_from("<I", cursor_imag, 20)[0]
        cursor_set_ids = [
            struct.unpack_from("<I", cursor_imag, 24 + index * 8)[0]
            for index in range(cursor_set_count)
        ]
        if cursor_set_count != 29 or len(set(cursor_set_ids)) != 29:
            errors.append("Extended CUR1 must contain 29 unique stock-shaped cursor sets")
        stock_cursor_indices = [
            tile_index
            for set_id in cursor_set_ids
            if set_id != 1038
            for tile_index in tactical_cursor_set_tile_indices(cursor_imag, set_id)
        ]
        capture_cursor_indices = tactical_cursor_set_tile_indices(cursor_imag, 1038)
        all_cursor_indices = stock_cursor_indices + capture_cursor_indices
        if any(
            tile_index >= 2624
            or not rewards_tiles[tile_index][1]
            for tile_index in stock_cursor_indices
        ):
            errors.append("Every stock CUR1 state must retain a populated original TILE")
        elif any(
            tile_index >= len(rewards_tiles) or not rewards_tiles[tile_index][1]
            for tile_index in capture_cursor_indices
        ):
            errors.append("Private CUR1 set 1038 references a missing TILE")
        else:
            for tile_index in set(all_cursor_indices):
                cursor_tile = rewards_tiles[tile_index][1]
                if len(cursor_tile) < 26:
                    errors.append("Extended CUR1 contains a truncated TILE")
                    break
                palette_mode = struct.unpack_from("<H", cursor_tile, 20)[0]
                palette_value = struct.unpack_from("<I", cursor_tile, 22)[0]
                if palette_mode == 0 and palette_value >= len(rewards_palettes):
                    errors.append("Extended CUR1 references a missing PALT entry")
                    break
                if palette_mode == 1 and palette_value >= len(cursor_tile):
                    errors.append("Extended CUR1 contains an invalid embedded palette")
                    break
        attack_cursor_indices = tactical_cursor_set_tile_indices(cursor_imag, 1005)
        explore_cursor_indices = tactical_cursor_set_tile_indices(cursor_imag, 1006)
        if attack_cursor_indices != [27, 27, 24, 27, 25]:
            errors.append("Extended CUR1 changed the complete stock Attack cursor topology")
        elif explore_cursor_indices != [26, 26, 24, 26, 25]:
            errors.append("Extended CUR1 changed the complete stock Explore cursor topology")
        elif not (
            len(capture_cursor_indices) == 5
            and capture_cursor_indices[0] == capture_cursor_indices[1]
            and capture_cursor_indices[1] == capture_cursor_indices[3]
            and capture_cursor_indices[0] >= 2624
            and capture_cursor_indices[2] == 24
            and capture_cursor_indices[4] == 25
        ):
            errors.append(
                "Private Capture cursor must replace only Attack's three primary "
                "frames and retain stock common-state TILEs 24/25"
            )
        else:
            capture_cursor_index = capture_cursor_indices[0]
            capture_cursor_tile = rewards_tiles[capture_cursor_index][1]
            if len(capture_cursor_tile) < 26 or struct.unpack_from(
                "<H", capture_cursor_tile, 0
            )[0] != 3:
                errors.append("Private Zoo Capture cursor is not a V3 TILE")
            elif struct.unpack_from("<HH", capture_cursor_tile, 2) != (40, 39):
                errors.append("Private Zoo Capture cursor changed stock 39x40 geometry")
        expected_common_cursor_hashes = {
            24: "3e946afa4b2edb01dd4d10f4c37045c4527bf8b1709b844748e6ceef8aabc357",
            25: "b375dce052dcc28061dfd4c509041315d5131c66ef2ee18243b16c06e9460da3",
        }
        for tile_index, expected_hash in expected_common_cursor_hashes.items():
            actual_hash = hashlib.sha256(rewards_tiles[tile_index][1]).hexdigest()
            if actual_hash != expected_hash:
                errors.append(
                    f"CUR1 common-state TILE {tile_index} is not the exact stock payload"
                )
    help_names = cam_names(root / "Data" / "restore_zoo_gpltext.cam")
    if not {(b"STRT", b"AITX"), (b"STRT", b"HPTX")} <= help_names:
        errors.append("Zoo GPL text CAM lacks STRT/AITX or STRT/HPTX")
    else:
        intent_data = cam_entry_data(
            root / "Data" / "restore_zoo_gpltext.cam", b"STRT", b"AITX"
        )
        rental_intent = indexed_strt_record(intent_data, 197)
        if rental_intent != (197, "Renting a beast"):
            errors.append("Reserved intent 197 must contain the rental action text")
        intent_record = indexed_strt_record(intent_data, 198)
        if intent_record != (198, "Capturing a monster"):
            errors.append(
                "Reserved intent 198 must contain the Capture action text"
            )
        zoo_occupant_intent = indexed_strt_record(intent_data, 199)
        if zoo_occupant_intent != (199, "waiting in the zoo"):
            errors.append(
                "Reserved intent 199 must contain the Zoo occupant text"
            )
    bdep = cam_entry_data(
        root / "Data" / "restore_zoo_miscdata.cam", b"DATA", b"BDEP"
    )
    expected_bdep_rows = {
        b"ZOO1",
        b"ZOO2",
        b"ZOO3",
    }
    for row in expected_bdep_rows:
        if bdep.splitlines().count(row) != 1:
            errors.append(f"BDEP must contain exactly one row: {row.decode()}")

    gpl = (root / "GPL" / "RestoreAbandonedZoo_Building_Data.dat").read_text(encoding="utf-8")
    for name in ("Restore_Zoo1", "Restore_Zoo2", "Restore_Zoo3"):
        if f"[{name}]" not in gpl:
            errors.append(f"Standalone GPL lacks [{name}]")
    for duplicate in ("[Zoo1]", "[Zoo2]", "[Zoo3]"):
        if duplicate in gpl:
            errors.append(f"GPL duplicates shipped prototype {duplicate}")
    if gpl.count("(birthScript2 Restore_Zoo_Building_Birth)") != 3:
        errors.append("Every Zoo level must refresh capacity after stock Building_Birth")
    if gpl.count("(birthscript Restore_Zoo_Building_Birth)") != 2:
        errors.append(
            "Zoo levels two and three must copy the stock Marketplace upgrade "
            "birthscript revenue restart"
        )
    if gpl.count("(upgradescript Restore_Zoo_Upgrade)") != 3:
        errors.append("Every Zoo level must queue through the stock upgrade callback")
    if gpl.count("(Visited_Script Restore_Zoo_Visited)") != 3:
        errors.append("Every Zoo level must dispatch visits through the rental wrapper")

    rental_fixture = (root / "GPL" / "RestoreAbandonedZoo_DealDemon_Test.gpl").read_text(
        encoding="utf-8"
    )
    required_rental_fixture = (
        "function Restore_Zoo_Prepare_Rental_Test_Hero",
        "$Advance_To_Level ( thisagent, 20 )",
        "$SetAttribute ( thisagent, #ATTRIB_Gold, 50000 )",
        "$SetAttribute ( thisagent, #ATTRIB_Armor_Struct_Bonus, 3 )",
        "$SetAttribute ( thisagent, #ATTRIB_Weapon_Struct_Bonus, 3 )",
        "$SetAttribute ( thisagent, #ATTRIB_Armor_Magic_Bonus, 3 )",
        "$SetAttribute ( thisagent, #ATTRIB_Weapon_Magic_Bonus, 3 )",
        "$SetAttribute ( thisagent, #ATTRIB_NumHealingPotions, #Max_Heal_Potions )",
        '$SpawnUnit ( palace, "Warrior",',
        '$SpawnUnit ( palace, "Ranger",',
        '$SpawnUnit ( palace, "Rogue",',
        '$SpawnUnit ( palace, "Wizard",',
    )
    for snippet in required_rental_fixture:
        if snippet not in rental_fixture:
            errors.append(f"Deal with a Demon rental fixture lacks: {snippet}")

    flag_gpl = (root / "GPL" / "RestoreAbandonedZoo_Flag_Data.dat").read_text(
        encoding="utf-8"
    )
    required_flag_contract = (
        "[Restore_Capture_Flag]",
        "{RewardFlag",
        "(type RewardFlag)",
        "(subtype Capture_Flag)",
        "(title Flag_Attack)",
        "(birthscript Restore_Capture_Flag_Birth)",
        "(activescript Restore_Capture_Flag_Poll)",
        "(deathscript Restore_Capture_Flag_Death)",
    )
    for snippet in required_flag_contract:
        if snippet not in flag_gpl:
            errors.append(f"Private Capture Flag stock clone is missing: {snippet}")
    if "[Flag_Attack]" in flag_gpl:
        errors.append("Private Capture Flag data must not replace stock [Flag_Attack]")
    capture = (root / "GPL" / "RestoreAbandonedZoo_Capture.gpl").read_text(
        encoding="utf-8"
    )
    for gpl_path in sorted((root / "GPL").glob("*.gpl")):
        nested_returns = returns_nested_in_foreach(
            gpl_path.read_text(encoding="utf-8")
        )
        if nested_returns:
            rendered = ", ".join(str(line) for line in nested_returns)
            errors.append(
                f"{gpl_path.name} returns from inside foreach at line(s) {rendered}"
            )
    required_capture_contract = (
        "function Restore_Capture_Flag_Birth",
        "function Restore_Zoo_Visitor_Limit",
        'zoo\'s "Level" >= 3',
        "return 8",
        'zoo\'s "Level" == 2',
        "return 6",
        "return 4",
        "function Restore_Is_Latched_Capture",
        'hero = hooligan\'s "leader"',
        'hero\'s "Target" == hooligan',
        'hero\'s "ActiveScript" == $Arrest_Hooligan',
        'hero\'s "BackScript" == $Arrest_Hooligan',
        "function Restore_Zoo_Pending_Reservations",
        'hooligan\'s "Target" == zoo',
        "function Restore_Refresh_Zoo_Capacity",
        "#ATTRIB_Zoo_Legal_Target, 1",
        "#ATTRIB_Zoo_Legal_Target, 0",
        "function Restore_Zoo_Building_Birth",
        "$Building_Birth ( zoo )",
        "function Restore_Zoo_Upgrade_Complete",
        'zoo\'s "birthScript2" = $Restore_Zoo_Upgrade_Complete',
        "function Restore_Zoo_Upgrade",
        "$basic_upgrade ( zoo )",
        'zoo\'s "birthScript2", #palace_upgrade_check, zoo',
        "#ATTRIB_CurrentStageBuilt",
        "function Restore_Captive_Hooligan_Death",
        "$Hooligan_Death ( thisagent )",
        "function Restore_Find_Available_Zoo",
        "function Restore_Find_Completed_Zoo",
        '$ListObjects ( thisagent, "building", -1, zoos,',
        '#MyPlayer, #CheckTitles, "Zoo", #ATTRIB_FirstStageBuilt, 1',
        'visitors = zoo\'s "Occupants"',
        '$Restore_Zoo_Pending_Reservations ( zoo )',
        'if ( occupied < limit )',
        'legal_zoos << zoo',
        'zoo = $ListMember ( legal_zoos, 1 )',
        'zoo = thisagent\'s "Target"',
        "expression #intent_waiting_in_zoo 199",
        "expression #intent_capturing_monster 198",
        "function Restore_Controlled_To_Hooligan",
        "function Restore_Begin_Stock_Zoo_Control",
        "$Control_Monster ( hero, thisagent )",
        '#ATTRIB_HP,',
        '#ATTRIB_MaxHP ) / 3',
        'thisagent\'s "BackScript" = $Restore_Controlled_To_Hooligan',
        'thisagent\'s "Type" = "Hidden"',
        '$DeleteEffector ( thisagent, "Charm_icon" )',
        '( hero\'s "Num_Followers" ) --',
        "function Restore_Hooligan_Basic",
        "function Restore_Hooligan_Goto_Zoo",
        "function Restore_Assign_Hooligan",
        "if ( committed >= limit )",
        "valid_heroes << hero",
        "hero = $ListMember ( valid_heroes, 1 )",
        'thisagent\'s "leader" = hero',
        "$SpecifyIntent ( hero, #intent_capturing_monster )",
        'hero\'s "Target" = thisagent',
        'hero\'s "ActiveScript" = $Arrest_Hooligan',
        'hero\'s "ActiveScript" != $Arrest_Hooligan',
        'hero\'s "BackScript" != $Arrest_Hooligan',
        'thisagent\'s "Type" = "Hooligan"',
        'thisagent\'s "BackScript" = $Restore_Hooligan_Basic',
        'thisagent\'s "ActiveScript" = $Restore_Hooligan_Goto_Zoo',
        "$Hide ( thisagent, zoo )",
        'owner = thisagent\'s "leader"',
        'owner\'s "Target" != thisagent',
        'owner\'s "ActiveScript" != $Arrest_Hooligan',
        'owner\'s "BackScript" != $Arrest_Hooligan',
        'thisagent\'s "Special_Boolean" = FALSE',
        '$Restore_Assign_Hooligan ( thisagent, owner )',
        "$DistanceBetweenAgents ( thisagent, owner ) >",
        "#Arrest_Hooligan_Dist",
        "$StopMoving ( thisagent )",
        "$Reset_Tasks ( owner )",
        'visitors = zoo\'s "Occupants"',
        "if ( $Restore_Zoo_Captive_Count ( zoo ) >= limit )",
        "$Enter_Building ( thisagent, zoo )",
        "$SpecifyIntent ( thisagent, #intent_waiting_in_zoo )",
        "expression #Restore_Zoo_Breakout_Threshold 6",
        "expression #Restore_Zoo_Breakout_Period 60000",
        "function Restore_Zoo_Breakout_Check",
        "$GetBuildingContainer ( thisagent )",
        "#Restore_Zoo_Breakout_Threshold",
        '$Restore_Zoo_Release_Captive ( thisagent, zoo )',
        'thisagent\'s "ActiveScript" = $Restore_Zoo_Breakout_Check',
        'thisagent\'s "BasicScript" = $Restore_Zoo_Breakout_Check',
        'thisagent\'s "BackScript" = $Restore_Zoo_Breakout_Check',
        '#Restore_Zoo_Breakout_Period',
        "$ListObjects ( zoo, \"Hooligan\", -1, hooligans, #NoHiddenMap )",
        "$MessageFlag ( zoo, #message_arrested_all_hooligans )",
        'thisagent\'s "IGDeathScript" = $Restore_Captive_Hooligan_Death',
        "#ATTRIB_NotFlaggable, 1",
        "#ATTRIB_NotSpellTarget, 1",
        '$SetThreadInterval ( thisagent\'s "ActiveScript", #Henchmen_Cycle )',
        'thisagent\'s "leader" = $NullAgent ()',
        '$Restore_Assign_Hooligan ( thisagent, $NullAgent () )',
        '$Restore_Find_Available_Zoo ( thisagent )',
        '#ATTRIB_RewardCost',
        'charm_percentage = 50 * (',
        '$Sqrt (( cash / 20.0 ) / target_strength )',
        'if ( charm_percentage > 95 )',
        '$RandomNumber ( 100 ) + 1',
        '$ListObjects (',
        'thisagent, "Hero", -1, heroes, #NoHiddenMap',
        "function Restore_Capture_Flag_Poll",
        "function Restore_Capture_Flag_Death_Callback",
        "function Restore_Capture_Flag_Death",
        '"RewardFlag", -1, flags, #RewardFlags',
        'flag\'s "SubType" == "Capture_Flag"',
        "function monster_gravestone",
        'deadflag = TRUE',
        '$Restore_Stock_Zoo_Flag_Check ( thisagent ) == TRUE',
        'thisagent\'s "Type" = "Dead"',
        'thisagent\'s "ActiveScript" = $be_dead_2',
        '"basic_death", thisagent',
        "function Restore_Stock_Zoo_Flag_Check",
        'thisagent\'s "Familiar" == TRUE',
        "$GetUnitPlayerNumber ( thisagent ) != #Monster_Player",
        "revenue = 0",
        'if ( $HasAttribute ( "RevenueScript", thisagent ))',
        'thisagent\'s "RevenueScript" == $Restore_Zoo_Revenue',
        "private_zoo = TRUE",
        "expression #intent_renting_beast 197",
        "function Restore_Zoo_Is_Stored_Captive",
        "function Restore_Zoo_Captive_Count",
        "function Restore_Zoo_Find_Rentable_Captive",
        "function Restore_Zoo_Rental_Check",
        "#ATTRIB_EmbassyActiveFlag",
        "#Percent_Chance_To_Buy_Stats",
        'thisagent\'s "TaskName" = "Rent_Beast"',
        "$SpecifyIntent ( thisagent, #intent_renting_beast )",
        "function Restore_Zoo_Visited",
        "function Restore_Zoo_Complete_Rental",
        "function Restore_Zoo_Finish_Rental",
        "function Restore_Zoo_Start_Rented_Beast",
        "$Spend_Gold ( thisagent, zoo, cost )",
        "$Control_Monster ( buyer, captive )",
        '$NewThread ( captive\'s "ActiveScript", #Normal_Cycle, captive )',
    )
    for snippet in required_capture_contract:
        if snippet not in capture:
            errors.append(f"Zoo capture stock-clone contract is missing: {snippet}")
    revenue_start = capture.index("function Restore_Zoo_Revenue")
    release_start = capture.index("function release_occupants")
    revenue = capture[revenue_start:release_start]
    if "$IsDead ( visitor )" in revenue:
        errors.append(
            "Zoo revenue must count valid stored occupants without filtering "
            "their stock subdued state"
        )
    release_end = capture.index("function Restore_Zoo_Visitor_Limit", release_start)
    release = capture[release_start:release_end]
    if 'thisagent\'s "birthScript2" == $Restore_Zoo_Building_Birth' in release:
        errors.append("Living-Zoo release protection must not use a mutable callback slot")
    if 'thisagent\'s "Title" == "Zoo" &&' in release:
        errors.append(
            "Living-Zoo release protection must guard the optional RevenueScript "
            "attribute before reading it"
        )
    goto_start = capture.index("function Restore_Hooligan_Goto_Zoo")
    goto_end = capture.index("function Restore_Begin_Stock_Zoo_Control", goto_start)
    goto = capture[goto_start:goto_end]
    prearrival_guard = goto.find("if ( $IsHidden ( thisagent ) == FALSE )")
    abandonment = goto.find('owner\'s "Target" != thisagent')
    hidden_arrival = goto.find("if ( $IsHidden ( thisagent ))")
    if not (0 <= prearrival_guard < abandonment < hidden_arrival):
        errors.append(
            "Zoo owner abandonment must apply only before stock Hide completes; "
            "hidden arrival must retain delivery priority"
        )
    birth_start = capture.index("function Restore_Zoo_Building_Birth")
    upgrade_complete_start = capture.index("function Restore_Zoo_Upgrade_Complete")
    upgrade_start = capture.index("function Restore_Zoo_Upgrade", upgrade_complete_start + 1)
    captive_death_start = capture.index("function Restore_Captive_Hooligan_Death")
    birth = capture[birth_start:upgrade_complete_start]
    upgrade_complete = capture[upgrade_complete_start:upgrade_start]
    upgrade = capture[upgrade_start:captive_death_start]
    birth_building = birth.find("$Building_Birth ( zoo )")
    birth_refresh = birth.find("$Restore_Refresh_Zoo_Capacity ( zoo )")
    birth_repoint = birth.find(
        'zoo\'s "birthScript2" = $Restore_Zoo_Upgrade_Complete'
    )
    if not (0 <= birth_building < birth_refresh < birth_repoint):
        errors.append(
            "Zoo initial completion must start stock Building_Birth before "
            "capacity refresh and upgrade-callback installation"
        )
    if "#ATTRIB_FirstStageBuilt" in birth:
        errors.append(
            "Zoo initial completion must not skip Building_Birth after the stock "
            "completion flag has already been set"
        )
    complete_stage = upgrade_complete.find("#ATTRIB_CurrentStageBuilt")
    complete_poll = upgrade_complete.find(
        'zoo\'s "birthScript2", #palace_upgrade_check, zoo'
    )
    complete_repoint = upgrade_complete.find(
        'zoo\'s "birthScript2" = $Restore_Zoo_Upgrade_Complete'
    )
    complete_refresh = upgrade_complete.find("$Restore_Refresh_Zoo_Capacity ( zoo )")
    if not (
        0 <= complete_stage < complete_poll < complete_repoint < complete_refresh
    ):
        errors.append(
            "Zoo upgrade completion must preserve palace_upgrade2 polling before "
            "restoring its callback and refreshing capacity"
        )
    upgrade_basic = upgrade.find("$basic_upgrade ( zoo )")
    upgrade_repoint = upgrade.find(
        'zoo\'s "birthScript2" = $Restore_Zoo_Upgrade_Complete'
    )
    upgrade_poll = upgrade.find(
        'zoo\'s "birthScript2", #palace_upgrade_check, zoo'
    )
    if not (0 <= upgrade_basic < upgrade_repoint < upgrade_poll):
        errors.append(
            "Zoo upgrade must queue stock basic_upgrade before installing and "
            "scheduling its completion callback"
        )
    stock_check_start = capture.index("function Restore_Stock_Zoo_Flag_Check")
    stock_check = capture[stock_check_start:]
    for snippet in (
        "zoo_agent = $NullAgent ()",
        '$ListObjects ( thisagent, "RewardFlag", -1, flags, #RewardFlags )',
        'zoo_agent = flag',
        "$Restore_Find_Completed_Zoo ( zoo_agent )",
        "$Restore_Begin_Stock_Zoo_Control (",
    ):
        if snippet not in stock_check:
            errors.append(f"Active stock Zoo success handoff is missing: {snippet}")
    callback_start = capture.index("function Restore_Capture_Flag_Death_Callback")
    callback_end = capture.index("function Restore_Capture_Flag_Death", callback_start + 1)
    callback = capture[callback_start:callback_end]
    if callback.count("$DeleteGamePiece ( thisagent )") != 1:
        errors.append("Capture overlay callback must literally delete the abandoned Zoo flag")
    if "$Restore_Stock_Zoo_Flag_Check" in callback or "$IsDead" in callback:
        errors.append("Capture must run from monster_gravestone, not the late overlay callback")
    gravestone_start = capture.index("function monster_gravestone")
    gravestone_end = capture.index("function Restore_Capture_Flag_Birth", gravestone_start)
    gravestone = capture[gravestone_start:gravestone_end]
    grave_stop = gravestone.find("$StopMoving ( thisagent )")
    grave_check = gravestone.find("$Restore_Stock_Zoo_Flag_Check ( thisagent )")
    grave_gold = gravestone.find("$DropGoldInRadius (")
    grave_dead = gravestone.find('thisagent\'s "Type" = "Dead"')
    grave_action = gravestone.find('$PerformAction ( thisagent, "basic_death", thisagent )')
    if not (0 <= grave_stop < grave_check < grave_gold < grave_dead < grave_action):
        errors.append("Monster gravestone must preserve the stock Zoo gate and death-tail ordering")
    forbidden_capture_contract = (
        "function monster_birth",
        "function Restore_Get_Attached_Capture_Flag",
        "function Restore_Get_Capture_Flag",
        "function Restore_Continue_Original_Monster_Death",
        "function Restore_Capture_Target_Death",
        'target\'s "IGDeathScript" = $Restore_Capture_Target_Death',
        '"Capture_Birth"',
        '"Capture_TargetID"',
        '"Capture_Target"',
        '"Capture_Zoo"',
        '"Capture_Ready"',
        '"Capture_Check"',
        '"Capture_Roll"',
        '"Capture_Hero"',
        'thisagent\'s "zoo_agent"',
        'target\'s "zoo_agent"',
        '"charm_percentage"',
        "Restore_Zoo_Get_Completed_Zoo",
        "CreateEffector",
        "TEMPORARY ROLLBACK LOAD PROBE",
        "$ListPalaces (",
        "$Hooligan_Goto_Palace",
        "$Hooligan_Check (",
        "$Is_Free_Task (",
        "function Restore_Is_Free_Hooligan_Task",
        "$SetAttribute ( thisagent, #ATTRIB_Speed",
        "function Restore_Hooligan_Check",
        "function Restore_Install_Hooligan_Check",
        "function Restore_Hooligan_Hero_Check",
        '"QuestScript"',
        'thisagent\'s "StartingScript" = thisagent\'s "QuestScript"',
        'thisagent\'s "BasicScript" = thisagent\'s "QuestScript"',
        'thisagent\'s "ActiveScript" = thisagent\'s "QuestScript"',
        'thisagent\'s "BackScript" = thisagent\'s "QuestScript"',
        "function attack_flag_birth",
        "function Restore_Latch_Hooligan_To_Hero",
        "#restore_zoo_flag_radius",
        "$ListSubtypesInRadius (",
    )
    for snippet in forbidden_capture_contract:
        if snippet in capture:
            errors.append(f"Isolated Hooligan diagnostic still contains: {snippet}")
    tame_cost_start = capture.index("function Restore_Zoo_Tame_Cost")
    tame_action_start = capture.index("function Restore_Zoo_Tame_Beast")
    tame_action_end = capture.index("function Restore_Zoo_Revenue")
    tame_cost = capture[tame_cost_start:tame_action_start]
    tame_action = capture[tame_action_start:tame_action_end]
    if "return $Restore_Zoo_Threat_Rank ( visitor ) * 500" not in tame_cost:
        errors.append("Tame Beast cost must remain 500 gold per Threat Rank")
    if 'visitor\'s "Original_Type" != "Monster"' not in tame_cost:
        errors.append("Tame Beast cost must reject a transient hero visitor")
    tame_order = tuple(
        tame_action.find(snippet)
        for snippet in (
            "$GetBuildingContainer ( thisagent )",
            "$Restore_Zoo_Is_Stored_Captive ( thisagent, zoo ) == FALSE",
            "$ClearEngineDeathFlags ( thisagent )",
            '$KillThread ( thisagent\'s "ActiveScript" )',
            'zoo\'s "Occupants" -= thisagent',
            "$Unhide ( thisagent )",
            'thisagent\'s "Type" = "Hero"',
            'thisagent\'s "EnemyType" = "Monster"',
            'thisagent\'s "Guardian_Mod" = 5',
            "#ATTRIB_SightRange ) < 250",
            "$SetAttribute ( thisagent, #ATTRIB_SightRange, 250 )",
            "palace = $GetTruePalace ( zoo )",
            'thisagent\'s "coord_home" = $LocationOf ( palace )',
            'thisagent\'s "coord_home" = $LocationOf ( zoo )',
            'thisagent\'s "BasicScript" = $Guardian',
            'thisagent\'s "BackScript" = $Guardian',
            'thisagent\'s "ActiveScript" = $Guardian',
            "$NewThread ( thisagent's \"ActiveScript\", #Normal_Cycle, thisagent )",
            "$Restore_Refresh_Zoo_Capacity ( zoo )",
        )
    )
    if -1 in tame_order or tame_order != tuple(sorted(tame_order)):
        errors.append(
            "Tame Beast must preserve the Mausoleum removal/start ordering and "
            "stock controlled-monster Guardian state"
        )
    rental_check_start = capture.index("function Restore_Zoo_Rental_Check")
    rental_start = capture.index("function Restore_Zoo_Start_Rented_Beast")
    rental_complete_start = capture.index("function Restore_Zoo_Complete_Rental")
    rental_finish_start = capture.index("function Restore_Zoo_Finish_Rental")
    rental_visit_start = capture.index("function Restore_Zoo_Visited")
    tame_action_start = capture.index("function Restore_Zoo_Tame_Beast")
    rental_check = capture[rental_check_start:rental_start]
    rental_release = capture[rental_start:rental_complete_start]
    rental_complete = capture[rental_complete_start:rental_finish_start]
    rental_finish = capture[rental_finish_start:rental_visit_start]
    rental_visit = capture[rental_visit_start:tame_action_start]
    rental_check_order = tuple(
        rental_check.find(snippet)
        for snippet in (
            'thisagent\'s "Num_Followers" > 0',
            "$RandomNumber ( 100 ) + 1 >= #Percent_Chance_To_Buy_Stats",
            '#MyPlayer, #CheckTitles, "Zoo", #ATTRIB_FirstStageBuilt, 1',
            "#ATTRIB_EmbassyActiveFlag",
            "$Restore_Zoo_Find_Rentable_Captive (",
            '$Loyalty_Mod_Pick_Closest (',
            'thisagent\'s "TaskName" = "Rent_Beast"',
            "$SpecifyIntent ( thisagent, #intent_renting_beast )",
        )
    )
    if -1 in rental_check_order or rental_check_order != tuple(
        sorted(rental_check_order)
    ):
        errors.append(
            "Rental shopping must preserve the stock chance/search/selection/task order"
        )
    rental_release_order = tuple(
        rental_release.find(snippet)
        for snippet in (
            "$ClearEngineDeathFlags ( captive )",
            '$KillThread ( captive\'s "ActiveScript" )',
            'zoo\'s "Occupants" -= captive',
            "$Unhide ( captive )",
            "#ATTRIB_MaxHP",
            "$Control_Monster ( buyer, captive )",
            '$NewThread ( captive\'s "ActiveScript", #Normal_Cycle, captive )',
            "$Restore_Refresh_Zoo_Capacity ( zoo )",
        )
    )
    if -1 in rental_release_order or rental_release_order != tuple(
        sorted(rental_release_order)
    ):
        errors.append(
            "Rented beasts must leave storage through Mausoleum ordering before "
            "stock Control_Monster and a fresh active thread"
        )
    rental_complete_order = tuple(
        rental_complete.find(snippet)
        for snippet in (
            "#ATTRIB_EmbassyActiveFlag",
            'thisagent\'s "Num_Followers" == 0',
            "$Restore_Zoo_Find_Rentable_Captive (",
            "$Total_Gold ( thisagent ) >= cost",
            "$Spend_Gold ( thisagent, zoo, cost )",
            "$Restore_Zoo_Start_Rented_Beast (",
            'thisagent\'s "ActiveScript" = $Restore_Zoo_Finish_Rental',
        )
    )
    if -1 in rental_complete_order or rental_complete_order != tuple(
        sorted(rental_complete_order)
    ):
        errors.append(
            "Rental completion must revalidate before stock hero payment and release"
        )
    if not (
        rental_finish.find("$Exit_Building ( thisagent, zoo )")
        < rental_finish.find("$Restore_Refresh_Zoo_Capacity ( zoo )")
    ):
        errors.append("Rental finish must exit the hero before refreshing Zoo capacity")
    rental_visit_order = tuple(
        rental_visit.find(snippet)
        for snippet in (
            'thisagent\'s "TaskName" == "Rent_Beast"',
            "$Enter_Building ( thisagent, thisagent's \"Target\" )",
            "#Upgrade_Equipment_Visit_Duration",
            'thisagent\'s "ActiveScript" = $Restore_Zoo_Complete_Rental',
            "$Upgrade_Equipment ( thisagent )",
        )
    )
    if -1 in rental_visit_order or rental_visit_order != tuple(
        sorted(rental_visit_order)
    ):
        errors.append(
            "Zoo visits must use the stock equipment duration for rentals and "
            "retain the abandoned fallback"
        )
    if "$ListSize ( visitors ) +" in capture:
        errors.append(
            "Zoo capacity must exclude heroes temporarily registered by Use_Building"
        )
    if "upgradescript2" in gpl:
        errors.append(
            "Generic Building does not declare upgradescript2; Zoo upgrade polling must use its declared completion slot"
        )
    if "$DeleteGamePiece ( target )" in capture:
        errors.append("Capture lifecycle must store successful monsters, not delete them")
    storage_enter = capture.index("$Enter_Building ( thisagent, zoo )")
    storage_intent = capture.index(
        "$SpecifyIntent ( thisagent, #intent_waiting_in_zoo )"
    )
    storage_interval = capture.index(
        'thisagent\'s "ActiveScript", #Restore_Zoo_Breakout_Period'
    )
    storage_basic = capture.index(
        'thisagent\'s "BasicScript" = $Restore_Zoo_Breakout_Check'
    )
    storage_back = capture.index(
        'thisagent\'s "BackScript" = $Restore_Zoo_Breakout_Check'
    )
    storage_breakout = capture.index(
        'thisagent\'s "ActiveScript" = $Restore_Zoo_Breakout_Check'
    )
    hidden_arrival = capture.index("if ( $IsHidden ( thisagent ))")
    final_capacity = capture.index(
        "if ( $Restore_Zoo_Captive_Count ( zoo ) >= limit )"
    )
    owner_reset = capture.index("$Reset_Tasks ( owner )", storage_enter)
    if not (
        hidden_arrival
        < final_capacity
        < storage_enter
        < owner_reset
        < storage_intent
        < storage_interval
        < storage_basic
        < storage_back
        < storage_breakout
    ):
        errors.append(
            "Zoo storage must final-check capacity, enter, release its owner, "
            "set occupant intent, delay the first check, then seal every task "
            "pointer into the periodic breakout lifecycle"
        )
    release_captive_start = capture.index("function Restore_Zoo_Release_Captive")
    breakout_start = capture.index("function Restore_Zoo_Breakout_Check")
    release_occupants_start = capture.index("function release_occupants")
    release_captive = capture[release_captive_start:breakout_start]
    release_reset = release_captive.find("$Reset_Controlled ( captive )")
    release_exit = release_captive.find("$Exit_Building ( captive, zoo )")
    if not (0 <= release_reset < release_exit):
        errors.append(
            "Zoo release must restore stock monster control before exiting the building"
        )
    breakout = capture[breakout_start:release_occupants_start]
    breakout_container = breakout.find("$GetBuildingContainer ( thisagent )")
    breakout_roll = breakout.find("$RandomNumber ( 100 ) + 1")
    breakout_release = breakout.find(
        "$Restore_Zoo_Release_Captive ( thisagent, zoo )"
    )
    breakout_refresh = breakout.find("$Restore_Refresh_Zoo_Capacity ( zoo )")
    if not (
        0 <= breakout_container < breakout_roll < breakout_release < breakout_refresh
    ):
        errors.append(
            "Zoo breakout must preserve the stock garrison container, random-roll, "
            "exit, and capacity-refresh order"
        )

    project = (root / "GPL" / "RestoreAbandonedZoo.gplproj").read_text(
        encoding="utf-8"
    )
    if 'source="RestoreAbandonedZoo_Capture.gpl"' not in project:
        errors.append("GPL project does not compile the Zoo capture bridge")
    if 'data="RestoreAbandonedZoo_Flag_Data.dat"' not in project:
        errors.append("GPL project does not compile the private Capture Flag")
    if 'source="RestoreAbandonedZoo_DealDemon_Test.gpl"' not in project:
        errors.append("GPL project does not compile the Deal Demon test fixture")
    if gpl.count("(IGdeathscript building_death)") != 3:
        errors.append("All three Zoo levels must retain stock building_death")

    deal_demon = (
        root / "GPL" / "RestoreAbandonedZoo_DealDemon_Test.gpl"
    ).read_text(encoding="utf-8")
    required_deal_demon_contract = (
        "function DEAL_DEMON()",
        'AIRootAgent\'s "Quest_Number" = #QNumber_Deal_Demon',
        "palaces = $ListPalaces()",
        "palace = $listmember(palaces,1)",
        'treasury_gold = $GetPlayerData ( palace, "gold" )',
        '$AdjustPlayerData ( palace, "gold", 90000 - treasury_gold )',
        '$SpawnUnit (Palace, "Restore_Zoo1", "MaxHP", $RandomCoord (Palace, 200) )',
        "$Setup_Quest_Music (AiRootAgent)",
        "$setup_random_treasure(30, #default_spawn_treasure_dist)",
        'AIRootAgent\'s "VictoryCondition" = $Demon_victory',
        'AIRootAgent\'s "VictoryCondition2" = $Demon_victory2',
    )
    for snippet in required_deal_demon_contract:
        if snippet not in deal_demon:
            errors.append(f"Deal Demon stock-clone fixture is missing: {snippet}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Restore Abandoned Zoo")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
