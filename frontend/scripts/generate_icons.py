#!/usr/bin/env python3
"""Generate the Flash PWA icons from the brand logo (TASK-007).

Run from `frontend/` whenever `docs/design/flash_initial_logo.png` changes:

    python3 scripts/generate_icons.py

Needs Python 3 + Pillow on the build machine only. The generated files are
committed, so `npm ci && npm run build` does not need Python.
The 1254 px original is never shipped in the app bundle.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent
SOURCE = FRONTEND.parent / "docs" / "design" / "flash_initial_logo.png"
ICONS = FRONTEND / "public" / "icons"
ASSETS = FRONTEND / "src" / "assets"

WHITE = (255, 255, 255, 255)
# Bounding box of the "F" mark (speed lines + bolt) in the 1254 px source.
MARK_BOX = (285, 260, 965, 694)


def square_on_white(mark: Image.Image, size: int, content_ratio: float) -> Image.Image:
    """Centre `mark` on a white square; the mark's longest side = size * content_ratio."""
    canvas = Image.new("RGBA", (size, size), WHITE)
    scale = (size * content_ratio) / max(mark.size)
    w, h = round(mark.width * scale), round(mark.height * scale)
    resized = mark.resize((w, h), Image.LANCZOS)
    canvas.paste(resized, ((size - w) // 2, (size - h) // 2), resized)
    return canvas


def main() -> None:
    src = Image.open(SOURCE).convert("RGBA")
    mark = src.crop(MARK_BOX)
    ICONS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    # "any" purpose icons: mark fills ~84 % of the square.
    square_on_white(mark, 192, 0.84).convert("RGB").save(ICONS / "icon-192.png", optimize=True)
    square_on_white(mark, 512, 0.84).convert("RGB").save(ICONS / "icon-512.png", optimize=True)
    # Maskable: keep the mark inside the 80 % safe zone (~60 % to be safe on circles).
    square_on_white(mark, 512, 0.60).convert("RGB").save(
        ICONS / "maskable-512.png", optimize=True
    )
    square_on_white(mark, 180, 0.80).convert("RGB").save(
        ICONS / "apple-touch-icon-180.png", optimize=True
    )
    fav = square_on_white(mark, 256, 0.92).convert("RGB")
    fav.save(FRONTEND / "public" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    # Full lockup (mark + wordmark + Arabic tagline) for the login screen, 480 px wide.
    lockup = src.crop((180, 250, 1074, 1040))
    ratio = 480 / lockup.width
    lockup = lockup.resize((480, round(lockup.height * ratio)), Image.LANCZOS)
    # Adaptive 128-colour palette keeps the file small for the app shell.
    lockup.convert("RGB").quantize(colors=128, method=Image.MEDIANCUT).save(
        ASSETS / "flash-logo.png", optimize=True
    )


if __name__ == "__main__":
    main()
