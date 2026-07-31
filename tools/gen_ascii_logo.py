"""Generate the Konsole welcome art at system_files/usr/share/arcalium/logo.txt.

The art is an "A" drawn from '#' with a dotted stipple along its edges, crossed
by a brighter swoosh that rises from the lower-left and tapers off to the
upper-right — the shape of assets/arccleanSVG.svg in the ASCII style of
assets/banana-gen-1785489379086.png.

Colour slots resolve through system_files/usr/share/arcalium/fastfetch.jsonc:
1 = white (swoosh), 3 = cyan (the A), 5 = light_blue (stipple).

    python tools/gen_ascii_logo.py system_files/usr/share/arcalium/logo.txt

Prints a colour-code-free copy to stdout for eyeballing proportions. Tweak the
geometry constants below and re-run; the file is plain text, so hand-editing the
result afterwards is equally valid.
"""

from __future__ import annotations

import math
import sys

WIDTH = 38
ART_ROWS = 14
APEX_L, APEX_R = 15, 16  # the two columns of the apex
LEG_W = 4  # stroke thickness of each leg

ARC_C0, ARC_C1 = 1, 34  # column span of the swoosh
ARC_BOTTOM = 13.0  # row the swoosh starts from, bottom-left
ARC_K = 1.414  # larger = shallower rise
ARC_TOP_ROW = 5  # row the swoosh exits on the right

FILL = "3"
EDGE = "5"
SWOOSH = "1"

MODE = sys.argv[2] if len(sys.argv) > 2 else "filled"

grid = [[" "] * WIDTH for _ in range(ART_ROWS)]
colour: list[list[str | None]] = [[None] * WIDTH for _ in range(ART_ROWS)]


def put(r: int, c: int, ch: str, col: str, over: bool = True) -> None:
    if not (0 <= r < ART_ROWS and 0 <= c < WIDTH):
        return
    if not over and grid[r][c] != " ":
        return
    grid[r][c] = ch
    colour[r][c] = col


def left_edge(r: int) -> int:
    return APEX_L - r


def right_edge(r: int) -> int:
    return APEX_R + r


def in_leg(r: int, c: int) -> bool:
    lo, hi = left_edge(r), right_edge(r)
    return c < lo + LEG_W or c > hi - LEG_W


def arc_top(c: int) -> float:
    if c < ARC_C0:
        return 99.0
    return ARC_BOTTOM - ARC_K * math.sqrt(c - ARC_C0)


def arc_col(r: float) -> float:
    return ARC_C0 + ((ARC_BOTTOM - r) / ARC_K) ** 2


def counter_half_width(r: int) -> int:
    """Half-width of the hole inside the A, opening downward from the apex."""
    return int((r - 3) * 1.6) if r >= 3 else -1


# --- the A -------------------------------------------------------------
for r in range(ART_ROWS):
    lo, hi = left_edge(r), right_edge(r)
    for c in range(lo, hi + 1):
        leg = in_leg(r, c)
        if MODE == "outline":
            if not leg:
                continue
        else:
            if not (leg or r <= arc_top(c)):
                continue
            half = counter_half_width(r)
            if half >= 0 and not leg and APEX_L - half <= c <= APEX_R + half:
                continue
        put(r, c, "#", FILL)

# --- stipple just outside the A ---------------------------------------
for r in range(1, ART_ROWS):
    put(r, left_edge(r) - 1, ".", EDGE, over=False)
    put(r, right_edge(r) + 1, ".", EDGE, over=False)
for r in range(2, ART_ROWS):
    put(r, left_edge(r) - 2, ":" if r % 2 else ".", EDGE, over=False)
    put(r, right_edge(r) + 2, ":" if r % 2 else ".", EDGE, over=False)

# --- the swoosh --------------------------------------------------------
# Built row by row rather than column by column: each row gets one contiguous
# horizontal run, which is what makes a curve read cleanly in text.
for r in range(ARC_TOP_ROW, int(ARC_BOTTOM) + 1):
    c_start = int(round(arc_col(r)))
    c_end = ARC_C1 if r == ARC_TOP_ROW else int(round(arc_col(r - 1))) - 1
    for c in range(c_start, min(c_end, ARC_C1) + 1):
        put(r, c, "#", SWOOSH)
        put(r + 1, c, "#", SWOOSH)

# Stipple the swoosh's tail where it leaves the A, so it tapers instead of
# ending on a hard character.
for r in range(ARC_TOP_ROW, min(int(ARC_BOTTOM) + 2, ART_ROWS)):
    run = [c for c in range(WIDTH) if grid[r][c] == "#" and colour[r][c] == SWOOSH]
    if run and max(run) > right_edge(r):
        put(r, max(run) + 1, ".", EDGE, over=False)

ART = []
for r in range(ART_ROWS):
    last = max((c for c in range(WIDTH) if grid[r][c] != " "), default=-1)
    line, current = [], None
    for c in range(last + 1):
        col = colour[r][c]
        if col is not None and col != current:
            line.append("$" + col)
            current = col
        line.append(grid[r][c])
    ART.append("".join(line))

ART.append("$3     A R C A L I U M   O S")


if __name__ == "__main__":
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ART) + "\n")
    plain = "\n".join(
        line.replace("$1", "").replace("$3", "").replace("$5", "") for line in ART
    )
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(plain)
