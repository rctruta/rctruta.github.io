"""Draw assets/harness-gating-cost.svg from the MotherDuck MCP study.

    python3 tools/harness_chart.py

Values are transcribed from reports/motherduck-study/report.md in
rctruta/harness-bench. Change them here only by changing them there first.

Three goals run twice against the same MCP surface — once bare, once with
mechanical gates in front of it. Every one of the twelve pairs graded PASS in
both arms, so the question is not whether gating works but what it costs, and
the answer turns out to depend on the model.
"""
import pathlib

# model -> (baseline tokens, gated tokens), summed over total_revenue,
# top_region and gold_revenue
DATA = [
    ("Claude Sonnet 5",   21563, 19937),
    ("Claude Haiku 4.5",  20445, 20917),
    ("o3-mini",            9901, 11368),
    ("GPT-4o-mini",        8484, 13258),
]
GOALS, ARMS = 3, 2

W, H = 760, 330
L, R, T, B = 64, 16, 44, 76
PLOT_H = H - T - B
MAX = 24_000
BASE, GATED = "#9aa0a6", "#34C759"


def y(v):
    return T + PLOT_H - (v / MAX) * PLOT_H


out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="system-ui, -apple-system, Helvetica, Arial, sans-serif" font-size="11.5">']

for v in range(0, MAX + 1, 4_000):
    out.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{W-R}" y2="{y(v):.1f}" stroke="#e6e6e6"/>')
    out.append(f'<text x="{L-8}" y="{y(v)+4:.1f}" text-anchor="end" fill="#666">{v//1000}K</text>')
out.append(f'<text x="14" y="{T-18}" fill="#666">tokens across three goals</text>')

slot = (W - L - R) / len(DATA)
bar = slot * 0.26
for i, (model, base, gated) in enumerate(DATA):
    cx = L + slot * (i + 0.5)
    out.append(f'<rect x="{cx-bar-2:.1f}" y="{y(base):.1f}" width="{bar:.1f}" '
               f'height="{T+PLOT_H-y(base):.1f}" fill="{BASE}"/>')
    out.append(f'<rect x="{cx+2:.1f}" y="{y(gated):.1f}" width="{bar:.1f}" '
               f'height="{T+PLOT_H-y(gated):.1f}" fill="{GATED}"/>')
    pct = (gated - base) / base * 100
    sign = "+" if pct >= 0 else "−"
    out.append(f'<text x="{cx:.1f}" y="{min(y(base), y(gated))-8:.1f}" text-anchor="middle" '
               f'font-weight="600" fill="{"#C2410C" if pct > 5 else "#2E7D32" if pct < -5 else "#666"}">'
               f'{sign}{abs(pct):.0f}%</text>')
    out.append(f'<text x="{cx:.1f}" y="{T+PLOT_H+18:.1f}" text-anchor="middle" fill="#111">{model}</text>')

ly = H - 26
out.append(f'<rect x="{L}" y="{ly-9}" width="11" height="11" fill="{BASE}"/>'
           f'<text x="{L+17}" y="{ly}" fill="#444">bare MCP surface</text>')
out.append(f'<rect x="{L+150}" y="{ly-9}" width="11" height="11" fill="{GATED}"/>'
           f'<text x="{L+167}" y="{ly}" fill="#444">with mechanical gates</text>')
out.append(f'<text x="{L}" y="{H-8}" fill="#666">'
           f'all {len(DATA)*GOALS} runs graded PASS in both arms</text>')
out.append('</svg>')

p = pathlib.Path("assets/harness-gating-cost.svg")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out))
deltas = ", ".join(f"{m} {(g-b)/b*100:+.0f}%" for m, b, g in DATA)
print(f"wrote {p} — {deltas}")
