"""Refuse to commit personal contact details to the public site.

Run by .githooks/pre-commit. Exits non-zero if a staged file contains a
personal email address, a phone number, or a street address.

Why this exists: on 2026-09-30 an agent put a personal Gmail address on the
public contact page without being asked, and it was live for about fifteen
minutes. A rule written in AGENTS.md did not prevent it. This does.

This file is in SKIP_FILES, so the gate does not scan itself — which is why
the address it was written about sat here, in a public repository, for two
weeks. An address belongs in ALLOWED or nowhere.

To publish a contact address deliberately, add it to ALLOWED below. That edit
is the decision, and it is visible in the diff.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Addresses chosen for publication. Nothing else may appear.
ALLOWED = {
    # "you@yourdomain.com",   # uncomment when the mailbox exists
}

PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")),
    ("phone number", re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")),
]

# files that legitimately carry contact details, and vendored output that is
# generated output — pagefind/ carries its translators' credits
SKIP_FILES = {"AGENTS.md", "tools/check_private.py"}
SKIP_DIRS = ("pagefind/", "node_modules/")

staged = subprocess.run(
    # ACMR, not ACM. A file that enters this repository as a RENAME has status
    # R and was never scanned — found 2026-10-15 while proving the marker check
    # below, when `git mv` of a private file into data/ passed clean. Anything
    # arriving by rename is as new to this repository as an addition.
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
    capture_output=True, text=True, cwd=ROOT,
).stdout.split()

# Private by subject, not by pattern.
#
# On 2026-10-15 data/employment.yaml was created in this public repository and
# committed. It held no email and no phone, so the patterns above passed it
# clean — but it carried a contract role deliberately kept off the portfolio
# and notes on which employment dates were still unconfirmed. The gate could
# not see the problem because the problem was the subject of the file.
#
# So a file may declare itself private in its first lines, and this refuses to
# commit it. A declaration a human writes and a gate reads, rather than a
# header nobody checks.
PRIVATE_MARKER = re.compile(
    r"\bPRIVATE:\s*do not commit\b|\bnever enter the public repository\b"
    r"|\bmust never enter the public repo", re.I)

declared = []
for name in staged:
    path = ROOT / name
    if not path.exists() or not path.is_file():
        continue
    if name in SKIP_FILES:
        continue
    try:
        head = path.read_text(errors="ignore")[:800]
    except Exception:
        continue
    if PRIVATE_MARKER.search(head):
        declared.append(name)

if declared:
    print("These staged files declare themselves private:\n", file=sys.stderr)
    for n in declared:
        print(f"  {n}", file=sys.stderr)
    print("\nThis repository is public. Move the file outside it and read it "
          "by absolute path, the way tools/model.py reads employment.yaml.",
          file=sys.stderr)
    sys.exit(1)

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
