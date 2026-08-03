#!/usr/bin/env python3
"""Generate Space Invaders-style pixel-art icon for Local AI Assistant."""

from pathlib import Path

from PIL import Image

# 16x16 crab/alien face — classic invader silhouette
ROWS = [
    "................",
    "......WWWW......",
    "....WWWWWWWW....",
    "...WWWWWWWWWW...",
    "..WW.WWWWWW.WW..",
    "..WWWWWWWWWWWW..",
    "..WWWTTWWTTWWW..",
    "..WWWTTWWTTWWW..",
    ".WWWWWWWWWWWWWW.",
    ".WW.WWWWWWWW.WW.",
    ".WW.WWWWWWWW.WW.",
    "....WWW..WWW....",
    "...WW......WW...",
    "..WW........WW..",
    "................",
    "................",
]

PALETTE = {
    ".": (26, 29, 36, 255),
    "W": (245, 248, 250, 255),
    "T": (46, 196, 182, 255),
}


def main() -> None:
    h = len(ROWS)
    w = len(ROWS[0])
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y, row in enumerate(ROWS):
        for x, ch in enumerate(row):
            px[x, y] = PALETTE[ch]

    repo = Path(__file__).resolve().parents[1] / "assets"
    repo.mkdir(parents=True, exist_ok=True)

    master = img.resize((512, 512), Image.Resampling.NEAREST)
    path = repo / "io.arcalium.Assistant.png"
    master.save(path, "PNG")
    print(f"wrote {path} ({path.stat().st_size} bytes)")

    for size in (256, 128, 64, 48):
        scaled = img.resize((size, size), Image.Resampling.NEAREST)
        out = repo / f"io.arcalium.Assistant-{size}.png"
        scaled.save(out, "PNG")
        print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
