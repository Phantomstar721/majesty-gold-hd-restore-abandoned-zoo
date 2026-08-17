from __future__ import annotations

import argparse
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


MAGIC = b"CYLBPC  \x01\x00\x01\x00"


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
    """Return every state TILE from one stock CUR1 cursor set."""
    set_count = struct.unpack_from("<I", imag, 20)[0]
    for set_index in range(set_count):
        current_id, set_offset = struct.unpack_from("<II", imag, 24 + set_index * 8)
        if current_id != set_id:
            continue
        direction_count = struct.unpack_from("<I", imag, set_offset)[0]
        if direction_count <= 0 or direction_count > 32:
            raise ValueError(f"Tactical cursor set {set_id} has invalid states")
        result: list[int] = []
        for direction in range(direction_count):
            relative = struct.unpack_from(
                "<i", imag, set_offset + 64 + direction * 4
            )[0]
            direction_offset = set_offset + relative + 4
            result.append(
                struct.unpack_from("<I", imag, direction_offset + 40)[0] & 0xFFFF
            )
        return result
    raise ValueError(f"Tactical cursor IMAG has no set {set_id}")


def single_direction_imag_tile_indices(imag: bytes) -> list[int]:
    """Return every TILE reached by the stock one-direction overlay layout."""
    if len(imag) < 24:
        raise ValueError("Overlay IMAG is truncated")
    set_count = struct.unpack_from("<I", imag, 20)[0]
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Overlay IMAG has an invalid set table")
    result: list[int] = []
    for set_index in range(set_count):
        _set_id, set_offset = struct.unpack_from("<II", imag, 24 + set_index * 8)
        direction_count = struct.unpack_from("<I", imag, set_offset)[0]
        if direction_count <= 0 or direction_count > 32:
            raise ValueError("Overlay IMAG has an invalid direction count")
        for direction in range(direction_count):
            relative = struct.unpack_from("<i", imag, set_offset + 64 + direction * 4)[0]
            direction_offset = set_offset + relative + 4
            frame_count = struct.unpack_from("<I", imag, direction_offset)[0] >> 16
            if frame_count <= 0 or frame_count > 64:
                raise ValueError("Overlay IMAG has an invalid frame count")
            for frame in range(frame_count):
                encoded = struct.unpack_from(
                    "<I", imag, direction_offset + 24 + frame * 8
                )[0]
                result.append(encoded & 0xFFFF)
    return result


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
        "Data/restore_zoo_units.xml",
        "Data/restore_zoo_maindata.cam",
        "Data/restore_zoo_capture_flag_maindata.cam",
        "Data/restore_zoo_interfacedata.cam",
        "Data/restore_zoo_rewards_interfacedata.cam",
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
            "Data\\restore_zoo_capture_flag_maindata.cam",
            "Data\\restore_zoo_maindata.cam",
            "Data\\restore_zoo_interfacedata.cam",
            "Data\\restore_zoo_rewards_interfacedata.cam",
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
        (b"STRT", b"MX09"),
        (b"STRT", b"ZC01"),
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
    if zoo_menu[0x08A8:0x08AC] != struct.pack("<I", 0x1389):
        errors.append("Zoo Place Reward control must dispatch the stock Palace REWARDS command")
    if len(zoo_menu) != 2504:
        errors.append("Zoo panel must restore AP02's complete Visitors control")
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
    art_names = cam_names(root / "Data" / "restore_zoo_maindata.cam")
    image_names = {name for extension, name in art_names if extension == b"IMAG"}
    for prefix in (b"ABn1", b"ABn2", b"ABn3"):
        if sum(name.startswith(prefix) for name in image_names) != 1:
            errors.append(f"Zoo main-data CAM lacks one stock {prefix.decode()} IMAG record")
    if not any(extension == b"TILE" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the positional stock TILE table")
    if not any(extension == b"SPLT" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the stock palette table")
    capture_art_path = root / "Data" / "restore_zoo_capture_flag_maindata.cam"
    capture_art_names = cam_names(capture_art_path)
    capture_images = {
        name for extension, name in capture_art_names if extension == b"IMAG"
    }
    if capture_images != {b"ZCA2Capture flag"}:
        errors.append(
            f"Private Capture Flag CAM has unexpected IMAG records: {sorted(capture_images)}"
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
        if any(data for _name, data in capture_tiles[:private_start]):
            errors.append("Private Capture Flag CAM replaces a stock TILE slot")
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
    rewards_interface = root / "Data" / "restore_zoo_rewards_interfacedata.cam"
    rewards_interface_names = cam_names(rewards_interface)
    rewards_interface_images = {
        name for extension, name in rewards_interface_names if extension == b"IMAG"
    }
    rewards_palettes = cam_section_entries(rewards_interface, b"PALT")
    if len(rewards_palettes) != 7 or any(
        not data for _name, data in rewards_palettes
    ):
        errors.append("Zoo rewards interface CAM must carry all seven stock PALT entries")
    if rewards_interface_images != {
        b"ZOBGbuilding dialog",
        b"ZCICItem Icons",
        b"CUR1Tactical Cursor",
    }:
        errors.append(
            f"Zoo rewards interface CAM has unexpected IMAG records: {sorted(rewards_interface_images)}"
        )
    if not any(extension == b"TILE" for extension, _ in rewards_interface_names):
        errors.append("Zoo rewards interface CAM lacks its private positional TILE table")
    else:
        rewards_imag = cam_entry_data(
            rewards_interface, b"IMAG", b"ZOBGbuilding dialog"
        )
        rewards_tiles = cam_section_entries(rewards_interface, b"TILE")
        rewards_tile_index = interface_imag_set_tile_index(rewards_imag, 1019)
        if rewards_tile_index >= len(rewards_tiles):
            errors.append("Private ZOBG set 1019 references a missing TILE")
        else:
            rewards_tile = rewards_tiles[rewards_tile_index][1]
            if len(rewards_tile) < 26 or struct.unpack_from("<H", rewards_tile, 0)[0] != 1:
                errors.append("Private Zoo rewards backing is not a V1 TILE")
            elif struct.unpack_from("<HH", rewards_tile, 2) != (245, 202):
                errors.append("Private Zoo rewards backing is not stock 202x245 geometry")
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
            if set_id != 1032
            for tile_index in tactical_cursor_set_tile_indices(cursor_imag, set_id)
        ]
        capture_cursor_indices = tactical_cursor_set_tile_indices(cursor_imag, 1032)
        all_cursor_indices = stock_cursor_indices + capture_cursor_indices
        if any(
            tile_index >= 2624
            or not rewards_tiles[tile_index][1]
            for tile_index in stock_cursor_indices
        ):
            errors.append("Every stock CUR1 state must retain a populated original TILE")
        elif any(
            tile_index < 2624
            or tile_index >= len(rewards_tiles)
            or not rewards_tiles[tile_index][1]
            for tile_index in capture_cursor_indices
        ):
            errors.append("Private CUR1 set 1032 must reference a nonempty appended TILE")
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
        if any(len(indices) != 3 or len(set(indices)) != 1 for indices in (
            attack_cursor_indices,
            explore_cursor_indices,
            capture_cursor_indices,
        )):
            errors.append("CUR1 cursor states do not share one TILE per cursor set")
        elif attack_cursor_indices != [27, 27, 27]:
            errors.append("Extended CUR1 changed stock Attack cursor TILE 27")
        elif explore_cursor_indices != [26, 26, 26]:
            errors.append("Extended CUR1 changed stock Explore cursor TILE 26")
        elif capture_cursor_indices[0] in {
            attack_cursor_indices[0],
            explore_cursor_indices[0],
        }:
            errors.append("Private Capture cursor reuses a stock cursor TILE")
        else:
            capture_cursor_index = capture_cursor_indices[0]
            capture_cursor_tile = rewards_tiles[capture_cursor_index][1]
            if len(capture_cursor_tile) < 26 or struct.unpack_from(
                "<H", capture_cursor_tile, 0
            )[0] != 3:
                errors.append("Private Zoo Capture cursor is not a V3 TILE")
            elif struct.unpack_from("<HH", capture_cursor_tile, 2) != (40, 39):
                errors.append("Private Zoo Capture cursor changed stock 39x40 geometry")
    help_names = cam_names(root / "Data" / "restore_zoo_gpltext.cam")
    if not {(b"STRT", b"AITX"), (b"STRT", b"HPTX")} <= help_names:
        errors.append("Zoo GPL text CAM lacks STRT/AITX or STRT/HPTX")
    else:
        intent_data = cam_entry_data(
            root / "Data" / "restore_zoo_gpltext.cam", b"STRT", b"AITX"
        )
        intent_record = indexed_strt_record(intent_data, 117)
        if intent_record != (117, "Capturing a monster"):
            errors.append(
                "Intent 117 must change only its text to Capturing a monster"
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
    if gpl.count("(upgradescript Restore_Zoo_Upgrade)") != 3:
        errors.append("Every Zoo level must refresh capacity through the stock upgrade callback")

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
        "function Restore_Zoo_Upgrade",
        "$basic_upgrade ( zoo )",
        "function Restore_Captive_Hooligan_Death",
        "$Hooligan_Death ( thisagent )",
        "function Restore_Find_Available_Zoo",
        '$ListObjects ( thisagent, "building", -1, zoos,',
        '#MyPlayer, #CheckTitles, "Zoo", #ATTRIB_FirstStageBuilt, 1',
        'visitors = zoo\'s "Occupants"',
        '$Restore_Zoo_Pending_Reservations ( zoo )',
        'if ( occupied < limit )',
        'zoo = thisagent\'s "Target"',
        "expression #intent_waiting_in_zoo 199",
        "expression #restore_zoo_flag_radius 300",
        "function Restore_Latch_Hooligan_To_Hero",
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
        "$SpecifyIntent ( hero, #intent_arresting_hooligan )",
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
        "$Enter_Building ( thisagent, zoo )",
        "$SpecifyIntent ( thisagent, #intent_waiting_in_zoo )",
        '$KillThread ( thisagent\'s "ActiveScript" )',
        "$ListObjects ( zoo, \"Hooligan\", -1, hooligans, #NoHiddenMap )",
        "$MessageFlag ( zoo, #message_arrested_all_hooligans )",
        'thisagent\'s "IGDeathScript" = $Restore_Captive_Hooligan_Death',
        "#ATTRIB_NotFlaggable, 1",
        "#ATTRIB_NotSpellTarget, 1",
        '$SetThreadInterval ( thisagent\'s "ActiveScript", #Henchmen_Cycle )',
        '$Restore_Find_Available_Zoo ( thisagent )',
        '#ATTRIB_RewardCost',
        'charm_percentage = 50 * (',
        '$Sqrt (( cash / 20.0 ) / target_strength )',
        'if ( charm_percentage > 95 )',
        '$RandomNumber ( 100 ) + 1',
        '$ListSubtypesInRadius (',
        '#restore_zoo_flag_radius',
        "function Restore_Capture_Flag_Poll",
        "function Restore_Capture_Flag_Death_Callback",
        "function Restore_Capture_Flag_Death",
        "function Restore_Get_Attached_Capture_Flag",
        '"RewardFlag", -1, flags, #RewardFlags',
        'flag\'s "SubType" == "Capture_Flag"',
        "function monster_gravestone",
        'deadflag = TRUE',
        '$Restore_Stock_Zoo_Flag_Check (',
        'thisagent, zoo_agent ) == TRUE',
        'thisagent\'s "Type" = "Dead"',
        'thisagent\'s "ActiveScript" = $be_dead_2',
        '"basic_death", thisagent',
        "function Restore_Stock_Zoo_Flag_Check",
    )
    for snippet in required_capture_contract:
        if snippet not in capture:
            errors.append(f"Zoo capture stock-clone contract is missing: {snippet}")
    stock_check_start = capture.index("function Restore_Stock_Zoo_Flag_Check")
    stock_check = capture[stock_check_start:]
    for snippet in (
        "$Restore_Find_Available_Zoo ( zoo_agent )",
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
    grave_lookup = gravestone.find("$Restore_Get_Attached_Capture_Flag")
    grave_check = gravestone.find("$Restore_Stock_Zoo_Flag_Check (")
    grave_gold = gravestone.find("$DropGoldInRadius (")
    grave_dead = gravestone.find('thisagent\'s "Type" = "Dead"')
    grave_action = gravestone.find('$PerformAction ( thisagent, "basic_death", thisagent )')
    if not (0 <= grave_stop < grave_lookup < grave_check < grave_gold < grave_dead < grave_action):
        errors.append("Monster gravestone must preserve the stock Zoo gate and death-tail ordering")
    forbidden_capture_contract = (
        "function monster_birth",
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
        "ClearEngineDeathFlags",
        "CreateEffector",
        "Resurrect",
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
    )
    for snippet in forbidden_capture_contract:
        if snippet in capture:
            errors.append(f"Isolated Hooligan diagnostic still contains: {snippet}")
    if "$DeleteGamePiece ( target )" in capture:
        errors.append("Capture lifecycle must store successful monsters, not delete them")
    storage_enter = capture.index("$Enter_Building ( thisagent, zoo )")
    storage_intent = capture.index(
        "$SpecifyIntent ( thisagent, #intent_waiting_in_zoo )"
    )
    storage_kill = capture.index('$KillThread ( thisagent\'s "ActiveScript" )')
    hidden_arrival = capture.index("if ( $IsHidden ( thisagent ))")
    if not hidden_arrival < storage_enter < storage_intent < storage_kill:
        errors.append(
            "Zoo storage must enter, set its occupant intent, then stop after arrival"
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
