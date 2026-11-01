"""Prevent accidental commit of personal contact details to the public repository."""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ALLOWED = {
}

PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")),
    ("phone number", re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")),
]

SKIP_FILES = {"AGENTS.md", "tools/check_private.py"}
SKIP_DIRS = ("pagefind/", "node_modules/")

all_files = '--all-files' in sys.argv
command = ['git', 'ls-files', '-z'] if all_files else [
    'git', 'diff', '--cached', '--name-only', '-z', '--diff-filter=ACMR']
staged = subprocess.check_output(command, cwd=ROOT).decode().split('\0')
staged = [name for name in staged if name]


def contents(name):
    if all_files:
        return (ROOT / name).read_text(errors='ignore')
    return subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT).decode(errors='ignore')

PRIVATE_MARKER = re.compile(
    r"\bPRIVATE:\s*do not commit\b|\bnever enter the public repository\b", re.I)

declared = []
for name in staged:
    path = ROOT / name
    if all_files and (not path.exists() or not path.is_file()):
        continue
    if name in SKIP_FILES:
        continue
    try:
        head = contents(name)[:800]
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f'Cannot inspect public content {name}: {exc}')
    if PRIVATE_MARKER.search(head):
        declared.append(name)

if declared:
    print("These staged files declare themselves private:\n", file=sys.stderr)
    for n in declared:
        print(f"  {n}", file=sys.stderr)
    sys.exit(1)

found = []
for name in staged:
    if name in SKIP_FILES or name.startswith(SKIP_DIRS) or not name.endswith((".html", ".css", ".js", ".yaml", ".md", ".json")):
        continue
    path = ROOT / name
    if all_files and not path.exists():
        continue
    text = contents(name)
    for label, pattern in PATTERNS:
        for hit in pattern.findall(text):
            if hit in ALLOWED:
                continue
            if hit.endswith(("@example.com", "@schema.org")):
                continue
            line = next(
                (i for i, l in enumerate(text.splitlines(), 1) if hit in l), 0
            )
            found.append((name, line, label, hit))

if found:
    print("\nBLOCKED — personal contact details in files staged for a public site:\n")
    for name, line, label, hit in found:
        print(f"  {name}:{line}  {label}  {hit}")
    print(
        "\nIf this is deliberate, add the address to ALLOWED in"
        "\ntools/check_private.py.\n"
    )
    sys.exit(1)
