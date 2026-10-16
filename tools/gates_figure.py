"""Draw assets/gate-registry.svg — each gate beside the incident that produced it.

    python3 tools/gates_figure.py

Nothing here is transcribed. The rows are parsed out of the registry table in
ai-agent-utils/GATES.md, and each date is read from the "observed YYYY-MM-DD"
line in the gate's own source. A figure in an article arguing that a claim
should name its source cannot be a figure with its numbers typed into it.

That also means the figure breaks loudly when the registry changes shape, which
is the behaviour you want: the alternative is a diagram that quietly describes
last month's system.
"""
import datetime
import html
import pathlib
import re
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
GATES = pathlib.Path.home() / "Projects" / "ai-agent-utils"
DOC = GATES / "GATES.md"
OUT = ROOT / "assets" / "gate-registry.svg"

if not DOC.exists():
    sys.exit(f"{DOC} not found — the registry is the source for this figure.")


def registry_section():
    """Only the registry table.

    Parsing every three-column row in the document picked up the header of the
    measurement table further down ("what | where it lives | committed?") and
    drew it as a gate. The section heading is the boundary, so use it.
    """
    text = DOC.read_text(encoding="utf-8")
    m = re.search(r"^##\s*The registry\s*$(.*?)^##\s", text, re.M | re.S)
    if not m:
        sys.exit(f"{DOC.name}: no '## The registry' section — the document changed shape.")
    return m.group(1)


def rows():
    """(gate, refuses, incident, date) from the GATES.md registry table."""
    text = registry_section()
    out = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`?([\w./]+)`?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        gate, refuses, incident = (g.strip() for g in m.groups())
        if gate in ("gate", "---") or refuses.startswith("---"):
            continue
        # prove_gates.sh belongs in the registry but not in this figure: its
        # left-hand cell is an aphorism ("an untested gate is theatre"), not an
        # incident, so it has nothing to sit opposite.
        if refuses.startswith("—"):
            continue
        out.append([gate, refuses, incident, date_for(gate)])
    if not out:
        sys.exit(f"parsed no rows from {DOC.name}; the table format changed.")
    return out


def date_for(gate):
    """The 'observed YYYY-MM-DD' line in the gate's own source, if it has one."""
    src = GATES / "templates" / "gates" / gate
    if not src.exists():
        return ""
    m = re.search(r"observed\s+(\d{4}-\d{2}-\d{2})", src.read_text(errors="ignore"))
    return m.group(1) if m else ""


DATA = rows()

W = 760
PAD, GAP = 16, 14
LEFT_W = 318
RIGHT_X = PAD + LEFT_W + 52
RIGHT_W = W - RIGHT_X - PAD
WRAP_L, WRAP_R = 46, 40
INK, MUTE = "#1f2937", "#6b7280"
INCIDENT, MECHANISM = "#C2410C", "#0F6E56"
FILL_I, FILL_M = "#FAECE7", "#E1F5EE"


def block(text, width):
    return textwrap.wrap(" ".join(text.split()), width)


heights = []
for gate, refuses, incident, _ in DATA:
    li = len(block(incident, WRAP_L))
    ri = len(block(refuses, WRAP_R)) + 1          # + the gate name line
    heights.append(max(li, ri) * 15 + 20)

TOP = 66
H = TOP + sum(heights) + GAP * (len(DATA) - 1) + PAD

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'width="{W}" height="{H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
    f'<rect width="{W}" height="{H}" fill="#fff"/>',
    f'<text x="{PAD}" y="26" font-size="15" font-weight="600" fill="{INK}">'
    f'Every gate exists because something went wrong once</text>',
    f'<text x="{PAD}" y="46" font-size="12" fill="{MUTE}">'
    f'parsed from GATES.md, version {(GATES / "templates" / "gates" / "VERSION").read_text().strip()}'
    f' &#183; {datetime.date.today().isoformat()}</text>',
    f'<text x="{PAD}" y="62" font-size="11" font-weight="600" fill="{INCIDENT}">THE INCIDENT</text>',
    f'<text x="{RIGHT_X}" y="62" font-size="11" font-weight="600" fill="{MECHANISM}">WHAT NOW REFUSES IT</text>',
]

y = TOP
for (gate, refuses, incident, date), h in zip(DATA, heights):
    svg.append(f'<rect x="{PAD}" y="{y}" width="{LEFT_W}" height="{h}" rx="5" '
               f'fill="{FILL_I}" stroke="{INCIDENT}" stroke-width="0.5"/>')
    svg.append(f'<rect x="{RIGHT_X}" y="{y}" width="{RIGHT_W}" height="{h}" rx="5" '
               f'fill="{FILL_M}" stroke="{MECHANISM}" stroke-width="0.5"/>')
    mid = y + h / 2
    svg.append(f'<path d="M{PAD + LEFT_W + 8} {mid} L{RIGHT_X - 10} {mid}" '
               f'stroke="{MUTE}" stroke-width="1" fill="none"/>')
    svg.append(f'<path d="M{RIGHT_X - 16} {mid - 4} L{RIGHT_X - 10} {mid} '
               f'L{RIGHT_X - 16} {mid + 4}" stroke="{MUTE}" stroke-width="1" fill="none"/>')

    ty = y + 16
    for ln in block(incident, WRAP_L):
        svg.append(f'<text x="{PAD + 10}" y="{ty}" font-size="11.5" fill="{INK}">'
                   f'{html.escape(ln)}</text>')
        ty += 15

    ty = y + 16
    label = html.escape(gate) + (f"   &#183; {date}" if date else "")
    svg.append(f'<text x="{RIGHT_X + 10}" y="{ty}" font-size="11.5" font-weight="600" '
               f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
               f'fill="{MECHANISM}">{label}</text>')
    ty += 15
    for ln in block("refuses " + refuses, WRAP_R):
        svg.append(f'<text x="{RIGHT_X + 10}" y="{ty}" font-size="11.5" '
                   f'fill="{INK}">{html.escape(ln)}</text>')
        ty += 15
    y += h + GAP

svg.append("</svg>")
OUT.write_text("\n".join(svg), encoding="utf-8")
print(f"{OUT.relative_to(ROOT)}: {len(DATA)} gates, parsed from {DOC.name}")
