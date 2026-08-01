#!/usr/bin/env python3
"""Replace Bazzite's Icons-Only Task Manager pins with Arcalium's.

The pins a new user gets come from the panel layout template, which runs when
Plasma first creates the panel. Update scripts under shells/.../updates/ run
afterwards and all guard on `launchers` being empty, so by the time they run the
template has already filled it in and they do nothing. Shipping our own update
script therefore had no effect: fresh installs came up with Bazzite's list, with
`preferred://browser` resolving to Brave and none of our bundled apps present.

Every writer of the list is patched so the value cannot depend on ordering.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

# The order here is the left-to-right order of the pins.
#
# The browser slot stays `preferred://browser` rather than naming Brave's
# desktop file. It resolves through our mimeapps.list default and is the one
# entry already confirmed to pin correctly on a fresh install.
#
# The Control Centre is deliberately absent. Its icon is the Arcalium mark, the
# same artwork as the Kickoff launcher at the far left of the panel, so pinning
# it put two identical marks side by side. It stays in the Kickoff favourites,
# where there is no adjacency to the launcher button.
#
# ProtonPlus is also absent from the panel: it is a setup/utility tool, not a
# daily launcher, so it belongs in Kickoff favourites rather than Icon Tasks.
LAUNCHERS = [
    "preferred://filemanager",
    "applications:io.github.kolunmi.Bazaar.desktop",
    "preferred://browser",
    "applications:com.heroicgameslauncher.hgl.desktop",
    "applications:com.spotify.Client.desktop",
]

# The template is authoritative; the update script is patched defensively so it
# cannot reapply Bazzite's list (which still names Lutris, removed from the
# catalogue) if it ever sees an empty value.
REQUIRED = Path(
    "/usr/share/plasma/layout-templates"
    "/org.kde.plasma.desktop.defaultPanel/contents/layout.js"
)
OPTIONAL = [
    Path(
        "/usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates"
        "/bazzite-pins.js"
    ),
]

CALL = re.compile(r'widget\.writeConfig\("launchers",\s*\[.*?\]\);', re.S)


def render(indent: str) -> str:
    body = ",\n".join(f'{indent}    "{entry}"' for entry in LAUNCHERS)
    return f'widget.writeConfig("launchers", [\n{body}\n{indent}]);'


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    matches = list(CALL.finditer(text))
    if not matches:
        return False
    if len(matches) != 1:
        sys.exit(f"ERROR: {path} has {len(matches)} launcher writes, expected 1")

    match = matches[0]
    line_start = text.rfind("\n", 0, match.start()) + 1
    indent = text[line_start : match.start()]
    if indent.strip():
        sys.exit(f"ERROR: {path} launcher write is not at the start of a line")

    patched = text[: match.start()] + render(indent) + text[match.end() :]
    path.write_text(patched, encoding="utf-8", newline="\n")

    for entry in LAUNCHERS:
        if f'"{entry}"' not in path.read_text(encoding="utf-8"):
            sys.exit(f"ERROR: {path} is missing {entry} after patching")
    print(f"patched {path}")
    return True


def main() -> None:
    if not REQUIRED.is_file():
        sys.exit(f"ERROR: {REQUIRED} is missing; upstream moved the panel template")
    if not patch(REQUIRED):
        sys.exit(f"ERROR: {REQUIRED} no longer writes a launchers list")

    for path in OPTIONAL:
        if path.is_file():
            patch(path)


if __name__ == "__main__":
    main()
