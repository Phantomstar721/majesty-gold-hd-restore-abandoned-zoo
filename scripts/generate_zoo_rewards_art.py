from __future__ import annotations

import argparse
import importlib.util
import struct
import sys
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = REPO_ROOT / "assets" / "source" / "interface" / "zoo-rewards-panel-master.png"
PRIMARY_MASTER_PATH = (
    REPO_ROOT / "assets" / "source" / "interface" / "zoo-primary-panel-master.png"
)
OUTPUT_PNG = REPO_ROOT / "assets" / "generated" / "interface" / "zoo-rewards-panel-202x245.png"
OUTPUT_TILE = REPO_ROOT / "assets" / "generated" / "interface" / "zoo-rewards-panel.tile"
PRIMARY_OUTPUT_PNG = (
    REPO_ROOT / "assets" / "generated" / "interface" / "zoo-primary-panel-200x245.png"
)
PRIMARY_OUTPUT_TILE = (
    REPO_ROOT / "assets" / "generated" / "interface" / "zoo-primary-panel.tile"
)
SOURCE_IMAG = b"INBgbuilding dialog"
SOURCE_SET_ID = 1019
PRIMARY_RAW_TEMPLATE_TILE = 466


def load_stock_pipeline():
    path = (
        REPO_ROOT.parent
        / "majesty-gold-hd-custom-guild-phantoms-haunt"
        / "src"
        / "build_phantom_guild.py"
    )
    spec = importlib.util.spec_from_file_location("zoo_stock_art_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load the proven Haunt CAM art pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def interface_set_tile_offset(imag: bytes, set_id: int) -> int:
    set_count = struct.unpack_from("<I", imag, 20)[0]
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Stock INBg has an invalid animation-set table")
    for set_index in range(set_count):
        table_offset = 24 + set_index * 8
        current_id, set_offset = struct.unpack_from("<II", imag, table_offset)
        if current_id != set_id:
            continue
        if set_offset + 68 > len(imag):
            raise ValueError(f"Stock INBg set {set_id} is truncated")
        direction_count = struct.unpack_from("<I", imag, set_offset)[0]
        if direction_count != 1:
            raise ValueError(f"Stock INBg set {set_id} no longer has one direction")
        relative = struct.unpack_from("<i", imag, set_offset + 64)[0]
        direction = set_offset + relative + 4
        if direction + 28 > len(imag):
            raise ValueError(f"Stock INBg set {set_id} has a truncated direction")
        frame_count = struct.unpack_from("<I", imag, direction)[0] >> 16
        if frame_count != 1:
            raise ValueError(f"Stock INBg set {set_id} no longer has one frame")
        return direction + 24
    raise ValueError(f"Stock INBg has no set {set_id}")


def decode_embedded_v1(stock, tile: bytes) -> Image.Image:
    if len(tile) < 26 or struct.unpack_from("<H", tile, 0)[0] != 1:
        raise ValueError("Stock AP41 backing is no longer an embedded-palette V1 TILE")
    height, width, stride = struct.unpack_from("<HHH", tile, 2)
    palette_offset = struct.unpack_from("<I", tile, 22)[0]
    colors = stock.embedded_palette_colors(tile, palette_offset)
    if colors is None or 26 + stride * height > len(tile):
        raise ValueError("Stock AP41 backing has invalid pixels or palette")
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(height):
        row = tile[26 + y * stride : 26 + (y + 1) * stride]
        for x, palette_index in enumerate(row[:width]):
            if palette_index:
                red, green, blue = colors[palette_index]
                pixels[x, y] = (red, green, blue, 255)
    return image


def fit_master(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    target_ratio = size[0] / size[1]
    current_ratio = image.width / image.height
    if current_ratio > target_ratio:
        width = round(image.height * target_ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / target_ratio)
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def is_palace_red(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return bool(
        alpha
        and red > 18
        and red > green * 1.25
        and blue >= green * 0.75
    )


def zoo_header_color(pixel: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Retain the stock title texture while shifting Palace red to Zoo timber."""
    red, green, blue, alpha = pixel
    light = max(red, green, blue)
    return (
        min(58, 24 + light // 5),
        min(48, 20 + light // 7),
        min(31, 13 + light // 10),
        alpha,
    )


def composite_stock_chrome(panel: Image.Image, stock_frame: Image.Image) -> Image.Image:
    if panel.size != stock_frame.size:
        raise ValueError("Zoo master and AP41 backing geometry differ")
    result = panel.copy()
    source = stock_frame.load()
    target = result.load()
    width, height = result.size
    for y in range(height):
        for x in range(width):
            # This is the Alchemist Brewing-panel split applied to AP41:
            # retain only the outer frame, title band, functional Capture row,
            # and navigation strip.  The entire Explore half is intentionally
            # left as Zoo backing, because its controls are offscreen in ZC01.
            preserve = (
                x < 6
                or x >= width - 6
                or y < 29
                or 29 <= y < 121
                or y >= 222
            )
            pixel = source[x, y]
            if y < 29 and pixel[3] and is_palace_red(pixel):
                # The title fill is part of the background TILE, not a control.
                # Recolor its stock texture to dark Zoo timber for legibility.
                target[x, y] = zoo_header_color(pixel)
            elif preserve and pixel[3] and not is_palace_red(pixel):
                target[x, y] = pixel
            elif 17 <= x <= 125 and 87 <= y <= 111 and not pixel[3]:
                # Stock uses transparent index 0 inside the amount field and
                # relies on the Palace panel beneath it to appear black.  A
                # private opaque backing needs to supply that contrast itself.
                target[x, y] = (18, 20, 14, 255)
    return result


def generate(game_path: Path) -> None:
    for path in (MASTER_PATH, PRIMARY_MASTER_PATH):
        if not path.is_file():
            raise FileNotFoundError(path)
    if MASTER_PATH.read_bytes() == PRIMARY_MASTER_PATH.read_bytes():
        raise ValueError("Zoo primary and Capture panels require distinct source masters")
    stock = load_stock_pipeline()
    source = game_path / "Data" / "interfacedata.cam"
    imag = stock.read_cam_entry(source, b"IMAG", SOURCE_IMAG).data
    tiles = stock.read_cam_entries(source, b"TILE")

    if PRIMARY_RAW_TEMPLATE_TILE >= len(tiles):
        raise ValueError("Stock guild-panel backing template TILE 466 is missing")
    primary_preview = fit_master(PRIMARY_MASTER_PATH, (200, 245)).convert("RGB")
    primary_tile = stock.tile_v1_embedded_from_rgb(
        tiles[PRIMARY_RAW_TEMPLATE_TILE].data,
        primary_preview.tobytes(),
    )
    if struct.unpack_from("<HH", primary_tile, 2) != (245, 200):
        raise ValueError("Packed Zoo guild backing changed the stock 200x245 geometry")
    PRIMARY_OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    primary_preview.save(PRIMARY_OUTPUT_PNG)
    PRIMARY_OUTPUT_TILE.write_bytes(primary_tile)

    tile_offset = interface_set_tile_offset(imag, SOURCE_SET_ID)
    source_index = struct.unpack_from("<I", imag, tile_offset)[0] & 0xFFFF
    if source_index >= len(tiles):
        raise ValueError(f"Stock INBg set {SOURCE_SET_ID} references missing TILE {source_index}")
    template = tiles[source_index].data
    stock_frame = decode_embedded_v1(stock, template)
    if stock_frame.size != (202, 245):
        raise ValueError(f"Stock AP41 backing geometry changed: {stock_frame.size}")

    panel = fit_master(MASTER_PATH, stock_frame.size)
    result = composite_stock_chrome(panel, stock_frame)
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    result.convert("RGB").save(OUTPUT_PNG)
    packed = stock.tile_v1_embedded_from_rgb(template, result.convert("RGB").tobytes())
    if packed == template:
        raise ValueError("Zoo rewards art did not produce a private TILE")
    if struct.unpack_from("<HH", packed, 2) != (245, 202):
        raise ValueError("Packed Zoo rewards TILE geometry changed")
    OUTPUT_TILE.write_bytes(packed)
    print(f"Generated {PRIMARY_OUTPUT_PNG}")
    print(
        f"Packed {PRIMARY_OUTPUT_TILE} from stock guild raw-texture "
        f"TILE {PRIMARY_RAW_TEMPLATE_TILE}"
    )
    print(f"Generated {OUTPUT_PNG}")
    print(f"Packed {OUTPUT_TILE} from stock INBg set {SOURCE_SET_ID} TILE {source_index}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Zoo rewards-panel backing")
    parser.add_argument("--game-path", type=Path, required=True)
    args = parser.parse_args()
    generate(args.game_path.resolve())


if __name__ == "__main__":
    main()
