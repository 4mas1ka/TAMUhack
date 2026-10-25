"""Image loading helpers for Rev's Creamery.

Every image is prepared with Pillow at start-up (cropped / resized once), so the game just
draws it 1:1 every frame. If an image file is missing the loaders return None / {} and
game.py falls back to simple shapes instead of crashing.

Images are looked for next to this file, then in an "assets" folder, then in an "images" folder.
"""
from pathlib import Path

import arcade
from PIL import Image

from pixel_font import render_pixel_text

BASE_DIR = Path(__file__).resolve().parent
SEARCH_DIRS = [BASE_DIR, BASE_DIR / "assets", BASE_DIR / "images"]


class Art:
    """A ready-to-draw texture plus its size in pixels."""

    def __init__(self, texture, width, height, avatar=None, avatar_small=None):
        self.texture = texture
        self.width = width
        self.height = height
        self.avatar = avatar              # 64x64 face portrait (build screen)
        self.avatar_small = avatar_small  # 40x40 face portrait (waiting strip)


# ---------------- low-level helpers ----------------
def find_asset(*names):
    """Return the first existing file matching any of `names`, or None."""
    for folder in SEARCH_DIRS:
        for name in names:
            path = folder / name
            if path.is_file():
                return path
    return None


def open_image(*names):
    path = find_asset(*names)
    if path is None:
        print(f"[assets] could not find any of: {', '.join(names)}")
        return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception as error:  # a corrupt file should not crash the game
        print(f"[assets] could not read {path}: {error}")
        return None


def to_texture(image):
    return arcade.Texture(image.convert("RGBA"))


def cover_resize(image, size, anchor_y=0.5):
    """Scale `image` to fill `size` without stretching, cropping the overflow.

    anchor_y: 0.0 keeps the top of the picture, 1.0 keeps the bottom.
    """
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    new_w = max(target_w, round(image.width * scale))
    new_h = max(target_h, round(image.height * scale))
    # Upscaling keeps hard pixel edges; downscaling uses a smooth filter.
    method = Image.NEAREST if scale >= 1 else Image.LANCZOS
    resized = image.resize((new_w, new_h), method)
    left = (new_w - target_w) // 2
    top = round((new_h - target_h) * anchor_y)
    return resized.crop((left, top, left + target_w, top + target_h))


# ---------------- loaders used by game.py ----------------
def load_background(names, size, anchor_y=0.5):
    image = open_image(*names)
    if image is None:
        return None
    return Art(to_texture(cover_resize(image, size, anchor_y)), size[0], size[1])


def load_counter(names, size, rows=92):
    """The counter is the wooden-plank strip at the top of wood.png, stretched across the screen."""
    image = open_image(*names)
    if image is None:
        return None
    strip = image.crop((0, 0, image.width, min(rows, image.height)))
    strip = strip.resize(size, Image.NEAREST)
    return Art(to_texture(strip), size[0], size[1])


def load_characters(definitions, max_height):
    """Load every customer sprite at one shared scale (so a dog stays smaller than a person).

    `definitions` is a list of dicts with a "key" and a tuple of candidate "files".
    Returns {key: Art}. Characters whose file is missing are simply left out.
    """
    sprites = {}
    for definition in definitions:
        image = open_image(*definition["files"])
        if image is None:
            continue
        box = image.getchannel("A").getbbox()  # trim the transparent margin
        if box:
            image = image.crop(box)
        sprites[definition["key"]] = image

    if not sprites:
        return {}

    scale = max_height / max(image.height for image in sprites.values())
    art = {}
    for key, image in sprites.items():
        width = max(1, round(image.width * scale))
        height = max(1, round(image.height * scale))
        sprite = image.resize((width, height), Image.LANCZOS)

        # Portrait = a square cut from the top of the sprite (head and shoulders).
        face = image.crop((0, 0, image.width, min(image.height, image.width)))
        art[key] = Art(
            to_texture(sprite),
            width,
            height,
            avatar=to_texture(face.resize((64, 64), Image.LANCZOS)),
            avatar_small=to_texture(face.resize((40, 40), Image.LANCZOS)),
        )
    return art


def load_trophy(names, size):
    image = open_image(*names)
    if image is None:
        return None
    image = image.resize((size, size), Image.NEAREST)
    return Art(to_texture(image), size, size)


def pixel_text_art(text, scale, fill, outline=(0, 0, 0), shadow=(0, 0, 0, 120)):
    """Title-style text drawn with the built-in pixel font."""
    image = render_pixel_text(text, scale=scale, fill=fill, outline=outline, shadow=shadow)
    return Art(to_texture(image), image.width, image.height)
