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
PNG. Upstream uses a bare panel.addWidget("org.kde.plasma.kickoff") with no
config — theme-name lookup goes blank after re-pins.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

LAUNCHERS = [
    "preferred://filemanager",
    "applications:io.github.kolunmi.Bazaar.desktop",
    "preferred://browser",
    "applications:com.heroicgameslauncher.hgl.desktop",
]

KICKOFF_ICON = "file:///usr/share/arcalium/kickoff-icon.png"

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

# Stock Plasma / Bazzite: no assignment, no trailing semicolon.
# Do not use \s* after ) — that would swallow the following newline.
BARE_KICKOFF = re.compile(
    r'(?P<indent>[ \t]*)panel\.addWidget\(\s*"org\.kde\.plasma\.kickoff"\s*\)[ \t]*;?'
)

ASSIGNED_KICKOFF = re.compile(
    r'(?P<indent>[ \t]*)(?:var|let|const)\s+(?P<var>[A-Za-z_][\w]*)\s*=\s*'
    r'panel\.addWidget\(\s*"org\.kde\.plasma\.kickoff"\s*\)[ \t]*;?'
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


def _kickoff_block(indent: str, var: str = "arcaliumKickoff") -> str:
    return (
        f'{indent}var {var} = panel.addWidget("org.kde.plasma.kickoff")\n'
        f'{indent}{var}.currentConfigGroup = ["General"]\n'
        f'{indent}{var}.writeConfig("icon", "{KICKOFF_ICON}")'
    )


def patch_kickoff_icon(path: Path, text: str) -> str:
    """Point Kickoff at the Arcalium absolute icon path."""
    if "org.kde.plasma.kickoff" not in text:
        return text

    # 1) Assigned form: keep the variable name, ensure icon write follows.
    def repl_assigned(m: re.Match[str]) -> str:
        indent, var = m.group("indent"), m.group("var")
        return (
            f'{indent}var {var} = panel.addWidget("org.kde.plasma.kickoff")\n'
            f'{indent}{var}.currentConfigGroup = ["General"]\n'
            f'{indent}{var}.writeConfig("icon", "{KICKOFF_ICON}")'
        )

    text2, n_assigned = ASSIGNED_KICKOFF.subn(repl_assigned, text)
    if n_assigned:
        print(f"rewrote {n_assigned} assigned Kickoff addWidget(s) in {path}")

    # 2) Bare form (what Bazzite / stock Plasma ship).
    text2, n_bare = BARE_KICKOFF.subn(
        lambda m: _kickoff_block(m.group("indent")), text2
    )
    if n_bare:
        print(f"rewrote {n_bare} bare Kickoff addWidget(s) in {path}")

    # 3) Also append a panels() pass so existing-panel update scripts set the icon.
    if KICKOFF_ICON not in text2:
        # Last resort: append a small loop (e.g. pins-only update scripts).
        appendix = f"""
// Arcalium: force Kickoff launcher icon (absolute path — survives theme resets).
{{
    const _arcaliumPanels = panels();
    for (let _i = 0; _i < _arcaliumPanels.length; ++_i) {{
        const _widgets = _arcaliumPanels[_i].widgets();
        for (let _j = 0; _j < _widgets.length; ++_j) {{
            const _w = _widgets[_j];
            if (_w.type === "org.kde.plasma.kickoff") {{
                _w.currentConfigGroup = ["General"];
                _w.writeConfig("icon", "{KICKOFF_ICON}");
                _w.reloadConfig();
            }}
        }}
    }}
}}
"""
        text2 = text2.rstrip() + "\n" + appendix
        print(f"appended Kickoff icon loop in {path}")

    if KICKOFF_ICON not in text2:
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
        text = REQUIRED.read_text(encoding="utf-8")
        if not CALL.search(text):
            sys.exit(f"ERROR: {REQUIRED} no longer writes a launchers list")
        sys.exit(f"ERROR: {REQUIRED} was not modified")

    for path in OPTIONAL:
        if path.is_file():
            patch(path)


if __name__ == "__main__":
    main()
