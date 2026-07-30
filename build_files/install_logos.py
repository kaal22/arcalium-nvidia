#!/usr/bin/env python3
"""Install cleaned Arcalium logo SVGs into the image.

Strips Adobe Illustrator private metadata (the aipgf CDATA blob) which is not
needed for rendering and bloats the files ~10×. Sources stay in /ctx/assets/.
"""

from __future__ import annotations

from pathlib import Path
import re
import shutil
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


def main() -> int:
    assets = Path(sys.argv[1] if len(sys.argv) > 1 else "/ctx/assets")
    mark = assets / "arccleanSVG.svg"
    wordmark = assets / "ARG_fullSVG.svg"
    if not mark.is_file() or not wordmark.is_file():
        print(f"missing logo SVGs under {assets}", file=sys.stderr)
        return 1

    places = Path("/usr/share/icons/hicolor/scalable/places")
    arcalium = Path("/usr/share/arcalium")

    # Application menu / distributor mark (white fill — matches dark Plasma panels).
    write_svg(mark, places / "distributor-logo.svg", "arcalium-mark")
    write_svg(mark, places / "distributor-logo-white.svg", "arcalium-mark-white")
    write_svg(mark, places / "start-here-kde.svg", "arcalium-start-here")
    # Keep canonical copies for splash, Plymouth watermark and docs to reference later.
    write_svg(mark, arcalium / "logo-mark.svg", "arcalium-mark")
    write_svg(wordmark, arcalium / "logo-wordmark.svg", "arcalium-wordmark")

    # Also mirror under applications so Kickoff and About pages can find them.
    apps = Path("/usr/share/icons/hicolor/scalable/apps")
    write_svg(mark, apps / "arcalium-logo.svg", "arcalium-mark")
    write_svg(wordmark, apps / "arcalium-wordmark.svg", "arcalium-wordmark")

    # Refresh icon cache if the helper is present (bootc image build is offline-safe).
    if shutil.which("gtk-update-icon-cache"):
        Path("/usr/share/icons/hicolor/index.theme").touch(exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
