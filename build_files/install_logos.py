#!/usr/bin/env python3
"""Install cleaned Arcalium logo SVGs into the image.

Strips Adobe Illustrator private metadata (the aipgf CDATA blob) which is not
needed for rendering and bloats the files ~10×. Sources stay in /ctx/assets/.

Also overwrites start-here / distributor-logo icons in every installed icon
theme (Breeze takes precedence over hicolor for Kickoff).
"""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import sys


def clean_svg(src: Path, element_id: str) -> str:
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"<metadata>.*?</metadata>\s*", "", text, flags=re.S)
    text = re.sub(r'\s+xmlns:i="[^"]*"', "", text)
    text = re.sub(r"\s*<!-- Generator:.*?-->\s*", "\n", text)
    text = re.sub(r'id="Layer_1"', f'id="{element_id}"', text, count=1)
    return text.replace("\r\n", "\n").strip() + "\n"


def write_svg(src: Path, dst: Path, element_id: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(clean_svg(src, element_id), encoding="utf-8", newline="\n")
    print(f"installed {dst} ({dst.stat().st_size} bytes)")


# Kickoff / menu button names Plasma and Fedora/Bazzite commonly resolve.
PLACE_NAMES = (
    "distributor-logo.svg",
    "distributor-logo-white.svg",
    "distributor-logo-symbolic.svg",
    "distributor-logo-steamdeck.svg",
    "start-here-kde.svg",
    "start-here.svg",
    "start-here-symbolic.svg",
)


def main() -> int:
    assets = Path(sys.argv[1] if len(sys.argv) > 1 else "/ctx/assets")
    mark = assets / "arccleanSVG.svg"
    wordmark = assets / "ARG_fullSVG.svg"
    if not mark.is_file() or not wordmark.is_file():
        print(f"missing logo SVGs under {assets}", file=sys.stderr)
        return 1

    places = Path("/usr/share/icons/hicolor/scalable/places")
    arcalium = Path("/usr/share/arcalium")
    icons_root = Path("/usr/share/icons")

    for name in PLACE_NAMES:
        write_svg(mark, places / name, "arcalium-mark")

    write_svg(mark, arcalium / "logo-mark.svg", "arcalium-mark")
    write_svg(wordmark, arcalium / "logo-wordmark.svg", "arcalium-wordmark")

    apps = Path("/usr/share/icons/hicolor/scalable/apps")
    write_svg(mark, apps / "arcalium-logo.svg", "arcalium-mark")
    write_svg(wordmark, apps / "arcalium-wordmark.svg", "arcalium-wordmark")

    # Breeze ships its own start-here-kde; Kickoff prefers the active icon theme
    # over hicolor. Overwrite scalable place icons in every theme. Raster PNGs are
    # mirrored from hicolor in build.sh after ImageMagick renders them.
    replaced = 0
    if icons_root.is_dir():
        for places_dir in icons_root.rglob("places"):
            if not places_dir.is_dir():
                continue
            if "scalable" not in places_dir.parts:
                continue
            for name in PLACE_NAMES:
                write_svg(mark, places_dir / name, "arcalium-mark")
                replaced += 1
    print(f"icon theme place overrides: {replaced} SVG files")

    if shutil.which("gtk-update-icon-cache"):
        Path("/usr/share/icons/hicolor/index.theme").touch(exist_ok=True)
        for theme_dir in sorted(icons_root.iterdir()):
            if theme_dir.is_dir() and (theme_dir / "index.theme").is_file():
                subprocess.run(
                    ["gtk-update-icon-cache", "-f", str(theme_dir)],
                    check=False,
                    capture_output=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
