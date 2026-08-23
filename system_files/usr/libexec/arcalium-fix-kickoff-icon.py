#!/usr/bin/env python3
"""Force Kickoff panel button to the Arcalium absolute icon path.

Existing user profiles often keep a theme name (start-here-kde) or a custom
file:// path that broke after a re-pin — Kickoff then shows a blank mark.

Global Theme / look-and-feel applies also reset Kickoff back to start-here-kde.
This script is idempotent and safe to run on every login (autostart + cleanup).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

KICKOFF_ICON = "file:///usr/share/arcalium/kickoff-icon.png"
APPLETRC = Path.home() / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"


def fix_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if line.strip() == "plugin=org.kde.plasma.kickoff":
            i += 1
            # Walk this applet's following sections/keys looking for General.
            while i < len(lines):
                cur = lines[i]
                if cur.startswith("[") and "Configuration][General" in cur:
                    out.append(cur)
                    i += 1
                    has_icon = False
                    general: list[str] = []
                    while i < len(lines) and not lines[i].startswith("["):
                        keyline = lines[i]
                        if keyline.startswith("icon="):
                            nl = "\n" if keyline.endswith("\n") else ""
                            general.append(f"icon={KICKOFF_ICON}{nl}")
                            has_icon = True
                        elif keyline.startswith("customButtonImage="):
                            pass  # drop broken custom art
                        elif keyline.startswith("useCustomButtonImage="):
                            nl = "\n" if keyline.endswith("\n") else ""
                            general.append(f"useCustomButtonImage=false{nl}")
                        else:
                            general.append(keyline)
                        i += 1
                    if not has_icon:
                        general.insert(0, f"icon={KICKOFF_ICON}\n")
                    out.extend(general)
                    continue
                # Next applet / containment — stop Kickoff-specific walk.
                if cur.startswith("[") and "[Applets]" in cur and "Configuration" not in cur:
                    break
                if cur.strip().startswith("plugin=") and "kickoff" not in cur:
                    break
                out.append(cur)
                i += 1
            continue
        i += 1

    updated = "".join(out)
    # Belt-and-suspenders: any leftover theme-name Kickoff icons elsewhere.
    updated = re.sub(
        r"(?m)^icon=(start-here\S*|distributor-logo\S*|bazzite\S*)?$",
        f"icon={KICKOFF_ICON}",
        updated,
    )
    updated = re.sub(
        r"(?m)^useCustomButtonImage=true$",
        "useCustomButtonImage=false",
        updated,
    )
    return updated


def main() -> int:
    if not APPLETRC.is_file():
        return 0
    if not Path("/usr/share/arcalium/kickoff-icon.png").is_file():
        # Image not in this deployment yet — nothing useful to point at.
        return 0
    original = APPLETRC.read_text(encoding="utf-8")
    if "org.kde.plasma.kickoff" not in original:
        return 0
    updated = fix_text(original)
    if updated != original:
        APPLETRC.write_text(updated, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
