"""Draw assets/malloy-skills-tokens.svg from the published Malloy study table.

    python3 tools/malloy_chart.py

Numbers are transcribed from the report in rctruta/malloy-publisher-agent-study,
which derives them from the per-turn traces. Change them here only by changing
them there first.
"""
import pathlib

# goal -> model -> (baseline tokens, skills-injected tokens)
DATA = [
    ("count", [("Haiku 4.5", 123191, 31658), ("Sonnet 5", 5489, 33597), ("GPT-4o-mini", 72841, 13698)]),
    ("breakdown", [("Haiku 4.5", 78725, 48030), ("Sonnet 5", 12864, 49580), ("GPT-4o-mini", 34708, 38574)]),
    ("model", [("Haiku 4.5", 11916, 26087), ("Sonnet 5", 13948, 33348), ("GPT-4o-mini", 6654, 19211)]),
]

W, H = 760, 380
L, R, T, B = 58, 14, 34, 74          # margins
PLOT_H = H - T - B
MAX = 130_000
BASE, SKILL = "#9aa0a6", "#34C759"

def y(v):
    return T + PLOT_H - (v / MAX) * PLOT_H

groups = [(g, m, b, s) for g, rows in DATA for m, b, s in rows]
slot = (W - L - R) / len(groups)
bar = slot * 0.3

out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="system-ui, -apple-system, Helvetica, Arial, sans-serif" font-size="11">']

# y axis
for v in range(0, MAX + 1, 25_000):
    out.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{W-R}" y2="{y(v):.1f}" stroke="#e6e6e6"/>')
    out.append(f'<text x="{L-8}" y="{y(v)+4:.1f}" text-anchor="end" fill="#666">{v//1000}K</text>')
out.append(f'<text x="14" y="{T-14}" fill="#666">tokens per run</text>')

for i, (goal, model, b, s) in enumerate(groups):
    cx = L + slot * (i + 0.5)
    out.append(f'<rect x="{cx-bar:.1f}" y="{y(b):.1f}" width="{bar:.1f}" '
               f'height="{T+PLOT_H-y(b):.1f}" fill="{BASE}"/>')
    out.append(f'<rect x="{cx:.1f}" y="{y(s):.1f}" width="{bar:.1f}" '
               f'height="{T+PLOT_H-y(s):.1f}" fill="{SKILL}"/>')
    out.append(f'<text x="{cx:.1f}" y="{T+PLOT_H+15:.1f}" text-anchor="middle" '
               f'fill="#444" font-size="10">{model}</text>')

# goal labels under each block of three
for gi, (goal, rows) in enumerate(DATA):
    cx = L + slot * (gi * 3 + 1.5)
    out.append(f'<text x="{cx:.1f}" y="{T+PLOT_H+34:.1f}" text-anchor="middle" '
               f'fill="#111" font-weight="600">{goal}</text>')
    if gi:
        x = L + slot * gi * 3
        out.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T+PLOT_H+22}" stroke="#ddd"/>')

ly = H - 20
out.append(f'<rect x="{L}" y="{ly-9}" width="11" height="11" fill="{BASE}"/>'
           f'<text x="{L+17}" y="{ly}" fill="#444">baseline</text>')
out.append(f'<rect x="{L+88}" y="{ly-9}" width="11" height="11" fill="{SKILL}"/>'
           f'<text x="{L+105}" y="{ly}" fill="#444">skills injected</text>')
out.append('</svg>')

p = pathlib.Path("assets/malloy-skills-tokens.svg")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out))
print("wrote", p, f"({len(groups)} runs x 2 cells)")
