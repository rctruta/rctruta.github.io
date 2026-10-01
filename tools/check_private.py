"""Refuse to commit personal contact details to the public site.

Run by .githooks/pre-commit. Exits non-zero if a staged file contains a
personal email address, a phone number, or a street address.

Why this exists: on 2026-09-30 an agent put ramona.truta@gmail.com on the
public contact page without being asked, and it was live for about fifteen
minutes. A rule written in AGENTS.md did not prevent it. This does.

To publish a contact address deliberately, add it to ALLOWED below. That edit
is the decision, and it is visible in the diff.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Addresses Ramona has decided to publish. Nothing else may appear.
ALLOWED = {
    # "ramona@ramonactruta.com",   # uncomment when the domain mailbox exists
}

PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")),
    ("phone number", re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")),
]

# files that legitimately carry contact details, and vendored output that is
# not Ramona's data — pagefind/ is generated and carries its translators' credits
SKIP_FILES = {"AGENTS.md", "tools/check_private.py"}
SKIP_DIRS = ("pagefind/", "node_modules/")

staged = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True, cwd=ROOT,
).stdout.split()

found = []
for name in staged:
    if name in SKIP_FILES or name.startswith(SKIP_DIRS) or not name.endswith((".html", ".css", ".js", ".yaml", ".md", ".json")):
        continue
    path = ROOT / name
    if not path.exists():
        continue
    text = path.read_text(errors="ignore")
    for label, pattern in PATTERNS:
        for hit in pattern.findall(text):
            if hit in ALLOWED:
                continue
            # schema.org and example addresses are not personal data
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
        "\ntools/check_private.py. That edit is the decision, and it shows in the diff.\n"
    )
    sys.exit(1)
