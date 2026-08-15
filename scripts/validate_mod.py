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
        "Data/restore_zoo_miscdata.cam",
        "Data/restore_zoo_textdata.cam",
        "Data/restore_zoo_gpltext.cam",
        "Data/RestoreAbandonedZoo.bcd",
        "GPL/RestoreAbandonedZoo_Building_Data.dat",
        "GPL/RestoreAbandonedZoo_Capture.gpl",
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
    if [item.get("Name") for item in descriptions] != ["Restore_Zoo1", "Restore_Zoo2", "Restore_Zoo3"]:
        errors.append("Unit XML must define the three private Zoo prototypes in order")
    description_ids = [item.get("ID") for item in descriptions]
    if description_ids != ["ZOO1", "ZOO2", "ZOO3"]:
        errors.append(f"Unexpected private Zoo description IDs: {description_ids}")
    image_ids = [item.find("./Engine/ImageIDBase").get("value") for item in descriptions]
    if image_ids != ["ABn1", "ABn2", "ABn3"]:
        errors.append(f"Unexpected stock Zoo image IDs: {image_ids}")
    if any(item.find("./Game/DialogID").get("value") != "MX09" for item in descriptions):
        errors.append("Every Zoo level must use the stock MX09 panel controller")

    load = manifest.find("./Mod/DataConfiguration/Dataset/Load")
    if load is None:
        errors.append("Manifest load block is missing")
    elif load.find("GPL") is None:
        errors.append("Standalone Zoo GPL load block is missing")
    elif [item.text for item in load.findall("Descriptions")] != [
        "Data\\restore_zoo_units.xml"
    ]:
        errors.append("Manifest must load only the Zoo building descriptions")

    text_names = cam_names(root / "Data" / "restore_zoo_textdata.cam")
    if not {(b"SMNU", b"MX09"), (b"STRT", b"MX09"), (b"STRT", b"UNTN")} <= text_names:
        errors.append(f"Zoo text CAM has unexpected entries: {sorted(text_names)}")
    zoo_menu = cam_entry_data(
        root / "Data" / "restore_zoo_textdata.cam", b"SMNU", b"MX09"
    )
    if len(zoo_menu) != 2488:
        errors.append("Zoo panel must remain the literal stock MX09 payload")
    art_names = cam_names(root / "Data" / "restore_zoo_maindata.cam")
    image_names = {name for extension, name in art_names if extension == b"IMAG"}
    for prefix in (b"ABn1", b"ABn2", b"ABn3"):
        if sum(name.startswith(prefix) for name in image_names) != 1:
            errors.append(f"Zoo main-data CAM lacks one stock {prefix.decode()} IMAG record")
    if not any(extension == b"TILE" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the positional stock TILE table")
    if not any(extension == b"SPLT" for extension, _ in art_names):
        errors.append("Zoo main-data CAM lacks the stock palette table")
    help_names = cam_names(root / "Data" / "restore_zoo_gpltext.cam")
    if not {(b"STRT", b"AITX"), (b"STRT", b"HPTX")} <= help_names:
        errors.append("Zoo GPL text CAM lacks STRT/AITX or STRT/HPTX")
    else:
        intent_record = indexed_strt_record(
            cam_entry_data(
                root / "Data" / "restore_zoo_gpltext.cam", b"STRT", b"AITX"
            ),
            117,
        )
        if intent_record != (117, "Capturing a monster"):
            errors.append(
                "Intent 117 must change only its text to Capturing a monster"
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

    capture = (root / "GPL" / "RestoreAbandonedZoo_Capture.gpl").read_text(
        encoding="utf-8"
    )
    required_capture_contract = (
        "function attack_flag_birth",
        "function Restore_Has_Completed_Zoo",
        '$ListObjects ( thisagent, "building", -1, zoos,',
        '#MyPlayer, #CheckTitles, "Zoo", #ATTRIB_FirstStageBuilt, 1 ) > 0',
        '$Restore_Has_Completed_Zoo ( thisagent )',
        '$ListObjects ( thisagent, "Building", -1, zoos,',
        '#CheckTitles, "Zoo", #ATTRIB_FirstStageBuilt, 1',
        'zoo = $ListMember ( zoos, 1 )',
        "function Restore_Convert_To_Stock_Hooligan",
        "function Restore_Hooligan_Control_Delay",
        "function Restore_Become_Hooligan",
        'thisagent\'s "Counter" * #Normal_Cycle >= #Charm_Delay_Time',
        'thisagent\'s "ActiveScript" = $Restore_Become_Hooligan',
        'thisagent\'s "Type" = "Hidden"',
        '$SetUnitPlayerNumber (',
        'thisagent, $GetUnitPlayerNumber ( flag ))',
        "function Restore_Hooligan_Basic",
        "function Restore_Hooligan_Goto_Zoo",
        "function Restore_Assign_Hooligan",
        "valid_heroes << hero",
        "hero = $ListMember ( valid_heroes, 1 )",
        'thisagent\'s "leader" = hero',
        "$SpecifyIntent ( hero, #intent_arresting_hooligan )",
        'hero\'s "Target" = thisagent',
        'hero\'s "ActiveScript" = $Arrest_Hooligan',
        'hero\'s "ActiveScript" != $Arrest_Hooligan',
        'hero\'s "BackScript" != $Arrest_Hooligan',
        'thisagent\'s "Type" = "Hooligan"',
        'thisagent\'s "ActiveScript" = thisagent\'s "BackScript"',
        'thisagent\'s "BackScript" = $Restore_Hooligan_Basic',
        'thisagent\'s "ActiveScript" = $Restore_Hooligan_Goto_Zoo',
        "$Hide ( thisagent, zoo )",
        'owner = thisagent\'s "leader"',
        'owner\'s "Target" != thisagent',
        'thisagent\'s "Special_Boolean" = FALSE',
        '$Restore_Assign_Hooligan ( thisagent, owner )',
        "$DistanceBetweenAgents ( thisagent, owner ) >",
        "#Arrest_Hooligan_Dist",
        "$StopMoving ( thisagent )",
        "$Reset_Tasks ( owner )",
        "$ListObjects ( zoo, \"Hooligan\", -1, hooligans, #NoHiddenMap )",
        "$MessageFlag ( zoo, #message_arrested_all_hooligans )",
        'thisagent\'s "IGDeathScript" = $Hooligan_Death',
        "#ATTRIB_NotFlaggable, 1",
        "#ATTRIB_NotSpellTarget, 1",
        '$SetThreadInterval ( thisagent\'s "ActiveScript", #Henchmen_Cycle )',
        'target\'s "Type" == "Monster"',
        'target, thisagent',
        "$DeleteGamePiece ( thisagent )",
    )
    for snippet in required_capture_contract:
        if snippet not in capture:
            errors.append(f"Zoo capture stock-clone contract is missing: {snippet}")
    forbidden_capture_contract = (
        "function monster_birth",
        "function monster_gravestone",
        "function Restore_Zoo_Capacity",
        "function Restore_Get_Available_Zoo",
        "Restore_Zoo_Get_Completed_Zoo",
        "ClearEngineDeathFlags",
        "CreateEffector",
        "Resurrect",
        'zoo\'s "Occupants" << thisagent',
        '$KillThread ( thisagent\'s "ActiveScript" )',
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
    )
    for snippet in forbidden_capture_contract:
        if snippet in capture:
            errors.append(f"Isolated Hooligan diagnostic still contains: {snippet}")

    project = (root / "GPL" / "RestoreAbandonedZoo.gplproj").read_text(
        encoding="utf-8"
    )
    if 'source="RestoreAbandonedZoo_Capture.gpl"' not in project:
        errors.append("GPL project does not compile the Zoo capture bridge")
    if gpl.count("(IGdeathscript building_death)") != 3:
        errors.append("All three Zoo levels must retain stock building_death")
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
