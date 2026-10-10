"""Draw assets/rag-calibration.svg from the published calibration record.

    python3 tools/rag_chart.py

Values are transcribed from eval/calibration.json in rctruta/podcast-rag,
written by eval/combine.py. Change them here only by changing them there first.

Two panels, because the study answers two questions: what recalibrating the
refusal threshold did, and whether a heavier signal would have done better.
"""
import pathlib

# from calibration.json
OLD_T, NEW_T = 0.25, 0.541
OLD_P, NEW_P = 0.564, 0.87
RECALL = 0.909
CANDIDATES = [                      # F-beta, beta = 0.5
    ("cosine, bi-encoder", 0.877, True),
    ("cross-encoder", 0.756, False),
    ("cosine + cross-encoder", 0.764, False),
]
CROSS_VALIDATED = 0.83
QUESTIONS, CHUNKS = 42, 7377

W, H = 760, 300
CHOSEN, OTHER, GHOST = "#34C759", "#9aa0a6", "#e6e6e6"

out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="system-ui, -apple-system, Helvetica, Arial, sans-serif" font-size="12">']

# --- left panel: precision before and after the threshold moved -------------
LX, LW, TOP, PLOT_H = 58, 250, 54, 170
out.append(f'<text x="14" y="26" font-weight="600" fill="#111">Precision at the refusal threshold</text>')
for v in (0, 0.25, 0.5, 0.75, 1.0):
    y = TOP + PLOT_H - v * PLOT_H
    out.append(f'<line x1="{LX}" y1="{y:.1f}" x2="{LX+LW}" y2="{y:.1f}" stroke="{GHOST}"/>')
    out.append(f'<text x="{LX-8}" y="{y+4:.1f}" text-anchor="end" fill="#666" font-size="11">{v:.2f}</text>')

for i, (label, thresh, prec, colour) in enumerate([
        ("before", OLD_T, OLD_P, OTHER), ("after", NEW_T, NEW_P, CHOSEN)]):
    cx = LX + LW * (0.3 + i * 0.4)
    bar = 58
    y = TOP + PLOT_H - prec * PLOT_H
    out.append(f'<rect x="{cx-bar/2:.1f}" y="{y:.1f}" width="{bar}" '
               f'height="{TOP+PLOT_H-y:.1f}" fill="{colour}"/>')
    out.append(f'<text x="{cx:.1f}" y="{y-7:.1f}" text-anchor="middle" '
               f'font-weight="600" fill="#111">{prec:.3f}</text>')
    out.append(f'<text x="{cx:.1f}" y="{TOP+PLOT_H+16:.1f}" text-anchor="middle" fill="#444">{label}</text>')
    out.append(f'<text x="{cx:.1f}" y="{TOP+PLOT_H+31:.1f}" text-anchor="middle" '
               f'fill="#666" font-size="11">threshold {thresh}</text>')
out.append(f'<text x="{LX}" y="{TOP+PLOT_H+54:.1f}" fill="#666" font-size="11">'
           f'recall after: {RECALL} &#183; {QUESTIONS} questions over {CHUNKS:,} chunks</text>')

# --- right panel: the signals that were tried and rejected ------------------
RX = 430
out.append(f'<text x="{RX}" y="26" font-weight="600" fill="#111">'
           f'F&#946; of each candidate signal (&#946; = 0.5)</text>')
bar_h, gap = 26, 16
for i, (name, score, chosen) in enumerate(CANDIDATES):
    y = TOP + i * (bar_h + gap)
    width = (W - RX - 70) * score
    out.append(f'<rect x="{RX}" y="{y}" width="{width:.1f}" height="{bar_h}" '
               f'fill="{CHOSEN if chosen else OTHER}"/>')
    out.append(f'<text x="{RX + width + 8:.1f}" y="{y + bar_h*0.72:.1f}" '
               f'fill="#111" font-weight="{"600" if chosen else "400"}">{score:.3f}</text>')
    out.append(f'<text x="{RX}" y="{y - 5:.1f}" fill="#444" font-size="11">{name}</text>')
out.append(f'<text x="{RX}" y="{TOP + 3*(bar_h+gap) + 10:.1f}" fill="#666" font-size="11">'
           f'chosen signal cross-validated at {CROSS_VALIDATED}</text>')
out.append('</svg>')

p = pathlib.Path("assets/rag-calibration.svg")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out))
print(f"wrote {p} — precision {OLD_P} -> {NEW_P}, {len(CANDIDATES)} candidate signals")
