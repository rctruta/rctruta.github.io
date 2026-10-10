"""Draw assets/lakehouse-semantics-probes.svg from the published probe results.

    python3 tools/lakehouse_chart.py

Values are transcribed from the results table in rctruta/lakehouse-semantics,
which derives them from running the probes. Change them here only by changing
them there first.

The highlight is derived, not chosen: a cell is marked when it disagrees with
the other two engines. Nothing encodes "stricter", because the study's own
finding is that strictness reverses by probe — only four of the seven are a
strict/permissive question at all, and the rest are integer division, rounding
and NULL ordering.
"""
import pathlib

# probe -> (duckdb, postgresql, databricks)
ROWS = [
    ("SELECT 1/0",                    ("inf", "raises", "raises")),
    ("SELECT 7/2",                    ("3.5", "3", "3.5")),
    ("SELECT '1' + 1",                ("raises", "2", "2")),
    ("INSERT 3.7 into INTEGER",       ("4", "4", "3")),
    ("ORDER BY x ASC, NULLs",         ("last", "last", "first")),
    ("duplicate PRIMARY KEY",         ("rejected", "rejected", "accepted")),
    ("INSERT 'abcdef' into CHAR(3)",  ("kept in full", "rejected", "rejected")),
]
ENGINES = ["DuckDB", "PostgreSQL", "Databricks"]

W, H = 760, 300
LABEL_W, TOP = 236, 52
ROW_H = (H - TOP - 26) / len(ROWS)
COL_W = (W - LABEL_W - 14) / len(ENGINES)
ODD, SAME, LINE = "#C2410C", "#444", "#e6e6e6"


def odd_one_out(values):
    """The index that disagrees with both others, or None when all three differ."""
    for i, v in enumerate(values):
        others = [values[j] for j in range(3) if j != i]
        if others[0] == others[1] and v != others[0]:
            return i
    return None


out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="system-ui, -apple-system, Helvetica, Arial, sans-serif" font-size="12.5">']

for c, name in enumerate(ENGINES):
    x = LABEL_W + COL_W * (c + 0.5)
    out.append(f'<text x="{x:.1f}" y="{TOP-18:.1f}" text-anchor="middle" '
               f'font-weight="600" fill="#111">{name}</text>')
out.append(f'<line x1="14" y1="{TOP-8}" x2="{W-14}" y2="{TOP-8}" stroke="#bbb"/>')

for r, (probe, values) in enumerate(ROWS):
    y = TOP + ROW_H * (r + 0.5)
    out.append(f'<text x="14" y="{y+4:.1f}" fill="#111" '
               f'font-family="ui-monospace, SFMono-Regular, Menlo, monospace" '
               f'font-size="11.5">{probe}</text>')
    odd = odd_one_out(values)
    for c, v in enumerate(values):
        x = LABEL_W + COL_W * (c + 0.5)
        if c == odd:
            out.append(f'<rect x="{x-COL_W/2+6:.1f}" y="{y-ROW_H/2+3:.1f}" '
                       f'width="{COL_W-12:.1f}" height="{ROW_H-6:.1f}" rx="4" fill="#FDF0E8"/>')
        fill, weight = (ODD, "600") if c == odd else (SAME, "400")
        out.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" '
                   f'fill="{fill}" font-weight="{weight}">{v}</text>')
    if r:
        out.append(f'<line x1="14" y1="{TOP+ROW_H*r:.1f}" x2="{W-14}" '
                   f'y2="{TOP+ROW_H*r:.1f}" stroke="{LINE}"/>')

ly = H - 8
out.append(f'<rect x="14" y="{ly-9}" width="11" height="11" rx="2" fill="#FDF0E8"/>'
           f'<text x="31" y="{ly}" fill="#666" font-size="11.5">'
           f'the engine that disagrees with the other two</text>')
out.append('</svg>')

p = pathlib.Path("assets/lakehouse-semantics-probes.svg")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out))
counts = {}
for _, v in ROWS:
    i = odd_one_out(v)
    if i is not None:
        counts[ENGINES[i]] = counts.get(ENGINES[i], 0) + 1
print("wrote", p, "—", ", ".join(f"{k} odd on {n}" for k, n in sorted(counts.items())))
