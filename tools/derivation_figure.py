"""Draw assets/derivation-chain.svg — why one copy anywhere breaks the chain.

    python3 tools/derivation_figure.py

Two panels of the same three boxes. In the first every step is derived, so the
claim is checkable against the source without anyone checking the middle. In
the second the middle step is a copy, and the property is gone — silently,
which is the whole point: nothing in the second panel fails.

This figure has no numbers in it, deliberately. It is the one structural claim
the article rests on, and a structural claim should not need a measurement to
be legible.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "derivation-chain.svg"

W = 760
BOX_W, BOX_H = 176, 54
GAP = 58
PANEL_H = 150
H = PANEL_H * 2 + 18

INK, MUTE = "#1f2937", "#6b7280"
OK, BAD = "#0F6E56", "#C2410C"
FILL_OK, FILL_BAD = "#E1F5EE", "#FAECE7"

LABELS = [("Source", "the run, the repository"),
          ("Data", "yaml, facts registry"),
          ("Claim", "page, résumé, post")]

X0 = (W - (BOX_W * 3 + GAP * 2)) / 2
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'width="{W}" height="{H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
    f'<rect width="{W}" height="{H}" fill="#fff"/>',
]


def panel(top, broken):
    # The data is not the defect. Source and Data are both fine in the broken
    # panel; the Claim is the box holding a copy, so the Claim is what goes
    # red. Marking Data instead says the opposite of the article's argument.
    stroke = [OK, OK, BAD if broken else OK]
    fill = [FILL_OK, FILL_OK, FILL_BAD if broken else FILL_OK]

    title = ("One copy, and nothing announces it"
             if broken else "Every step derived")
    svg.append(f'<text x="{X0}" y="{top + 18}" font-size="13" font-weight="600" '
               f'fill="{BAD if broken else OK}">{title}</text>')

    by = top + 34
    for i, (name, sub) in enumerate(LABELS):
        x = X0 + i * (BOX_W + GAP)
        svg.append(f'<rect x="{x}" y="{by}" width="{BOX_W}" height="{BOX_H}" rx="6" '
                   f'fill="{fill[i]}" stroke="{stroke[i]}" stroke-width="0.6"/>')
        svg.append(f'<text x="{x + BOX_W / 2}" y="{by + 22}" font-size="13" '
                   f'font-weight="600" text-anchor="middle" fill="{INK}">{name}</text>')
        svg.append(f'<text x="{x + BOX_W / 2}" y="{by + 39}" font-size="11" '
                   f'text-anchor="middle" fill="{MUTE}">{sub}</text>')

        if i < 2:
            ax, mid = x + BOX_W, by + BOX_H / 2
            copy_edge = broken and i == 1
            col = BAD if copy_edge else OK
            dash = ' stroke-dasharray="5 4"' if copy_edge else ""
            svg.append(f'<path d="M{ax + 7} {mid} L{ax + GAP - 9} {mid}" '
                       f'stroke="{col}" stroke-width="1.4" fill="none"{dash}/>')
            svg.append(f'<path d="M{ax + GAP - 15} {mid - 4.5} L{ax + GAP - 9} {mid} '
                       f'L{ax + GAP - 15} {mid + 4.5}" stroke="{col}" '
                       f'stroke-width="1.4" fill="none"/>')
            svg.append(f'<text x="{ax + GAP / 2 - 1}" y="{mid - 9}" font-size="10.5" '
                       f'text-anchor="middle" font-family="{MONO}" fill="{col}">'
                       f'{"copies" if copy_edge else "derives"}</text>')

    ly = by + BOX_H + 26
    if broken:
        svg.append(f'<text x="{X0}" y="{ly}" font-size="11.5" fill="{BAD}">'
                   f'The claim no longer traces to the source. Edit the data and the '
                   f'copy keeps its old value &#8212; no error, no warning.</text>')
    else:
        svg.append(f'<path d="M{X0 + BOX_W / 2} {by + BOX_H + 8} '
                   f'L{X0 + BOX_W / 2} {ly - 4} '
                   f'L{X0 + BOX_W * 2.5 + GAP * 2} {ly - 4} '
                   f'L{X0 + BOX_W * 2.5 + GAP * 2} {by + BOX_H + 8}" '
                   f'stroke="{OK}" stroke-width="1" fill="none"/>')
        svg.append(f'<text x="{W / 2}" y="{ly + 15}" font-size="11.5" '
                   f'text-anchor="middle" fill="{OK}">'
                   f'Derivation is transitive: the claim is checkable against the '
                   f'source, without checking the middle.</text>')


panel(0, False)
svg.append(f'<path d="M{X0} {PANEL_H + 4} L{W - X0} {PANEL_H + 4}" '
           f'stroke="#e6e6e6" stroke-width="1"/>')
panel(PANEL_H + 14, True)
svg.append("</svg>")

OUT.write_text("\n".join(svg), encoding="utf-8")
print(f"{OUT.relative_to(ROOT)}: two panels, intact and broken")
