from __future__ import annotations

import argparse
import colorsys
import importlib.util
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_INTERFACE = (
    REPO_ROOT
    / "assets"
    / "source"
    / "capture-flag"
    / "capture-flag-interface-master.png"
)
SOURCE_WORLD = (
    REPO_ROOT
    / "assets"
    / "source"
    / "capture-flag"
    / "capture-flag-world-master.png"
)
OUTPUT_DIR = REPO_ROOT / "assets" / "generated" / "capture-flag"
STOCK_IMAGE = b"ARA2flag attack"
STOCK_BUTTON_IMAGE = b"INTCItem Icons"
STOCK_BUTTON_TILE = 92
STOCK_SPECIAL_TILES = tuple(range(16655, 16667))
STOCK_MINIMAP_TILES = tuple(range(16667, 16671))
STOCK_INTERFACE_TILES = tuple(range(16671, 16675))
CAPTURE_WORLD_PALETTE = 793
PLAYER_COLORS = (
    (35, 83, 212),
    (24, 156, 100),
    (218, 135, 27),
    (160, 45, 170),
)


def load_stock_pipeline():
    path = (
        REPO_ROOT.parent
        / "majesty-gold-hd-custom-guild-phantoms-haunt"
        / "src"
        / "build_phantom_guild.py"
    )
    spec = importlib.util.spec_from_file_location("zoo_capture_flag_stock_art", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load the proven Haunt CAM art pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def render_indexed_v3(stock, tile: bytes, palettes: list[object]) -> Image.Image:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected a readable stock indexed-v3 flag TILE")
    height, width, indices = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    output = image.load()
    for y, row in enumerate(indices):
        for x, index in enumerate(row):
            if not index:
                continue
            red, green, blue = colors[index]
            if stock.is_transparent_rgb(red, green, blue):
                continue
            output[x, y] = (red, green, blue, 255)
    return image


def render_embedded_v1(stock, tile: bytes) -> Image.Image:
    if len(tile) < 26 or struct.unpack_from("<H", tile, 0)[0] != 1:
        raise ValueError("Expected a stock indexed-v1 Capture button TILE")
    height, width, stride = struct.unpack_from("<HHH", tile, 2)
    palette_offset = struct.unpack_from("<I", tile, 22)[0]
    colors = stock.embedded_palette_colors(tile, palette_offset)
    if colors is None or stride < width or 26 + stride * height > len(tile):
        raise ValueError("Stock Capture button TILE has invalid pixels or palette")
    transparent = struct.unpack_from("<H", tile, 16)[0] & 0xFF
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    output = image.load()
    for y in range(height):
        row = tile[26 + y * stride : 26 + (y + 1) * stride]
        for x, index in enumerate(row[:width]):
            if index == transparent:
                continue
            red, green, blue = colors[index]
            output[x, y] = (red, green, blue, 255)
    return image


def embedded_v1_from_rgba(original_tile: bytes, image: Image.Image) -> bytes:
    """Pack RGBA while retaining stock indexed-v1 transparency semantics."""
    if len(original_tile) < 26 or struct.unpack_from("<H", original_tile, 0)[0] != 1:
        raise ValueError("Capture button template is not TILE v1")
    height, width, stride = struct.unpack_from("<HHH", original_tile, 2)
    image = image.convert("RGBA")
    if image.size != (width, height) or stride < width or stride == width * 2:
        raise ValueError("Capture button art changed the stock indexed-v1 geometry")

    rgb = Image.new("RGB", image.size, (0, 0, 0))
    rgb.paste(image.convert("RGB"), mask=image.getchannel("A"))
    quantized = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette() or []
    alpha = image.getchannel("A")
    output = bytearray(original_tile[:26])
    for y in range(height):
        for x in range(width):
            output.append(
                min(255, int(quantized.getpixel((x, y))) + 1)
                if alpha.getpixel((x, y)) >= 16
                else 0
            )
        output += b"\x00" * max(0, stride - width)

    original_palette_offset = struct.unpack_from("<I", original_tile, 22)[0]
    original_palette_tail = (
        original_tile[original_palette_offset:]
        if 0 <= original_palette_offset < len(original_tile)
        else b""
    )
    palette_prefix = original_palette_tail[:8]
    palette_suffix = original_palette_tail[8 + 256 * 4 :]
    new_palette_offset = len(output)
    struct.pack_into("<H", output, 16, 0)
    struct.pack_into("<H", output, 20, 1)
    struct.pack_into("<I", output, 22, new_palette_offset)
    output += palette_prefix or b"\x00\x00\x00\x01\x00\x00\x00\x00"
    output += b"\x00\x00\x00\x00"
    for index in range(255):
        offset = index * 3
        if offset + 2 < len(raw_palette):
            red, green, blue = raw_palette[offset : offset + 3]
        else:
            red, green, blue = (0, 0, 0)
        output += bytes((red, green, blue, 0))
    output += palette_suffix
    return bytes(output)


def is_red_cloth(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return bool(alpha and red > 45 and red > green * 1.30 and red > blue * 1.08)


def is_blue_trim(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return bool(alpha and blue > 45 and blue > red * 1.28 and blue > green * 1.12)


def lerp_color(
    dark: tuple[int, int, int],
    light: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int, int]:
    amount = max(0.0, min(1.0, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(dark, light)) + (255,)


def master_palette() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Sample the generated concept so the tiny frames inherit its palette."""
    master = Image.open(SOURCE_WORLD).convert("RGBA")
    green: list[tuple[int, int, int]] = []
    gold: list[tuple[int, int, int]] = []
    for red, channel_green, blue, alpha in master.getdata():
        if alpha < 128:
            continue
        if channel_green > red * 1.20 and channel_green > blue * 1.20:
            green.append((red, channel_green, blue))
        elif red > channel_green >= blue and red > 105 and channel_green > 65:
            gold.append((red, channel_green, blue))
    if not green or not gold:
        raise ValueError("Capture Flag source master no longer exposes green and gold samples")

    def average(values: list[tuple[int, int, int]]) -> tuple[int, int, int]:
        return tuple(round(sum(value[index] for value in values) / len(values)) for index in range(3))

    return average(green), average(gold)


def draw_paw(
    image: Image.Image,
    center_x: int,
    top_y: int,
    gold: tuple[int, int, int],
) -> None:
    """Draw the smallest readable four-toe paw used by the world sprite."""
    pixels = image.load()
    shadow = (49, 37, 18, 255)
    bright = tuple(min(255, channel + 28) for channel in gold) + (255,)
    base = gold + (255,)
    toe_points = {
        (-6, 1), (-5, 1), (-6, 2), (-5, 2),
        (-3, 0), (-2, 0), (-3, 1), (-2, 1),
        (2, 0), (3, 0), (2, 1), (3, 1),
        (5, 1), (6, 1), (5, 2), (6, 2),
    }
    pad_points = {
        (-3, 4), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 4),
        (-4, 5), (-3, 5), (-2, 5), (-1, 5), (0, 5), (1, 5), (2, 5), (3, 5), (4, 5),
        (-4, 6), (-3, 6), (-2, 6), (-1, 6), (0, 6), (1, 6), (2, 6), (3, 6), (4, 6),
        (-3, 7), (-2, 7), (-1, 7), (0, 7), (1, 7), (2, 7), (3, 7),
    }
    for dx, dy in toe_points | pad_points:
        x, y = center_x + dx + 1, top_y + dy + 1
        if 0 <= x < image.width and 0 <= y < image.height and pixels[x, y][3]:
            pixels[x, y] = shadow
    for dx, dy in toe_points:
        x, y = center_x + dx, top_y + dy
        if 0 <= x < image.width and 0 <= y < image.height and pixels[x, y][3]:
            pixels[x, y] = bright if dy <= 0 else base
    for dx, dy in pad_points:
        x, y = center_x + dx, top_y + dy
        if 0 <= x < image.width and 0 <= y < image.height and pixels[x, y][3]:
            pixels[x, y] = bright if dy <= 3 else base


def capture_world_frame(
    source: Image.Image,
    green: tuple[int, int, int],
    gold: tuple[int, int, int],
) -> Image.Image:
    result = source.copy()
    source_pixels = source.load()
    target = result.load()
    body_rows: list[tuple[int, int, int]] = []

    for y in range(source.height):
        red_x = [x for x in range(source.width) if is_red_cloth(source_pixels[x, y])]
        if y < 10 or len(red_x) < 2:
            continue
        left, right = min(red_x), max(red_x)
        body_rows.append((y, left, right))
        red_values = [source_pixels[x, y][0] for x in red_x]
        median = sorted(red_values)[len(red_values) // 2]
        for x in range(left, right + 1):
            pixel = source_pixels[x, y]
            if not pixel[3] or is_blue_trim(pixel):
                continue
            brightness = pixel[0] if is_red_cloth(pixel) else median
            wave = 0.88 + 0.12 * math.sin((x + y) * 0.85)
            amount = max(0.0, min(1.0, (brightness / 255.0) * wave))
            dark = tuple(max(4, round(channel * 0.28)) for channel in green)
            light = tuple(min(210, round(channel * 1.22 + 8)) for channel in green)
            target[x, y] = lerp_color(dark, light, amount)

    emblem_rows = [row for row in body_rows if 14 <= row[0] <= min(25, source.height - 1)]
    if not emblem_rows:
        raise ValueError("Stock Attack Flag frame no longer exposes a body for the paw emblem")
    center_x = round(sum((left + right) / 2 for _y, left, right in emblem_rows) / len(emblem_rows))
    top_y = max(14, min(source.height - 7, 17))
    draw_paw(result, center_x, top_y, gold)
    return result


def capture_minimap_frame(
    source: Image.Image,
    green: tuple[int, int, int],
    gold: tuple[int, int, int],
) -> Image.Image:
    result = source.copy()
    pixels = result.load()
    for y in range(result.height):
        for x in range(result.width):
            red, channel_green, blue, alpha = pixels[x, y]
            if not alpha:
                continue
            if red > channel_green * 1.20 and red > blue * 1.08:
                strength = max(0.35, red / 255.0)
                pixels[x, y] = tuple(round(channel * strength) for channel in gold) + (255,)
            elif is_blue_trim((red, channel_green, blue, alpha)) and (x + y) % 2:
                pixels[x, y] = tuple(round(channel * 0.75) for channel in green) + (255,)
    return result


def capture_button_icon(
    source: Image.Image,
    green: tuple[int, int, int],
    gold: tuple[int, int, int],
) -> Image.Image:
    """Retain INTC set 1011's stock button frame and repaint its tiny flag."""
    result = source.copy()
    source_pixels = source.load()
    target = result.load()
    body_rows: list[tuple[int, int, int]] = []
    for y in range(source.height):
        red_x = [x for x in range(source.width) if is_red_cloth(source_pixels[x, y])]
        if y < 4 or len(red_x) < 2:
            continue
        left, right = min(red_x), max(red_x)
        body_rows.append((y, left, right))
        median = sorted(source_pixels[x, y][0] for x in red_x)[len(red_x) // 2]
        for x in range(left, right + 1):
            pixel = source_pixels[x, y]
            if not pixel[3] or is_blue_trim(pixel):
                continue
            brightness = pixel[0] if is_red_cloth(pixel) else median
            amount = max(0.0, min(1.0, brightness / 255.0))
            dark = tuple(max(4, round(channel * 0.25)) for channel in green)
            light = tuple(min(210, round(channel * 1.18 + 8)) for channel in green)
            target[x, y] = lerp_color(dark, light, amount)
    if not body_rows:
        raise ValueError("Stock INTC set 1011 no longer exposes a red Attack flag")

    paw = gold + (255,)
    paw_bright = tuple(min(255, channel + 30) for channel in gold) + (255,)
    shadow = (45, 34, 17, 255)
    center_x = round(sum((left + right) / 2 for _y, left, right in body_rows) / len(body_rows))
    points = {
        (-3, 0), (-1, -1), (1, -1), (3, 0),
        (-1, 2), (0, 1), (1, 2),
        (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3),
        (-1, 4), (0, 4), (1, 4),
    }
    top_y = 11
    for dx, dy in points:
        x, y = center_x + dx + 1, top_y + dy + 1
        if 0 <= x < result.width and 0 <= y < result.height and target[x, y][3]:
            target[x, y] = shadow
    for dx, dy in points:
        x, y = center_x + dx, top_y + dy
        if 0 <= x < result.width and 0 <= y < result.height and target[x, y][3]:
            target[x, y] = paw_bright if dy <= 1 else paw
    return result


def interface_master() -> Image.Image:
    source = Image.open(SOURCE_INTERFACE).convert("RGB")
    fitted = ImageOps.fit(source, (100, 100), method=Image.Resampling.LANCZOS)
    fitted = ImageEnhance.Contrast(fitted).enhance(1.06)
    return fitted.filter(ImageFilter.SHARPEN)


def player_variant(source: Image.Image, target: tuple[int, int, int]) -> Image.Image:
    result = source.copy().convert("RGB")
    pixels = result.load()
    target_hue, target_sat, _target_value = colorsys.rgb_to_hsv(
        target[0] / 255.0,
        target[1] / 255.0,
        target[2] / 255.0,
    )
    for y in range(result.height):
        for x in range(result.width):
            red, green, blue = pixels[x, y]
            hue, saturation, value = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
            if blue > 55 and blue > red * 1.30 and blue > green * 1.10 and saturation > 0.34:
                saturation = max(0.58, min(0.92, saturation * target_sat / 0.75))
                new_red, new_green, new_blue = colorsys.hsv_to_rgb(target_hue, saturation, value)
                pixels[x, y] = (round(new_red * 255), round(new_green * 255), round(new_blue * 255))
    return result


def write_tile(path: Path, tile: bytes) -> None:
    path.write_bytes(tile)
    if len(tile) < 26:
        raise ValueError(f"Generated TILE is truncated: {path}")


def generate(game_path: Path) -> None:
    for path in (SOURCE_INTERFACE, SOURCE_WORLD):
        if not path.is_file():
            raise FileNotFoundError(path)
    stock = load_stock_pipeline()
    source_cam = game_path / "Data" / "maindata.cam"
    interface_cam = game_path / "Data" / "interfacedata.cam"
    stock.read_cam_entry(source_cam, b"IMAG", STOCK_IMAGE)
    stock.read_cam_entry(interface_cam, b"IMAG", STOCK_BUTTON_IMAGE)
    tiles = stock.read_cam_entries(source_cam, b"TILE")
    palettes = stock.read_cam_entries(source_cam, b"SPLT")
    interface_tiles = stock.read_cam_entries(interface_cam, b"TILE")
    if len(tiles) <= STOCK_INTERFACE_TILES[-1] or len(palettes) <= CAPTURE_WORLD_PALETTE:
        raise ValueError(f"Stock flag art tables are incomplete in {source_cam}")
    if len(interface_tiles) <= STOCK_BUTTON_TILE:
        raise ValueError(f"Stock Capture button art is missing from {interface_cam}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    green, gold = master_palette()
    world_frames: list[Image.Image] = []
    for frame, source_index in enumerate(STOCK_SPECIAL_TILES):
        source = render_indexed_v3(stock, tiles[source_index].data, palettes)
        image = capture_world_frame(source, green, gold)
        world_frames.append(image)
        png_path = OUTPUT_DIR / f"special-{frame:02d}.png"
        image.save(png_path)
        template = stock.remap_tile_palette_index(
            tiles[source_index].data,
            CAPTURE_WORLD_PALETTE,
        )
        write_tile(
            OUTPUT_DIR / f"special-{frame:02d}.tile",
            stock.tile_from_png_native_size(template, palettes, png_path),
        )

    for frame, source_index in enumerate(STOCK_MINIMAP_TILES):
        source = render_indexed_v3(stock, tiles[source_index].data, palettes)
        image = capture_minimap_frame(source, green, gold)
        png_path = OUTPUT_DIR / f"minimap-{frame:02d}.png"
        image.save(png_path)
        template = stock.remap_tile_palette_index(
            tiles[source_index].data,
            CAPTURE_WORLD_PALETTE,
        )
        write_tile(
            OUTPUT_DIR / f"minimap-{frame:02d}.tile",
            stock.tile_from_png_native_size(template, palettes, png_path),
        )

    master = interface_master()
    variants: list[Image.Image] = []
    for frame, (source_index, player_color) in enumerate(zip(STOCK_INTERFACE_TILES, PLAYER_COLORS)):
        image = player_variant(master, player_color)
        variants.append(image)
        png_path = OUTPUT_DIR / f"interface-{frame:02d}.png"
        image.save(png_path)
        write_tile(
            OUTPUT_DIR / f"interface-{frame:02d}.tile",
            stock.tile_from_rgb(tiles[source_index].data, palettes, image.tobytes()),
        )

    button_template = interface_tiles[STOCK_BUTTON_TILE].data
    button = capture_button_icon(render_embedded_v1(stock, button_template), green, gold)
    button.save(OUTPUT_DIR / "capture-button-icon-25.png")
    write_tile(
        OUTPUT_DIR / "capture-button-icon-25.tile",
        embedded_v1_from_rgba(button_template, button),
    )

    preview = Image.new("RGB", (400, 100), (22, 22, 22))
    for frame, image in enumerate(variants):
        preview.paste(image, (frame * 100, 0))
    preview.save(OUTPUT_DIR / "capture-flag-interface-preview.png")

    scale = 8
    world_preview = Image.new("RGB", (35 * scale * 4, 42 * scale * 3), (32, 32, 32))
    for frame, image in enumerate(world_frames):
        enlarged = image.resize(
            (image.width * scale, image.height * scale),
            Image.Resampling.NEAREST,
        )
        world_preview.paste(
            enlarged,
            ((frame % 4) * 35 * scale, (frame // 4) * 42 * scale),
            enlarged,
        )
    world_preview.save(OUTPUT_DIR / "capture-flag-world-preview.png")
    print(
        "Generated 12 world, 4 minimap, 4 interface, and 1 button "
        f"Capture Flag frames in {OUTPUT_DIR}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the private Zoo Capture Flag art")
    parser.add_argument("--game-path", type=Path, required=True)
    args = parser.parse_args()
    generate(args.game_path.resolve())


if __name__ == "__main__":
    main()
