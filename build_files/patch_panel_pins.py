#!/usr/bin/env python3
"""Replace Bazzite's Icons-Only Task Manager pins with Arcalium's.

The pins a new user gets come from the panel layout template, which runs when
Plasma first creates the panel. Update scripts under shells/.../updates/ run
afterwards and all guard on `launchers` being empty, so by the time they run the
template has already filled it in and they do nothing. Shipping our own update
script therefore had no effect: fresh installs came up with Bazzite's list, with
`preferred://browser` resolving to Firefox and none of our bundled apps present.

Every writer of the list is patched so the value cannot depend on ordering.

Also force the Kickoff (application launcher) button icon to an absolute Arcalium
PNG. Theme-name lookup (start-here-kde) is fragile after re-pins — Breeze caches,
symbolic colouring, and leftover customButtonImage paths often leave a blank mark.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

# The order here is the left-to-right order of the pins.
#
# The browser slot stays `preferred://browser` rather than naming Firefox's
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
#
# Brave and Spotify are not pinned: they are Flathub install-on-demand (like
# Steam), not bundled in the ISO.
LAUNCHERS = [
    "preferred://filemanager",
    "applications:io.github.kolunmi.Bazaar.desktop",
    "preferred://browser",
    "applications:com.heroicgameslauncher.hgl.desktop",
]

# Absolute file:// path — skips icon-theme resolution entirely.
KICKOFF_ICON = "file:///usr/share/arcalium/kickoff-icon.png"

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
ADD_KICKOFF = re.compile(
    r'(?P<var>[A-Za-z_][\w]*)\s*=\s*[^;]*addWidget\(\s*"org\.kde\.plasma\.kickoff"\s*\)'
)
ICON_WRITE = re.compile(
    r'(?P<var>[A-Za-z_][\w]*)\.writeConfig\(\s*"icon"\s*,\s*"[^"]*"\s*\)'
)
ICON_NAME_WRITE = re.compile(
    r'\.writeConfig\(\s*"icon"\s*,\s*"(?:start-here[^"]*|distributor-logo[^"]*|bazzite[^"]*)"\s*\)'
)


def render_launchers(indent: str) -> str:
    body = ",\n".join(f'{indent}    "{entry}"' for entry in LAUNCHERS)
    return f'widget.writeConfig("launchers", [\n{body}\n{indent}]);'


def patch_launchers(path: Path, text: str) -> str:
    matches = list(CALL.finditer(text))
    if not matches:
        return text
    if len(matches) != 1:
        sys.exit(f"ERROR: {path} has {len(matches)} launcher writes, expected 1")

    match = matches[0]
    line_start = text.rfind("\n", 0, match.start()) + 1
    indent = text[line_start : match.start()]
    if indent.strip():
        sys.exit(f"ERROR: {path} launcher write is not at the start of a line")

    patched = text[: match.start()] + render_launchers(indent) + text[match.end() :]
    for entry in LAUNCHERS:
        if f'"{entry}"' not in patched:
            sys.exit(f"ERROR: {path} is missing {entry} after patching")
    print(f"patched launchers in {path}")
    return patched


def patch_kickoff_icon(path: Path, text: str) -> str:
    """Point Kickoff at the Arcalium absolute icon path."""
    # Rewrite any start-here / distributor / bazzite icon config strings.
    text2, n_name = ICON_NAME_WRITE.subn(
        f'.writeConfig("icon", "{KICKOFF_ICON}")', text
    )
    if n_name:
        print(f"rewrote {n_name} Kickoff-style icon write(s) in {path}")

    # Ensure each kickoff widget gets an explicit icon writeConfig.
    inserts: list[tuple[int, str]] = []
    for match in ADD_KICKOFF.finditer(text2):
        var = match.group("var")
        # Look ahead ~12 lines for an icon write on this var.
        window = text2[match.end() : match.end() + 800]
        if re.search(rf'{re.escape(var)}\.writeConfig\(\s*"icon"', window):
            # Already has icon= — normalize to our path if still a theme name.
            continue
        line_start = text2.rfind("\n", 0, match.start()) + 1
        indent = text2[line_start : match.start()]
        inserts.append(
            (
                match.end(),
                f'\n{indent}{var}.writeConfig("icon", "{KICKOFF_ICON}");',
            )
        )

    if inserts:
        out = text2
        # Insert from the end so offsets stay valid.
        for pos, snippet in sorted(inserts, key=lambda t: t[0], reverse=True):
            out = out[:pos] + snippet + out[pos:]
        print(f"injected Kickoff icon write(s) in {path}")
        text2 = out

    # Normalize any remaining icon writes on kickoff vars to our path.
    kickoff_vars = {m.group("var") for m in ADD_KICKOFF.finditer(text2)}
    if kickoff_vars:

        def repl(m: re.Match[str]) -> str:
            if m.group("var") in kickoff_vars:
                return f'{m.group("var")}.writeConfig("icon", "{KICKOFF_ICON}")'
            return m.group(0)

        text2, n = ICON_WRITE.subn(repl, text2)
        if n:
            print(f"normalized {n} Kickoff icon write(s) in {path}")

    if KICKOFF_ICON not in text2 and "org.kde.plasma.kickoff" in text2:
        sys.exit(
            f"ERROR: {path} mentions kickoff but has no Arcalium kickoff icon path"
        )
    return text2


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    if CALL.search(text):
        text = patch_launchers(path, text)
    if "org.kde.plasma.kickoff" in text:
        text = patch_kickoff_icon(path, text)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path}")
    return True


def main() -> None:
    if not REQUIRED.is_file():
        sys.exit(f"ERROR: {REQUIRED} is missing; upstream moved the panel template")
    if not patch(REQUIRED):
        # Still require launcher patch on the template.
        text = REQUIRED.read_text(encoding="utf-8")
        if not CALL.search(text):
            sys.exit(f"ERROR: {REQUIRED} no longer writes a launchers list")
        sys.exit(f"ERROR: {REQUIRED} was not modified")

    for path in OPTIONAL:
        if path.is_file():
            patch(path)


if __name__ == "__main__":
    main()
