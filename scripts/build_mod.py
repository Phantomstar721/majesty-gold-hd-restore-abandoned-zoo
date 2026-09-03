from __future__ import annotations

import argparse
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path


MAGIC = b"CYLBPC  \x01\x00\x01\x00"
HEADER_SIZE = 20
DIR_ENTRY_SIZE = 8
SECTION_HEADER_SIZE = 8
ENTRY_HEADER_SIZE = 28
REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "RestoreAbandonedZoo"
VISITORS_CONTROL_ID = 0x1F55
ZOO_PLACE_REWARD_CONTROL_ID = 0x2293
PALACE_REWARDS_CONTROL_ID = 0x1389
ZOO_REWARDS_DIALOG_ID = b"ZC01"
ZOO_TAME_DIALOG_ID = b"ZT01"
ZOO_TAME_OPEN_COMMAND_ID = 0x2A30
ZOO_REWARDS_BACKGROUND_SOURCE = b"INBgbuilding dialog"
ZOO_REWARDS_BACKGROUND_CUSTOM = b"ZOBGbuilding dialog"
ZOO_REWARDS_BACKGROUND_TOKEN = b"ZOBG"
ZOO_REWARDS_BACKGROUND_SET = 1019
ZOO_TAME_BACKGROUND_SET = 1013
ZOO_REWARDS_TILE = (
    REPO_ROOT / "assets" / "generated" / "interface" / "zoo-rewards-panel.tile"
)
ZOO_CAPTURE_ICON_SOURCE = b"INTCItem Icons"
ZOO_CAPTURE_ICON_CUSTOM = b"ZCICItem Icons"
ZOO_CAPTURE_ICON_TOKEN = b"ZCIC"
ZOO_CAPTURE_ICON_SET = 1011
ZOO_CAPTURE_ICON_SOURCE_TILE = 92
ZOO_CAPTURE_ICON_TILE = (
    REPO_ROOT / "assets" / "generated" / "capture-flag" / "capture-button-icon-25.tile"
)
TACTICAL_CURSOR_IMAGE = b"CUR1Tactical Cursor"
STOCK_ATTACK_CURSOR_SET = 1005
STOCK_EXPLORE_CURSOR_SET = 1006
PRIVATE_CAPTURE_CURSOR_SET = 1038
STOCK_ATTACK_CURSOR_TILE = 27
STOCK_EXPLORE_CURSOR_TILE = 26
ZOO_CAPTURE_CURSOR_TILE = (
    REPO_ROOT / "assets" / "generated" / "capture-flag" / "capture-cursor-40.tile"
)
CAPTURE_FLAG_IMAGE_SOURCE = b"ARA2flag attack"
CAPTURE_FLAG_IMAGE_CUSTOM = b"ZCA2Capture flag"
CAPTURE_FLAG_IMAGE_TOKEN = b"ZCA2"
CAPTURE_FLAG_ART_DIR = REPO_ROOT / "assets" / "generated" / "capture-flag"
CAPTURE_FLAG_SPECIAL_TILES = tuple(range(16655, 16667))
CAPTURE_FLAG_MINIMAP_TILES = tuple(range(16667, 16671))
CAPTURE_FLAG_INTERFACE_TILES = tuple(range(16671, 16675))
CAPTURE_FLAG_PALETTE = 793
AP02_VISITORS_RECORD_START = 0x013C
AP02_VISITORS_RECORD_END = 0x01D4
MX09_VISITORS_RECORD_START = 0x013C
MX09_VISITORS_RECORD_END = 0x01C4
MX09_PLACE_REWARD_COMMAND_OFFSET = 0x0898
AP39_REWARDS_COMMAND_OFFSET = 0x0130
AP41_EXPLORE_CONTROLS = (
    (0x00A0, 0x0118, (0x1388,)),  # Increase Explore reward.
    (0x0118, 0x0190, (0x1389,)),  # Decrease Explore reward.
    (0x0238, 0x02E0, (0x138B,)),  # Place Explore Flag.
    (0x02E0, 0x0380, (0x138C,)),  # Explore reward amount.
    (0x0380, 0x03D4, (0x1B5A,)),  # Explore Flag icon.
)
STOCK_HIDDEN_CONTROL_COORDINATE = 1500
AP41_ATTACK_ICON_CONTROL_START = 0x0660
AP41_ATTACK_ICON_CONTROL_END = 0x06B8
AP10_SECONDARY_CONTROL_START = 0x0D2C
AP10_SECONDARY_CONTROL_END = 0x0DF0
AP10_SECONDARY_CONTROL_RECT = (103, 162, 93, 26)
ZOO_TAME_CONTROL_RECT = (7, 217, 93, 26)
AP10_SECONDARY_LABEL_INDEX_OFFSET = 0x30
AP10_SECONDARY_TOOLTIP_INDEX_OFFSET = 0x38
AP10_SECONDARY_COMMAND_OFFSET = 0x88


@dataclass(frozen=True)
class CamEntry:
    name: bytes
    data: bytes


@dataclass(frozen=True)
class CamSection:
    extension: bytes
    entries: tuple[CamEntry, ...]
    padding: bytes = b"\x00\x00\x00\x00"


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def fourcc_id(value: str) -> int:
    raw = value.encode("ascii")
    if len(raw) != 4:
        raise ValueError(f"Expected a four-character ID, got {value!r}")
    return struct.unpack("<I", raw)[0]


def pad_name(name: bytes) -> bytes:
    if len(name) > 20:
        raise ValueError(f"CAM entry name is too long: {name!r}")
    return name.ljust(20, b"\x00")


def read_cam_entry(path: Path, section_ext: bytes, entry_name: bytes) -> CamEntry:
    data = path.read_bytes()
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError(f"{path} is not a CYLBPC CAM archive")

    cursor = HEADER_SIZE
    sections: list[tuple[bytes, int]] = []
    for _ in range(u32(data, 12)):
        sections.append((data[cursor : cursor + 4], u32(data, cursor + 4)))
        cursor += DIR_ENTRY_SIZE

    for extension, section_offset in sections:
        if extension != section_ext:
            continue
        count = u32(data, section_offset)
        cursor = section_offset + SECTION_HEADER_SIZE
        for _ in range(count):
            raw_name = data[cursor : cursor + 20]
            payload_offset = u32(data, cursor + 20)
            payload_size = u32(data, cursor + 24)
            cursor += ENTRY_HEADER_SIZE
            if raw_name.rstrip(b"\x00") == entry_name:
                return CamEntry(raw_name, data[payload_offset : payload_offset + payload_size])
        break
    raise ValueError(f"Could not find {section_ext!r}/{entry_name!r} in {path}")


def read_cam_entries(path: Path, section_ext: bytes) -> list[CamEntry]:
    data = path.read_bytes()
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError(f"{path} is not a CYLBPC CAM archive")
    cursor = HEADER_SIZE
    for _ in range(u32(data, 12)):
        extension = data[cursor : cursor + 4]
        section_offset = u32(data, cursor + 4)
        cursor += DIR_ENTRY_SIZE
        if extension != section_ext:
            continue
        entries: list[CamEntry] = []
        entry_cursor = section_offset + SECTION_HEADER_SIZE
        for _ in range(u32(data, section_offset)):
            name = data[entry_cursor : entry_cursor + 20]
            offset = u32(data, entry_cursor + 20)
            size = u32(data, entry_cursor + 24)
            entry_cursor += ENTRY_HEADER_SIZE
            entries.append(CamEntry(name, data[offset : offset + size]))
        return entries
    raise ValueError(f"Could not find {section_ext!r} section in {path}")


def require_cam_entry_prefix(path: Path, section_ext: bytes, prefixes: tuple[bytes, ...]) -> None:
    data = path.read_bytes()
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError(f"{path} is not a CYLBPC CAM archive")
    cursor = HEADER_SIZE
    for _ in range(u32(data, 12)):
        extension = data[cursor : cursor + 4]
        section_offset = u32(data, cursor + 4)
        cursor += DIR_ENTRY_SIZE
        if extension != section_ext:
            continue
        found: set[bytes] = set()
        entry_cursor = section_offset + SECTION_HEADER_SIZE
        for _ in range(u32(data, section_offset)):
            name = data[entry_cursor : entry_cursor + 20].rstrip(b"\x00")
            entry_cursor += ENTRY_HEADER_SIZE
            for prefix in prefixes:
                if name.startswith(prefix):
                    found.add(prefix)
        missing = set(prefixes) - found
        if missing:
            raise ValueError(
                f"Stock Zoo art is missing from {path}: "
                + ", ".join(sorted(item.decode("ascii") for item in missing))
            )
        return
    raise ValueError(f"Could not find {section_ext!r} section in {path}")


def write_cam(path: Path, sections: tuple[CamSection, ...]) -> None:
    file_header_size = HEADER_SIZE + len(sections) * DIR_ENTRY_SIZE
    content_header_size = sum(
        SECTION_HEADER_SIZE + len(section.entries) * ENTRY_HEADER_SIZE
        for section in sections
    )
    cursor = file_header_size + content_header_size
    payload_offsets: list[list[int]] = []
    for section in sections:
        offsets: list[int] = []
        for entry in section.entries:
            offsets.append(cursor)
            cursor += len(entry.data)
        payload_offsets.append(offsets)

    output = bytearray(MAGIC)
    output += struct.pack("<II", len(sections), content_header_size)
    section_offset = file_header_size
    for section in sections:
        output += section.extension + struct.pack("<I", section_offset)
        section_offset += SECTION_HEADER_SIZE + len(section.entries) * ENTRY_HEADER_SIZE
    for section_index, section in enumerate(sections):
        output += struct.pack("<I", len(section.entries)) + section.padding
        for entry_index, entry in enumerate(section.entries):
            output += entry.name
            output += struct.pack(
                "<II",
                payload_offsets[section_index][entry_index],
                len(entry.data),
            )
    for section in sections:
        for entry in section.entries:
            output += entry.data
    path.write_bytes(output)


def patch_keyed_strt(data: bytes, replacements: dict[int, str]) -> bytes:
    count = struct.unpack_from("<H", data, 0)[0]
    version = data[2:4]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    records: list[tuple[int, bytes]] = []
    seen: set[int] = set()
    for offset in offsets:
        string_id = u32(data, offset)
        end = data.index(b"\x00", offset + 4)
        text = data[offset + 4 : end]
        if string_id in replacements:
            text = replacements[string_id].encode("cp1252")
            seen.add(string_id)
        records.append((string_id, text))
    for string_id, text in replacements.items():
        if string_id not in seen:
            records.append((string_id, text.encode("cp1252")))
    return encode_strt(version, records)


def patch_indexed_strt(data: bytes, replacements: dict[int, str]) -> bytes:
    count = struct.unpack_from("<H", data, 0)[0]
    version = data[2:4]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    records: list[tuple[int, bytes]] = []
    for index, offset in enumerate(offsets):
        string_id = u32(data, offset)
        end = data.index(b"\x00", offset + 4)
        text = data[offset + 4 : end]
        if index in replacements:
            text = replacements[index].encode("cp1252")
        records.append((string_id, text))
    unknown = sorted(set(replacements) - set(range(count)))
    if unknown:
        raise ValueError(f"STRT replacement indices do not exist: {unknown}")
    return encode_strt(version, records)


def append_indexed_strt(data: bytes, additions: tuple[str, ...]) -> bytes:
    count = struct.unpack_from("<H", data, 0)[0]
    version = data[2:4]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    records: list[tuple[int, bytes]] = []
    for offset in offsets:
        string_id = u32(data, offset)
        end = data.index(b"\x00", offset + 4)
        records.append((string_id, data[offset + 4 : end]))
    next_id = max((string_id for string_id, _text in records), default=-1) + 1
    records.extend(
        (next_id + index, text.encode("cp1252"))
        for index, text in enumerate(additions)
    )
    return encode_strt(version, records)


def encode_strt(version: bytes, records: list[tuple[int, bytes]]) -> bytes:
    output = bytearray(struct.pack("<H", len(records)) + version)
    output += b"\x00\x00\x00\x00" * len(records)
    offsets: list[int] = []
    for string_id, text in records:
        offsets.append(len(output))
        output += struct.pack("<I", string_id) + text + b"\x00"
    for index, offset in enumerate(offsets):
        struct.pack_into("<I", output, 4 + index * 4, offset)
    return bytes(output)


def restore_zoo_visitors_control(zoo_menu: bytes, blacksmith_menu: bytes) -> bytes:
    """Replace MX09's truncated Visitors record with stock AP02's full control."""
    command = struct.pack("<I", VISITORS_CONTROL_ID)
    if zoo_menu.count(command) != 1 or blacksmith_menu.count(command) != 1:
        raise ValueError("Stock Visitors command contract changed")

    abandoned = zoo_menu[MX09_VISITORS_RECORD_START:MX09_VISITORS_RECORD_END]
    stock = blacksmith_menu[AP02_VISITORS_RECORD_START:AP02_VISITORS_RECORD_END]
    if len(abandoned) != 0x88 or abandoned[-4:] != b"\xff" * 4:
        raise ValueError("Abandoned MX09 Visitors record boundary changed")
    if len(stock) != 0x98 or stock[-4:] != b"\xff" * 4:
        raise ValueError("Stock AP02 Visitors control boundary changed")
    if abandoned[:0x84] != stock[:0x84]:
        raise ValueError("MX09 Visitors prefix no longer matches stock AP02")
    if struct.unpack_from("<4I", stock, 0x08) != (32, 162, 139, 26):
        raise ValueError("Stock AP02 Visitors rectangle changed")

    return (
        zoo_menu[:MX09_VISITORS_RECORD_START]
        + stock
        + zoo_menu[MX09_VISITORS_RECORD_END:]
    )


def restore_zoo_reward_dispatch(zoo_menu: bytes, palace_menu: bytes) -> bytes:
    """Give MX09's orphaned reward button AP39's literal REWARDS command."""
    zoo_command = struct.pack("<I", ZOO_PLACE_REWARD_CONTROL_ID)
    palace_command = struct.pack("<I", PALACE_REWARDS_CONTROL_ID)
    if zoo_menu.count(zoo_command) != 1:
        raise ValueError("Stock MX09 Place Reward command contract changed")
    if palace_menu[AP39_REWARDS_COMMAND_OFFSET : AP39_REWARDS_COMMAND_OFFSET + 4] != palace_command:
        raise ValueError("Stock AP39 REWARDS command contract changed")
    if zoo_menu[
        MX09_PLACE_REWARD_COMMAND_OFFSET : MX09_PLACE_REWARD_COMMAND_OFFSET + 4
    ] != zoo_command:
        raise ValueError("Stock MX09 Place Reward command offset changed")

    patched = bytearray(zoo_menu)
    patched[
        MX09_PLACE_REWARD_COMMAND_OFFSET : MX09_PLACE_REWARD_COMMAND_OFFSET + 4
    ] = palace_menu[
        AP39_REWARDS_COMMAND_OFFSET : AP39_REWARDS_COMMAND_OFFSET + 4
    ]
    return bytes(patched)


def add_zoo_tame_control(zoo_menu: bytes, ap10_menu: bytes) -> bytes:
    """Append AP10's complete secondary-panel opener at Brewing's final rect."""
    if zoo_menu[-8:] != b"\xff" * 8:
        raise ValueError("Stock MX09 no longer has its two-word terminal marker")
    source = bytearray(
        ap10_menu[AP10_SECONDARY_CONTROL_START:AP10_SECONDARY_CONTROL_END]
    )
    if len(source) != 0xC4 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock AP10 secondary-panel control boundary changed")
    if struct.unpack_from("<4I", source, 0x08) != AP10_SECONDARY_CONTROL_RECT:
        raise ValueError("Stock AP10 secondary-panel rectangle changed")
    if u32(source, AP10_SECONDARY_COMMAND_OFFSET) != 0x1F49:
        raise ValueError("Stock AP10 secondary-panel command changed")
    if zoo_menu.count(struct.pack("<I", ZOO_TAME_OPEN_COMMAND_ID)):
        raise ValueError("Stock MX09 unexpectedly contains the private Tame command")

    struct.pack_into("<4I", source, 0x08, *ZOO_TAME_CONTROL_RECT)
    struct.pack_into("<I", source, AP10_SECONDARY_LABEL_INDEX_OFFSET, 26)
    struct.pack_into("<I", source, AP10_SECONDARY_TOOLTIP_INDEX_OFFSET, 27)
    struct.pack_into(
        "<I", source, AP10_SECONDARY_COMMAND_OFFSET, ZOO_TAME_OPEN_COMMAND_ID
    )
    # The first of MX09's final two FFFFFFFF words terminates its last real
    # control; only the second is the stream terminator. Preserve the former
    # in place and insert the complete AP10 record before the latter.
    return zoo_menu[:-4] + bytes(source) + zoo_menu[-4:]


def privatize_zoo_tame_menu(mausoleum_menu: bytes) -> bytes:
    """Clone MX05's selected-occupant action panel with Zoo backing art."""
    if mausoleum_menu[-8:] != b"\xff" * 8:
        raise ValueError("Stock MX05 no longer has its two-word terminal marker")
    if mausoleum_menu.count(b"INBg") != 2:
        raise ValueError("Stock MX05 no longer has exactly two INBg references")
    if mausoleum_menu.count(struct.pack("<I", 0x1388)) != 1:
        raise ValueError("Stock MX05 occupant-list control changed")
    if mausoleum_menu.count(struct.pack("<I", 0x138B)) != 1:
        raise ValueError("Stock MX05 selected-action control changed")
    if mausoleum_menu.count(struct.pack("<I", 0x1F46)) != 1:
        raise ValueError("Stock MX05 selected-cost control changed")
    return mausoleum_menu.replace(b"INBg", ZOO_REWARDS_BACKGROUND_TOKEN)


def privatize_zoo_rewards_menu(palace_rewards_menu: bytes) -> bytes:
    """Clone AP41 and move its Explore controls to stock's hidden position."""
    if palace_rewards_menu.count(b"INBg") != 1:
        raise ValueError("Stock AP41 no longer contains exactly one INBg background token")
    if ZOO_REWARDS_BACKGROUND_TOKEN in palace_rewards_menu:
        raise ValueError("Stock AP41 unexpectedly already contains the Zoo background token")
    if ZOO_CAPTURE_ICON_TOKEN in palace_rewards_menu:
        raise ValueError("Stock AP41 unexpectedly already contains the Zoo Capture icon token")
    patched = bytearray(palace_rewards_menu)
    for start, end, command_ids in AP41_EXPLORE_CONTROLS:
        control = palace_rewards_menu[start:end]
        if not control.endswith(b"\xff" * 4):
            raise ValueError(f"Stock AP41 control boundary changed at {start:#x}")
        for command_id in command_ids:
            if control.count(struct.pack("<I", command_id)) != 1:
                raise ValueError(
                    f"Stock AP41 command {command_id:#x} changed at {start:#x}"
                )
        struct.pack_into(
            "<II",
            patched,
            start + 8,
            STOCK_HIDDEN_CONTROL_COORDINATE,
            STOCK_HIDDEN_CONTROL_COORDINATE,
        )
    patched = patched.replace(b"INBg", ZOO_REWARDS_BACKGROUND_TOKEN, 1)
    attack_icon = palace_rewards_menu[
        AP41_ATTACK_ICON_CONTROL_START:AP41_ATTACK_ICON_CONTROL_END
    ]
    if attack_icon.count(struct.pack("<I", 0x1B59)) != 1:
        raise ValueError("Stock AP41 Attack icon command changed")
    if attack_icon.count(b"INTC") != 1:
        raise ValueError("Stock AP41 Attack icon no longer selects one INTC resource")
    private_attack_icon = attack_icon.replace(b"INTC", ZOO_CAPTURE_ICON_TOKEN, 1)
    patched[
        AP41_ATTACK_ICON_CONTROL_START:AP41_ATTACK_ICON_CONTROL_END
    ] = private_attack_icon
    return bytes(patched)


def write_text_cams(game_path: Path, data_dir: Path) -> None:
    base_textdata = game_path / "Data" / "textdata.cam"
    expansion_textdata = game_path / "DataMX" / "mx_textdata.cam"
    gpltext = game_path / "DataMX" / "mx_gpltext.cam"
    stock_menu = read_cam_entry(expansion_textdata, b"SMNU", b"MX09")
    stock_blacksmith_menu = read_cam_entry(base_textdata, b"SMNU", b"AP02")
    stock_palace_menu = read_cam_entry(base_textdata, b"SMNU", b"AP39")
    stock_palace_rewards_menu = read_cam_entry(base_textdata, b"SMNU", b"AP41")
    stock_ap10_menu = read_cam_entry(base_textdata, b"SMNU", b"AP10")
    stock_mausoleum_action_menu = read_cam_entry(
        expansion_textdata, b"SMNU", b"MX05"
    )
    stock_mausoleum_action_strings = read_cam_entry(
        expansion_textdata, b"STRT", b"MX05"
    )
    stock_palace_rewards_strings = read_cam_entry(base_textdata, b"STRT", b"AP41")
    stock_strings = read_cam_entry(expansion_textdata, b"STRT", b"MX09")
    unit_names = read_cam_entry(base_textdata, b"STRT", b"UNTN")
    advisor_text = read_cam_entry(gpltext, b"STRT", b"AITX")
    help_text = read_cam_entry(gpltext, b"STRT", b"HPTX")

    patched_strings = append_indexed_strt(
        patch_indexed_strt(
            stock_strings.data,
            {
                0: "A completed Zoo makes Capture Flags on living monsters trigger the stock Hooligan return lifecycle.",
                4: "Destroy this Zoo.",
            },
        ),
        (
            "TAME BEAST",
            "Open the Zoo's Tame Beast panel.",
        ),
    )
    zoo_rewards_strings = patch_indexed_strt(
        stock_palace_rewards_strings.data,
        {
            2: "Capture Flag",
            3: "Place a Capture Flag.",
            9: "Current Capture Flag default reward amount in gold",
            10: "Capture",
            11: "Decrease Capture Flag reward amount.",
            12: "Increase Capture Flag reward amount.",
            13: "Return to the Zoo's Main Window.",
        },
    )
    zoo_tame_strings = patch_indexed_strt(
        stock_mausoleum_action_strings.data,
        {
            0: "Captured monsters available for taming.",
            1: "ZOO",
            2: "Return to the Zoo's Main Window.",
            5: "Zoom the Main Map to the selected monster.",
            6: "CAPTURED MONSTERS",
            7: "TAME BEAST",
            8: "Release the selected monster to guard your kingdom.",
            9: "500",
            10: "Cost to tame the selected monster",
        },
    )
    patched_names = patch_keyed_strt(
        unit_names.data,
        {
            fourcc_id("ZOO1"): "Zoo",
            fourcc_id("ZOO2"): "Zoo",
            fourcc_id("ZOO3"): "Zoo",
        },
    )
    patched_help = patch_keyed_strt(
        help_text.data,
        {
            fourcc_id("hZ01"): (
                "- Restored civic building\n\n"
                "- May be upgraded twice\n\n"
                "- Enables Attack Flags to turn living monsters into stock Hooligans\n\n\n"
                "\x01BCBCFFThese long-abandoned grounds hint at an unfinished royal plan to exhibit Ardania's creatures."
            ),
            fourcc_id("hZ02"): (
                "- Second-level Zoo\n\n"
                "- Increased building hit points\n\n"
                "- May be upgraded once more"
            ),
            fourcc_id("hZ03"): (
                "- Third-level Zoo\n\n"
                "- Maximum building hit points"
            ),
        },
    )
    patched_advisor_text = patch_indexed_strt(
        advisor_text.data,
        {
            198: "Capturing a monster",
            199: "waiting in the zoo",
        },
    )

    write_cam(
        data_dir / "restore_zoo_textdata.cam",
        (
            CamSection(
                b"SMNU",
                (
                    CamEntry(
                        pad_name(b"MX09"),
                        add_zoo_tame_control(
                            restore_zoo_visitors_control(
                                restore_zoo_reward_dispatch(
                                    stock_menu.data, stock_palace_menu.data
                                ),
                                stock_blacksmith_menu.data,
                            ),
                            stock_ap10_menu.data,
                        ),
                    ),
                    CamEntry(
                        pad_name(ZOO_REWARDS_DIALOG_ID),
                        privatize_zoo_rewards_menu(stock_palace_rewards_menu.data),
                    ),
                    CamEntry(
                        pad_name(ZOO_TAME_DIALOG_ID),
                        privatize_zoo_tame_menu(stock_mausoleum_action_menu.data),
                    ),
                ),
            ),
            CamSection(
                b"STRT",
                (
                    CamEntry(pad_name(b"UNTN"), patched_names),
                    CamEntry(pad_name(b"MX09"), patched_strings),
                    CamEntry(
                        pad_name(ZOO_REWARDS_DIALOG_ID), zoo_rewards_strings
                    ),
                    CamEntry(pad_name(ZOO_TAME_DIALOG_ID), zoo_tame_strings),
                ),
            ),
        ),
    )
    write_cam(
        data_dir / "restore_zoo_gpltext.cam",
        (
            CamSection(
                b"STRT",
                (
                    CamEntry(pad_name(b"AITX"), patched_advisor_text),
                    CamEntry(pad_name(b"HPTX"), patched_help),
                ),
            ),
        ),
    )


def write_miscdata_cam(game_path: Path, data_dir: Path) -> None:
    # Majesty resolves DATA/BDEP as one complete resource; separate mod copies
    # do not merge. Use the same base stock source as the proven Haunt package
    # and include the known local custom-building rules in one payload.
    source = game_path / "Data" / "miscdata.cam"
    stock_bdep = read_cam_entry(source, b"DATA", b"BDEP").data
    additions = (
        b"# Restored Zoo levels use the stock Blacksmith no-prerequisite form\r\n"
        b"ZOO1\r\n"
        b"ZOO2\r\n"
        b"ZOO3\r\n"
    )
    if not stock_bdep.endswith(b"\r\n"):
        raise ValueError(f"Stock BDEP has an unexpected line ending: {source}")
    custom_ids = (b"ZOO1", b"ZOO2", b"ZOO3")
    if any(line.split(b" ", 1)[0] in custom_ids for line in stock_bdep.splitlines()):
        raise ValueError("Stock BDEP unexpectedly already defines a local custom building")
    patched_bdep = stock_bdep + b"\r\n" + additions
    write_cam(
        data_dir / "restore_zoo_miscdata.cam",
        (CamSection(b"DATA", (CamEntry(pad_name(b"BDEP"), patched_bdep),)),),
    )


def write_maindata_cam(game_path: Path, data_dir: Path) -> None:
    """Package the literal expansion Zoo art through stock positional CAM tables.

    TILE entries are addressed by their section position, so retain the entire
    stock MX TILE and palette tables exactly, as the proven Haunt package does.
    Only the three abandoned Zoo IMAG records are exposed by this mod.
    """
    source = game_path / "DataMX" / "mx_maindata.cam"
    images = read_cam_entries(source, b"IMAG")
    zoo_prefixes = (b"ABn1", b"ABn2", b"ABn3")
    zoo_images = tuple(
        entry
        for prefix in zoo_prefixes
        for entry in images
        if entry.name.rstrip(b"\x00").startswith(prefix)
    )
    if len(zoo_images) != 3:
        raise ValueError(f"Expected three stock Zoo IMAG records in {source}, found {len(zoo_images)}")
    tiles = tuple(read_cam_entries(source, b"TILE"))
    palettes = tuple(read_cam_entries(source, b"SPLT"))
    if not tiles or not palettes:
        raise ValueError(f"Stock Zoo art tables are incomplete in {source}")
    write_cam(
        data_dir / "restore_zoo_maindata.cam",
        (
            CamSection(b"IMAG", zoo_images),
            CamSection(b"TILE", tiles, padding=b"\x01\x00\x00\x00"),
            CamSection(b"SPLT", palettes),
        ),
    )


def write_capture_flag_maindata_cam(game_path: Path, data_dir: Path) -> None:
    """Package a private art clone of stock ARA2 for Restore_Capture_Flag.

    The IMAG animation topology remains the literal stock Attack Flag layout:
    twelve Special frames, four Minimap frames, and four player-color Interface
    directions.  Every reached TILE is redirected to an appended private slot,
    so neither ARA2 nor ARA4 can be visually replaced by this mod.
    """
    source = game_path / "Data" / "maindata.cam"
    stock_imag = read_cam_entry(source, b"IMAG", CAPTURE_FLAG_IMAGE_SOURCE).data
    tiles = read_cam_entries(source, b"TILE")
    palettes = read_cam_entries(source, b"SPLT")
    if len(tiles) <= CAPTURE_FLAG_INTERFACE_TILES[-1]:
        raise ValueError(f"Stock Capture Flag source TILE table is incomplete in {source}")
    if len(palettes) <= CAPTURE_FLAG_PALETTE:
        raise ValueError(f"Stock Capture Flag palette table is incomplete in {source}")

    groups = (
        (CAPTURE_FLAG_SPECIAL_TILES, "special", 3),
        (CAPTURE_FLAG_MINIMAP_TILES, "minimap", 3),
        (CAPTURE_FLAG_INTERFACE_TILES, "interface", 1),
    )
    overrides: dict[int, bytes] = {}
    for indices, stem, expected_version in groups:
        for frame, source_index in enumerate(indices):
            path = CAPTURE_FLAG_ART_DIR / f"{stem}-{frame:02d}.tile"
            if not path.is_file():
                raise FileNotFoundError(f"Generated Capture Flag TILE is missing: {path}")
            custom_tile = path.read_bytes()
            if len(custom_tile) < 26 or struct.unpack_from("<H", custom_tile, 0)[0] != expected_version:
                raise ValueError(
                    f"Capture Flag {stem} frame {frame} is not TILE v{expected_version}: {path}"
                )
            if struct.unpack_from("<HH", custom_tile, 2) != struct.unpack_from(
                "<HH", tiles[source_index].data, 2
            ):
                raise ValueError(
                    f"Capture Flag {stem} frame {frame} changed stock geometry"
                )
            if custom_tile == tiles[source_index].data:
                raise ValueError(
                    f"Capture Flag {stem} frame {frame} is still identical to ARA2"
                )
            if expected_version == 3:
                palette_mode = struct.unpack_from("<H", custom_tile, 20)[0]
                palette_index = struct.unpack_from("<I", custom_tile, 22)[0]
                if palette_mode != 0 or palette_index != CAPTURE_FLAG_PALETTE:
                    raise ValueError(
                        f"Capture Flag {stem} frame {frame} must use stock palette "
                        f"{CAPTURE_FLAG_PALETTE}, got mode {palette_mode}, index {palette_index}"
                    )
            overrides[source_index] = custom_tile

    expected_indices = set(
        CAPTURE_FLAG_SPECIAL_TILES
        + CAPTURE_FLAG_MINIMAP_TILES
        + CAPTURE_FLAG_INTERFACE_TILES
    )
    if set(overrides) != expected_indices:
        raise ValueError("Capture Flag art does not cover every stock ARA2 frame")

    extra: list[CamEntry] = []

    def append(name: bytes, data: bytes) -> int:
        index = len(tiles) + len(extra)
        if index > 0xFFFF:
            raise ValueError("Private Capture Flag TILE index exceeds the IMAG low16 field")
        extra.append(CamEntry(pad_name(name), data))
        return index

    reference_offsets = imag_tile_reference_offsets(stock_imag)
    ordered_source_indices = (
        CAPTURE_FLAG_SPECIAL_TILES
        + CAPTURE_FLAG_MINIMAP_TILES
        + CAPTURE_FLAG_INTERFACE_TILES
    )
    if len(reference_offsets) != len(ordered_source_indices):
        raise ValueError(
            "Stock ARA2 no longer has the audited 12 Special, 4 Minimap, "
            "and 4 Interface frame fields"
        )
    custom_imag_buffer = bytearray(stock_imag)
    for tile_offset, source_index in zip(reference_offsets, ordered_source_indices):
        encoded = u32(stock_imag, tile_offset)
        private_index = append(
            CAPTURE_FLAG_IMAGE_TOKEN + f"{source_index:05d}".encode("ascii"),
            overrides[source_index],
        )
        struct.pack_into(
            "<I",
            custom_imag_buffer,
            tile_offset,
            (encoded & 0xFFFF0000) | private_index,
        )
    custom_imag = bytes(custom_imag_buffer)
    if len(extra) != len(expected_indices):
        raise ValueError(
            f"Private Capture Flag IMAG reached {len(extra)} TILEs; expected {len(expected_indices)}"
        )
    if custom_imag == stock_imag:
        raise ValueError("Private Capture Flag IMAG was not redirected to private TILEs")

    blank_stock_slots = tuple(CamEntry(entry.name, b"") for entry in tiles)
    write_cam(
        data_dir / "restore_zoo_capture_flag_maindata.cam",
        (
            CamSection(
                b"IMAG",
                (CamEntry(pad_name(CAPTURE_FLAG_IMAGE_CUSTOM), custom_imag),),
            ),
            CamSection(
                b"TILE",
                blank_stock_slots + tuple(extra),
                padding=b"\x01\x00\x00\x00",
            ),
            # Indexed-v3 TILEs require their palette table in the emitted
            # maindata package. Carry the literal base table through the
            # highest referenced index exactly as the proven Alchemist/Haunt
            # private art packages do. The manifest loads this CAM before the
            # MX Zoo CAM, so MX palettes 0-287 remain final for Zoo art.
            CamSection(
                b"SPLT",
                tuple(palettes[: CAPTURE_FLAG_PALETTE + 1]),
                padding=b"\x01\x00\x00\x00",
            ),
        ),
    )


def write_interfacedata_cam(game_path: Path, data_dir: Path) -> None:
    """Expose the literal stock monster-icon atlases in every Zoo dataset.

    The stock IX92/IX94 resolver assumes these expansion interface resources
    are already loaded. Base quests do not load mx_interfacedata.cam, so retain
    its complete positional TILE table and expose only the two atlas IMAG
    records through the Zoo's ordinary mod dataset.
    """
    source = game_path / "DataMX" / "mx_interfacedata.cam"
    images = read_cam_entries(source, b"IMAG")
    icon_prefixes = (b"IX92", b"IX94")
    icon_images = tuple(
        entry
        for prefix in icon_prefixes
        for entry in images
        if entry.name.rstrip(b"\x00").startswith(prefix)
    )
    if len(icon_images) != 2:
        raise ValueError(
            f"Expected stock IX92 and IX94 monster-icon records in {source}, "
            f"found {len(icon_images)}"
        )
    tiles = tuple(read_cam_entries(source, b"TILE"))
    if not tiles:
        raise ValueError(f"Stock monster-icon TILE table is incomplete in {source}")
    write_cam(
        data_dir / "restore_zoo_interfacedata.cam",
        (
            CamSection(b"IMAG", icon_images),
            CamSection(b"TILE", tiles, padding=b"\x01\x00\x00\x00"),
        ),
    )


def interface_imag_set_tile_offset(imag: bytes, set_id: int) -> int:
    """Return the sole frame TILE field for a stock one-direction UI set."""
    set_count = u32(imag, 20)
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Interface IMAG has an invalid animation-set table")
    for set_index in range(set_count):
        table_offset = 24 + set_index * 8
        current_id, set_offset = struct.unpack_from("<II", imag, table_offset)
        if current_id != set_id:
            continue
        if set_offset + 68 > len(imag) or u32(imag, set_offset) != 1:
            raise ValueError(f"Interface IMAG set {set_id} no longer has one direction")
        relative = struct.unpack_from("<i", imag, set_offset + 64)[0]
        direction_offset = set_offset + relative + 4
        if direction_offset + 28 > len(imag):
            raise ValueError(f"Interface IMAG set {set_id} has a truncated direction")
        if u32(imag, direction_offset) >> 16 != 1:
            raise ValueError(f"Interface IMAG set {set_id} no longer has one frame")
        return direction_offset + 24
    raise ValueError(f"Interface IMAG has no set {set_id}")


def interface_imag_exact_tile_offset(
    imag: bytes,
    set_id: int,
    source_tile_index: int,
) -> int:
    """Locate one proven stock TILE field inside a compact interface set.

    INTC item-icon sets use a shorter directional record than the INBg dialog
    backing. Restrict the search to the selected stock set and require its
    known source TILE exactly once instead of applying the actor-frame layout.
    """
    set_count = u32(imag, 20)
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Interface IMAG has an invalid animation-set table")
    sets = [struct.unpack_from("<II", imag, 24 + index * 8) for index in range(set_count)]
    for index, (current_id, set_offset) in enumerate(sets):
        if current_id != set_id:
            continue
        next_offset = sets[index + 1][1] if index + 1 < len(sets) else len(imag)
        if set_offset + 80 > next_offset or next_offset > len(imag):
            raise ValueError(f"Interface IMAG set {set_id} has invalid boundaries")
        matches = [
            offset
            for offset in range(set_offset + 80, next_offset - 3, 4)
            if (u32(imag, offset) & 0xFFFF) == source_tile_index
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Interface IMAG set {set_id} references stock TILE "
                f"{source_tile_index} {len(matches)} times"
            )
        return matches[0]
    raise ValueError(f"Interface IMAG has no set {set_id}")


def append_tactical_cursor_set(
    imag: bytes,
) -> bytes:
    """Append selector 38 by cloning stock Attack cursor set 1005 literally."""
    set_count = u32(imag, 20)
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("CUR1 has an invalid animation-set table")
    sets = [struct.unpack_from("<II", imag, 24 + index * 8) for index in range(set_count)]
    if any(set_id == PRIVATE_CAPTURE_CURSOR_SET for set_id, _offset in sets):
        raise ValueError("Stock CUR1 unexpectedly already contains set 1038")
    source_matches = [
        (index, offset)
        for index, (set_id, offset) in enumerate(sets)
        if set_id == STOCK_ATTACK_CURSOR_SET
    ]
    if len(source_matches) != 1:
        raise ValueError("Stock CUR1 no longer contains exactly one Attack cursor set 1005")
    source_index, source_offset = source_matches[0]
    source_end = sets[source_index + 1][1] if source_index + 1 < len(sets) else len(imag)
    if source_offset + 76 > source_end or source_end > len(imag):
        raise ValueError("Stock CUR1 Attack cursor set has invalid boundaries")
    clone = bytearray(imag[source_offset:source_end])
    direction_count = u32(clone, 0)
    if direction_count != 3:
        raise ValueError("Stock CUR1 Attack cursor no longer has three states")
    for direction in range(direction_count):
        relative = struct.unpack_from("<i", clone, 64 + direction * 4)[0]
        direction_offset = relative + 4
        tile_offset = direction_offset + 40
        if tile_offset + 4 > len(clone):
            raise ValueError("Stock CUR1 Attack cursor state is truncated")
        encoded = u32(clone, tile_offset)
        if encoded & 0xFFFF != STOCK_ATTACK_CURSOR_TILE:
            raise ValueError(
                "Stock CUR1 Attack cursor state no longer references TILE 27"
            )

    old_table_end = 24 + set_count * 8
    private_offset = len(imag) + 8
    output = bytearray(imag[:24])
    struct.pack_into("<I", output, 20, set_count + 1)
    for set_id, set_offset in sets:
        output += struct.pack("<II", set_id, set_offset + 8)
    output += struct.pack("<II", PRIVATE_CAPTURE_CURSOR_SET, private_offset)
    output += imag[old_table_end:]
    output += clone
    return bytes(output)


def privateize_tactical_cursor_tiles(
    imag: bytes,
    tiles: list[CamEntry],
    append,
    custom_capture_tile: bytes,
) -> tuple[bytes, set[int]]:
    """Preserve every stock CUR1 frame; replace only Capture's primary art.

    Retail CUR1 uses an end-anchored frame/lane table. Attack set 1005 has
    three primary TILE-27 frames plus shared cursor-state frames at TILE 24 and
    TILE 25. The private set must retain those shared frames literally; a
    fixed offset per direction sees only the primary frames and allows a later
    consolidated art layer to replace the shared slots with unrelated art.
    """
    patched = bytearray(imag)
    set_count = u32(imag, 20)
    sets = [
        struct.unpack_from("<II", imag, 24 + set_index * 8)
        for set_index in range(set_count)
    ]
    all_reference_offsets = imag_tile_reference_offsets(imag)
    stock_indices: set[int] = set()
    capture_replacement: int | None = None
    for set_index, (set_id, set_offset) in enumerate(sets):
        set_end = sets[set_index + 1][1] if set_index + 1 < len(sets) else len(imag)
        set_reference_offsets = tuple(
            offset
            for offset in all_reference_offsets
            if set_offset <= offset < set_end
        )
        source_indices = tuple(
            u32(imag, offset) & 0xFFFF for offset in set_reference_offsets
        )
        if set_id in (STOCK_ATTACK_CURSOR_SET, PRIVATE_CAPTURE_CURSOR_SET):
            if source_indices != (27, 27, 24, 27, 25):
                raise ValueError(
                    f"CUR1 set {set_id} no longer matches the complete stock "
                    "Attack cursor frame topology"
                )
        for tile_offset in set_reference_offsets:
            encoded = u32(imag, tile_offset)
            source_index = encoded & 0xFFFF
            if source_index >= len(tiles):
                raise ValueError(f"CUR1 references missing TILE {source_index}")
            if (
                set_id == PRIVATE_CAPTURE_CURSOR_SET
                and source_index == STOCK_ATTACK_CURSOR_TILE
            ):
                if capture_replacement is None:
                    capture_replacement = append(b"ZCCUCursor", custom_capture_tile)
                replacement = capture_replacement
            else:
                # Includes private set 1038's stock common-state TILEs 24/25,
                # so a later consolidated layer cannot provide other payloads
                # at those positional slots.
                stock_indices.add(source_index)
                replacement = source_index
            if replacement != source_index:
                struct.pack_into(
                    "<I",
                    patched,
                    tile_offset,
                    (encoded & 0xFFFF0000) | replacement,
                )
    if capture_replacement is None:
        raise ValueError("Extended CUR1 did not emit a private Capture cursor TILE")
    return bytes(patched), stock_indices


def privateize_interface_imag_tiles(
    imag: bytes,
    tiles: list[CamEntry],
    append,
    name_prefix: bytes,
    overrides: dict[int, bytes],
) -> bytes:
    """Clone every TILE reached by a stock interface IMAG into private slots.

    This is the same stock-adjacent positional-TILE pattern used by the
    Alchemist Brewing subpanel: the original index range remains empty, and
    every frame in the private IMAG is redirected to an appended private TILE.
    """
    patched = bytearray(imag)
    tile_offsets = imag_tile_reference_offsets(imag)
    replacements: dict[int, int] = {}
    for tile_offset in tile_offsets:
        encoded = u32(imag, tile_offset)
        source_index = encoded & 0xFFFF
        if source_index >= len(tiles):
            raise ValueError(f"IMAG references missing TILE {source_index}")
        if source_index not in replacements:
            replacements[source_index] = append(
                name_prefix + f"{source_index:05d}".encode("ascii"),
                overrides.get(source_index, tiles[source_index].data),
            )
        struct.pack_into(
            "<I",
            patched,
            tile_offset,
            (encoded & 0xFFFF0000) | replacements[source_index],
        )
    return bytes(patched)


def imag_tile_reference_offsets(imag: bytes) -> tuple[int, ...]:
    """Return typed IMAG TILE fields using Majesty's end-anchored layout.

    Stock direction records declare frame/lane counts at +4 and store their
    (metadata, TILE-reference) pairs at the end of each bounded direction
    record. Variable control words between those regions make a fixed +24
    frame-table guess unsafe. The 32-direction projectile record is the one
    audited exception and declares its count at +28.
    """
    set_count = u32(imag, 20)
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("IMAG has an invalid animation-set table")
    sets = [
        struct.unpack_from("<II", imag, 24 + set_index * 8)
        for set_index in range(set_count)
    ]
    set_offsets = [offset for _set_id, offset in sets]
    if set_offsets != sorted(set_offsets) or len(set(set_offsets)) != len(set_offsets):
        raise ValueError("IMAG set offsets are not strictly increasing")
    if set_offsets[0] < 24 + set_count * 8 or set_offsets[-1] >= len(imag):
        raise ValueError("IMAG set offsets leave the record")

    result: list[int] = []
    for set_index, (set_id, set_offset) in enumerate(sets):
        set_end = sets[set_index + 1][1] if set_index + 1 < len(sets) else len(imag)
        if set_end - set_offset < 68:
            raise ValueError(f"IMAG set {set_id} is truncated")
        direction_count = u32(imag, set_offset)
        direction_table_end = set_offset + 64 + direction_count * 4
        if direction_count <= 0 or direction_count > 32 or direction_table_end > set_end:
            raise ValueError(f"IMAG set {set_id} has invalid directions")
        relative_offsets = [
            struct.unpack_from("<i", imag, set_offset + 64 + direction * 4)[0]
            for direction in range(direction_count)
        ]
        if (
            relative_offsets != sorted(relative_offsets)
            or len(set(relative_offsets)) != len(relative_offsets)
            or any(relative <= 0 for relative in relative_offsets)
        ):
            raise ValueError(f"IMAG set {set_id} has unsupported direction offsets")
        anchors = [set_offset + relative for relative in relative_offsets]
        if anchors[0] < direction_table_end or anchors[-1] >= set_end:
            raise ValueError(f"IMAG set {set_id} direction data leaves the set")
        for direction, anchor in enumerate(anchors):
            direction_end = anchors[direction + 1] if direction + 1 < len(anchors) else set_end
            if anchor + 12 > direction_end:
                raise ValueError(f"IMAG set {set_id} direction {direction} is truncated")
            count_word = u32(imag, anchor + 4)
            frame_count = count_word >> 16
            lane_count = count_word & 0xFFFF
            field_count = frame_count * lane_count
            if 0 < field_count <= 4096 and frame_count > 0 and lane_count > 0:
                table_start = direction_end - field_count * 8
                minimum = anchor + 8
            else:
                if anchor + 36 > direction_end:
                    raise ValueError(f"IMAG set {set_id} direction {direction} is truncated")
                projectile_count = u32(imag, anchor + 28)
                frame_count = projectile_count >> 16
                lane_count = projectile_count & 0xFFFF
                field_count = frame_count * lane_count
                if not (0 < field_count <= 4096 and frame_count > 0 and lane_count > 0):
                    raise ValueError(
                        f"IMAG set {set_id} direction {direction} has no audited layout"
                    )
                table_start = direction_end - field_count * 8
                minimum = anchor + 32
            if table_start < minimum or (table_start - anchor) % 4:
                raise ValueError(
                    f"IMAG set {set_id} direction {direction} has an invalid frame table"
                )
            offsets = tuple(table_start + field * 8 + 4 for field in range(field_count))
            if not offsets or offsets[-1] + 4 > direction_end:
                raise ValueError(f"IMAG set {set_id} direction {direction} exceeds its boundary")
            result.extend(offsets)
    return tuple(result)


def write_zoo_rewards_interfacedata_cam(game_path: Path, data_dir: Path) -> None:
    """Package ZC01 art plus a stock-shaped private Capture cursor set."""
    source = game_path / "Data" / "interfacedata.cam"
    stock_imag = read_cam_entry(
        source, b"IMAG", ZOO_REWARDS_BACKGROUND_SOURCE
    ).data
    stock_icon_imag = read_cam_entry(
        source, b"IMAG", ZOO_CAPTURE_ICON_SOURCE
    ).data
    stock_cursor_imag = read_cam_entry(source, b"IMAG", TACTICAL_CURSOR_IMAGE).data
    tiles = read_cam_entries(source, b"TILE")
    palettes = read_cam_entries(source, b"PALT")
    if not tiles:
        raise ValueError(f"Stock interface TILE table is incomplete in {source}")
    if len(palettes) != 7 or any(not entry.data for entry in palettes):
        raise ValueError(f"Stock interface PALT table is incomplete in {source}")
    source_offset = interface_imag_set_tile_offset(
        stock_imag, ZOO_REWARDS_BACKGROUND_SET
    )
    source_index = u32(stock_imag, source_offset) & 0xFFFF
    tame_source_offset = interface_imag_set_tile_offset(
        stock_imag, ZOO_TAME_BACKGROUND_SET
    )
    tame_source_index = u32(stock_imag, tame_source_offset) & 0xFFFF
    if source_index >= len(tiles):
        raise ValueError("Stock AP41 backing references a missing TILE")
    if tame_source_index >= len(tiles):
        raise ValueError("Stock MX05 backing references a missing TILE")
    if tame_source_index == source_index:
        raise ValueError("Stock AP41 and MX05 unexpectedly share one backing TILE")
    if not ZOO_REWARDS_TILE.is_file():
        raise FileNotFoundError(
            f"Generated Zoo rewards TILE is missing: {ZOO_REWARDS_TILE}"
        )
    custom_tile = ZOO_REWARDS_TILE.read_bytes()
    if len(custom_tile) < 26 or struct.unpack_from("<H", custom_tile, 0)[0] != 1:
        raise ValueError("Zoo rewards art is not an embedded-palette V1 TILE")
    if struct.unpack_from("<HH", custom_tile, 2) != (245, 202):
        raise ValueError("Zoo rewards art must retain stock 202x245 geometry")
    if custom_tile == tiles[source_index].data:
        raise ValueError("Zoo rewards art is still identical to the stock AP41 backing")
    if custom_tile == tiles[tame_source_index].data:
        raise ValueError("Zoo tame art is still identical to the stock MX05 backing")
    icon_offset = interface_imag_exact_tile_offset(
        stock_icon_imag,
        ZOO_CAPTURE_ICON_SET,
        ZOO_CAPTURE_ICON_SOURCE_TILE,
    )
    if not ZOO_CAPTURE_ICON_TILE.is_file():
        raise FileNotFoundError(
            f"Generated Zoo Capture icon TILE is missing: {ZOO_CAPTURE_ICON_TILE}"
        )
    custom_icon_tile = ZOO_CAPTURE_ICON_TILE.read_bytes()
    if len(custom_icon_tile) < 26 or struct.unpack_from("<H", custom_icon_tile, 0)[0] != 1:
        raise ValueError("Zoo Capture button art is not an indexed V1 TILE")
    if struct.unpack_from("<HH", custom_icon_tile, 2) != (25, 25):
        raise ValueError("Zoo Capture button art must retain stock 25x25 geometry")
    if custom_icon_tile == tiles[ZOO_CAPTURE_ICON_SOURCE_TILE].data:
        raise ValueError("Zoo Capture button art is still identical to stock Attack")
    if not ZOO_CAPTURE_CURSOR_TILE.is_file():
        raise FileNotFoundError(
            f"Generated Zoo Capture cursor TILE is missing: {ZOO_CAPTURE_CURSOR_TILE}"
        )
    custom_cursor_tile = ZOO_CAPTURE_CURSOR_TILE.read_bytes()
    stock_cursor_tile = tiles[STOCK_ATTACK_CURSOR_TILE].data
    if len(custom_cursor_tile) < 26 or struct.unpack_from(
        "<H", custom_cursor_tile, 0
    )[0] != 3:
        raise ValueError("Zoo Capture cursor art is not a stock-format V3 TILE")
    if struct.unpack_from("<HH", custom_cursor_tile, 2) != struct.unpack_from(
        "<HH", stock_cursor_tile, 2
    ):
        raise ValueError("Zoo Capture cursor art changed the stock Attack cursor geometry")
    if custom_cursor_tile == stock_cursor_tile:
        raise ValueError("Zoo Capture cursor art is still identical to stock Attack")

    extra: list[CamEntry] = []

    def append(name: bytes, data: bytes) -> int:
        index = len(tiles) + len(extra)
        extra.append(CamEntry(pad_name(name), data))
        return index

    custom_imag = privateize_interface_imag_tiles(
        stock_imag,
        tiles,
        append,
        ZOO_REWARDS_BACKGROUND_TOKEN,
        {
            source_index: custom_tile,
            tame_source_index: custom_tile,
        },
    )
    private_source_index = u32(custom_imag, source_offset) & 0xFFFF
    if private_source_index < len(tiles):
        raise ValueError("Private Zoo rewards backing was not moved to an appended TILE")
    private_tame_source_index = u32(custom_imag, tame_source_offset) & 0xFFFF
    if private_tame_source_index < len(tiles):
        raise ValueError("Private Zoo tame backing was not moved to an appended TILE")
    private_icon_index = append(ZOO_CAPTURE_ICON_TOKEN + b"Button", custom_icon_tile)
    custom_icon_imag = bytearray(stock_icon_imag)
    encoded_icon = u32(stock_icon_imag, icon_offset)
    struct.pack_into(
        "<I",
        custom_icon_imag,
        icon_offset,
        (encoded_icon & 0xFFFF0000) | private_icon_index,
    )
    extended_cursor_imag = append_tactical_cursor_set(
        stock_cursor_imag,
    )
    custom_cursor_imag, stock_cursor_indices = privateize_tactical_cursor_tiles(
        extended_cursor_imag,
        tiles,
        append,
        custom_cursor_tile,
    )

    stock_slots = tuple(
        entry if index in stock_cursor_indices else CamEntry(entry.name, b"")
        for index, entry in enumerate(tiles)
    )
    write_cam(
        data_dir / "restore_zoo_rewards_interfacedata.cam",
        (
            CamSection(b"PALT", tuple(palettes)),
            CamSection(
                b"IMAG",
                (
                    CamEntry(pad_name(ZOO_REWARDS_BACKGROUND_CUSTOM), custom_imag),
                    CamEntry(pad_name(ZOO_CAPTURE_ICON_CUSTOM), bytes(custom_icon_imag)),
                    CamEntry(pad_name(TACTICAL_CURSOR_IMAGE), custom_cursor_imag),
                ),
            ),
            CamSection(
                b"TILE",
                stock_slots + tuple(extra),
                padding=b"\x01\x00\x00\x00",
            ),
        ),
    )


def prepare_output(output_root: Path) -> tuple[Path, Path]:
    resolved = output_root.resolve()
    if resolved.exists():
        if resolved.name != "RestoreAbandonedZoo":
            raise ValueError(
                "Refusing to replace an output directory not named RestoreAbandonedZoo: "
                f"{resolved}"
            )
        shutil.rmtree(resolved)
    data_dir = resolved / "Data"
    gpl_dir = resolved / "GPL"
    data_dir.mkdir(parents=True)
    gpl_dir.mkdir()
    return data_dir, gpl_dir


def merge_effective_art_layers(data_dir: Path) -> None:
    """Materialize the existing art load order as one CAM per domain."""

    def entries(path: Path, extension: bytes) -> tuple[CamEntry, ...]:
        result = tuple(read_cam_entries(path, extension))
        if not result:
            raise ValueError(f"{path} has no {extension.decode('ascii')} section")
        return result

    def overlay(earlier: tuple[CamEntry, ...], later: tuple[CamEntry, ...]) -> tuple[CamEntry, ...]:
        output: list[CamEntry] = []
        for index in range(max(len(earlier), len(later))):
            early = earlier[index] if index < len(earlier) else None
            late = later[index] if index < len(later) else None
            chosen = late if late is not None and late.data else early
            if chosen is None:
                chosen = CamEntry(index.to_bytes(4, "little").ljust(20, b"\x00"), b"")
            output.append(chosen)
        return tuple(output)

    def union_images(*paths: Path) -> tuple[CamEntry, ...]:
        output: list[CamEntry] = []
        by_key: dict[bytes, bytes] = {}
        for path in paths:
            for entry in read_cam_entries(path, b"IMAG"):
                key = entry.name.rstrip(b"\x00")[:4]
                previous = by_key.get(key)
                if previous is not None:
                    if previous != entry.data:
                        raise ValueError(f"Conflicting private IMAG key {key!r}")
                    continue
                by_key[key] = entry.data
                output.append(entry)
        return tuple(output)

    capture_main = data_dir / "restore_zoo_capture_flag_maindata.cam"
    zoo_main = data_dir / "restore_zoo_maindata.cam"
    write_cam(
        zoo_main,
        (
            CamSection(b"IMAG", union_images(capture_main, zoo_main)),
            CamSection(
                b"TILE",
                overlay(entries(capture_main, b"TILE"), entries(zoo_main, b"TILE")),
                padding=b"\x01\x00\x00\x00",
            ),
            CamSection(
                b"SPLT",
                overlay(entries(capture_main, b"SPLT"), entries(zoo_main, b"SPLT")),
                padding=b"\x01\x00\x00\x00",
            ),
        ),
    )
    capture_main.unlink()

    visitor_interface = data_dir / "restore_zoo_interfacedata.cam"
    rewards_interface = data_dir / "restore_zoo_rewards_interfacedata.cam"
    write_cam(
        visitor_interface,
        (
            CamSection(
                b"PALT",
                entries(rewards_interface, b"PALT"),
                padding=b"\x01\x00\x00\x00",
            ),
            CamSection(b"IMAG", union_images(visitor_interface, rewards_interface)),
            CamSection(
                b"TILE",
                overlay(
                    entries(visitor_interface, b"TILE"),
                    entries(rewards_interface, b"TILE"),
                ),
                padding=b"\x01\x00\x00\x00",
            ),
        ),
    )
    rewards_interface.unlink()


def build(game_path: Path, output_root: Path) -> None:
    game_path = game_path.resolve()
    compiler = game_path / "SDK" / "Gplbcc.exe"
    if not compiler.is_file():
        raise FileNotFoundError(f"Majesty GPL compiler was not found: {compiler}")
    require_cam_entry_prefix(
        game_path / "DataMX" / "mx_maindata.cam",
        b"IMAG",
        (b"ABn1", b"ABn2", b"ABn3"),
    )

    data_dir, gpl_dir = prepare_output(output_root)
    shutil.copy2(SOURCE_ROOT / "RestoreAbandonedZoo.mmxml", output_root / "RestoreAbandonedZoo.mmxml")
    shutil.copy2(SOURCE_ROOT / "mod-definition.json", output_root / "mod-definition.json")
    shutil.copy2(SOURCE_ROOT / "Data" / "restore_zoo_units.xml", data_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Building_Data.dat", gpl_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Flag_Data.dat", gpl_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Capture.gpl", gpl_dir)
    shutil.copy2(
        SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_DealDemon_Test.gpl", gpl_dir
    )
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo.gplproj", gpl_dir)
    write_maindata_cam(game_path, data_dir)
    write_capture_flag_maindata_cam(game_path, data_dir)
    write_interfacedata_cam(game_path, data_dir)
    write_zoo_rewards_interfacedata_cam(game_path, data_dir)
    merge_effective_art_layers(data_dir)
    write_miscdata_cam(game_path, data_dir)
    write_text_cams(game_path, data_dir)
    result = subprocess.run(
        (str(compiler), "-in", "RestoreAbandonedZoo.gplproj", "-out", "RestoreAbandonedZoo.bcd", "-stdout"),
        cwd=gpl_dir,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"GPL compiler failed with exit code {result.returncode}")
    compiled = gpl_dir / "RestoreAbandonedZoo.bcd"
    if not compiled.is_file():
        raise FileNotFoundError(f"GPL compiler did not produce {compiled}")
    shutil.copy2(compiled, data_dir / compiled.name)
    compiled.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Restore Abandoned Zoo")
    parser.add_argument("--game-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.game_path, args.output_root)
    print(f"Built {args.output_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
