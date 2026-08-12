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


def write_text_cams(game_path: Path, data_dir: Path) -> None:
    base_textdata = game_path / "Data" / "textdata.cam"
    expansion_textdata = game_path / "DataMX" / "mx_textdata.cam"
    gpltext = game_path / "DataMX" / "mx_gpltext.cam"
    stock_menu = read_cam_entry(expansion_textdata, b"SMNU", b"MX09")
    stock_strings = read_cam_entry(expansion_textdata, b"STRT", b"MX09")
    unit_names = read_cam_entry(base_textdata, b"STRT", b"UNTN")
    help_text = read_cam_entry(gpltext, b"STRT", b"HPTX")

    patched_strings = patch_indexed_strt(
        stock_strings.data,
        {
            0: "The Zoo is a restored civic building. Monster capture controls are not yet available.",
            4: "Destroy this Zoo.",
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
                "- Monster capture controls are not available in this version\n\n\n"
                "\x01BCBCFFThese long-abandoned grounds hint at an unfinished royal plan to exhibit Ardania's creatures."
            ),
            fourcc_id("hZ02"): (
                "- Second-level Zoo\n\n"
                "- Increased building hit points\n\n"
                "- May be upgraded once more\n\n"
                "- Monster capture controls are not available in this version"
            ),
            fourcc_id("hZ03"): (
                "- Third-level Zoo\n\n"
                "- Maximum building hit points\n\n"
                "- Monster capture controls are not available in this version"
            ),
        },
    )

    write_cam(
        data_dir / "restore_zoo_textdata.cam",
        (
            CamSection(b"SMNU", (CamEntry(pad_name(b"MX09"), stock_menu.data),)),
            CamSection(
                b"STRT",
                (
                    CamEntry(pad_name(b"UNTN"), patched_names),
                    CamEntry(pad_name(b"MX09"), patched_strings),
                ),
            ),
        ),
    )
    write_cam(
        data_dir / "restore_zoo_gpltext.cam",
        (CamSection(b"STRT", (CamEntry(pad_name(b"HPTX"), patched_help),)),),
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
    shutil.copy2(SOURCE_ROOT / "GPL" / "RestoreAbandonedZoo.gplproj", gpl_dir)
    write_maindata_cam(game_path, data_dir)
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
