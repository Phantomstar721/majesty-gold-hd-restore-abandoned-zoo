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
ZOO_REWARDS_BACKGROUND_SOURCE = b"INBgbuilding dialog"
ZOO_REWARDS_BACKGROUND_CUSTOM = b"ZOBGbuilding dialog"
ZOO_REWARDS_BACKGROUND_TOKEN = b"ZOBG"
ZOO_REWARDS_BACKGROUND_SET = 1019
ZOO_REWARDS_TILE = (
    REPO_ROOT / "assets" / "generated" / "interface" / "zoo-rewards-panel.tile"
)
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


def privatize_zoo_rewards_menu(palace_rewards_menu: bytes) -> bytes:
    """Clone AP41 and move its Explore controls to stock's hidden position."""
    if palace_rewards_menu.count(b"INBg") != 1:
        raise ValueError("Stock AP41 no longer contains exactly one INBg background token")
    if ZOO_REWARDS_BACKGROUND_TOKEN in palace_rewards_menu:
        raise ValueError("Stock AP41 unexpectedly already contains the Zoo background token")
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
    return bytes(patched)


def write_text_cams(game_path: Path, data_dir: Path) -> None:
    base_textdata = game_path / "Data" / "textdata.cam"
    expansion_textdata = game_path / "DataMX" / "mx_textdata.cam"
    gpltext = game_path / "DataMX" / "mx_gpltext.cam"
    stock_menu = read_cam_entry(expansion_textdata, b"SMNU", b"MX09")
    stock_blacksmith_menu = read_cam_entry(base_textdata, b"SMNU", b"AP02")
    stock_palace_menu = read_cam_entry(base_textdata, b"SMNU", b"AP39")
    stock_palace_rewards_menu = read_cam_entry(base_textdata, b"SMNU", b"AP41")
    stock_palace_rewards_strings = read_cam_entry(base_textdata, b"STRT", b"AP41")
    stock_strings = read_cam_entry(expansion_textdata, b"STRT", b"MX09")
    unit_names = read_cam_entry(base_textdata, b"STRT", b"UNTN")
    advisor_text = read_cam_entry(gpltext, b"STRT", b"AITX")
    help_text = read_cam_entry(gpltext, b"STRT", b"HPTX")

    patched_strings = patch_indexed_strt(
        stock_strings.data,
        {
            0: "A completed Zoo makes Attack Flags on living monsters trigger the stock Hooligan return lifecycle.",
            4: "Destroy this Zoo.",
        },
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
            117: "Capturing a monster",
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
                        restore_zoo_visitors_control(
                            restore_zoo_reward_dispatch(
                                stock_menu.data, stock_palace_menu.data
                            ),
                            stock_blacksmith_menu.data,
                        ),
                    ),
                    CamEntry(
                        pad_name(ZOO_REWARDS_DIALOG_ID),
                        privatize_zoo_rewards_menu(stock_palace_rewards_menu.data),
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
    set_count = u32(imag, 20)
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Interface IMAG has an invalid animation-set table")
    replacements: dict[int, int] = {}
    for set_index in range(set_count):
        table_offset = 24 + set_index * 8
        set_id, set_offset = struct.unpack_from("<II", imag, table_offset)
        if set_offset + 68 > len(imag):
            raise ValueError(f"Interface IMAG set {set_id} is truncated")
        direction_count = u32(imag, set_offset)
        if direction_count <= 0 or direction_count > 32:
            raise ValueError(f"Interface IMAG set {set_id} has invalid directions")
        for direction in range(direction_count):
            relative = struct.unpack_from(
                "<i", imag, set_offset + 64 + direction * 4
            )[0]
            direction_offset = set_offset + relative + 4
            if direction_offset + 28 > len(imag):
                raise ValueError(f"Interface IMAG set {set_id} has a truncated direction")
            frame_count = u32(imag, direction_offset) >> 16
            if frame_count <= 0 or frame_count > 64:
                raise ValueError(f"Interface IMAG set {set_id} has invalid frames")
            for frame in range(frame_count):
                tile_offset = direction_offset + 24 + frame * 8
                encoded = u32(imag, tile_offset)
                source_index = encoded & 0xFFFF
                if source_index >= len(tiles):
                    raise ValueError(
                        f"Interface IMAG references missing TILE {source_index}"
                    )
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


def write_zoo_rewards_interfacedata_cam(game_path: Path, data_dir: Path) -> None:
    """Package a private Zoo-themed clone of stock INBg for ZC01 only."""
    source = game_path / "Data" / "interfacedata.cam"
    stock_imag = read_cam_entry(
        source, b"IMAG", ZOO_REWARDS_BACKGROUND_SOURCE
    ).data
    tiles = read_cam_entries(source, b"TILE")
    if not tiles:
        raise ValueError(f"Stock interface TILE table is incomplete in {source}")
    source_offset = interface_imag_set_tile_offset(
        stock_imag, ZOO_REWARDS_BACKGROUND_SET
    )
    source_index = u32(stock_imag, source_offset) & 0xFFFF
    if source_index >= len(tiles):
        raise ValueError("Stock AP41 backing references a missing TILE")
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
        {source_index: custom_tile},
    )
    private_source_index = u32(custom_imag, source_offset) & 0xFFFF
    if private_source_index < len(tiles):
        raise ValueError("Private Zoo rewards backing was not moved to an appended TILE")

    blank_stock_slots = tuple(CamEntry(entry.name, b"") for entry in tiles)
    write_cam(
        data_dir / "restore_zoo_rewards_interfacedata.cam",
        (
            CamSection(
                b"IMAG",
                (CamEntry(pad_name(ZOO_REWARDS_BACKGROUND_CUSTOM), custom_imag),),
            ),
            CamSection(
                b"TILE",
                blank_stock_slots + tuple(extra),
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
    shutil.copy2(SOURCE_ROOT / "Data" / "restore_zoo_units.xml", data_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Building_Data.dat", gpl_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Flag_Data.dat", gpl_dir)
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_Capture.gpl", gpl_dir)
    shutil.copy2(
        SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo_DealDemon_Test.gpl", gpl_dir
    )
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo.gplproj", gpl_dir)
    write_maindata_cam(game_path, data_dir)
    write_interfacedata_cam(game_path, data_dir)
    write_zoo_rewards_interfacedata_cam(game_path, data_dir)
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
