"""Generate the master résumé from the site's own data.

    python3 tools/build_resume.py

Writes ~/claude-docs-allowed/Resume/SUBMIT/RESUME_MASTER.txt. Not part of the
website: it is not in this repository and it is not published.

Why this exists. The site, the GitHub profile, the bio and the interview prep
sheet were all generated from data/. The résumés were not — they were
hand-written .txt files in another directory, so a number corrected in
work.yaml never reached the artifact that actually goes to employers. On
2026-10-15 a figure on three résumés turned out to come from a 2013 proof of
concept, and fixing it meant editing three files by hand. This closes that.

What is generated and what is not:

  generated   every role, every date, every project line, education, honours
  hers        the tagline in employment.yaml, and the five role variants

The five role variants (DEVREL, ENGINEER, ENABLEMENT, DATASCIENCE, CURRENT)
stay hand-curated. Choosing what to emphasise for a role is editorial
judgement, not data, and generating it would produce five identical files.
This is the comprehensive one they are cut from.

Output format is what qr/build_variant.py already parses: line 1 name, line 2
tagline, line 3 contact, ALL-CAPS section headings, "- " bullets, and job
headings carrying "| <dates>". So the existing HTML and PDF pipeline applies
unchanged.

A role with an unfilled "[YOURS: ...]" date generates fine here and then stops
qr/build_variant.py, which refuses any variant holding a placeholder. The gap
is visible in the file rather than guessed at.
"""
import pathlib
import sys

from config_loader import load_config
from model import (load_taxonomy, load_work_sections, load_employment,
                   load_education, count_testimonials)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = (pathlib.Path.home() / "claude-docs-allowed" / "Resume" / "SUBMIT"
       / "RESUME_MASTER.txt")

CONFIG = load_config()
AUTHOR = CONFIG["site"]["author"]["name"]


PRIVATE = (pathlib.Path.home() / "claude-docs-allowed" / "Resume"
           / "contact_private.yaml")


def contact_line():
    """Public links from config.yaml, private details from outside the repo.

    This repository is public and tools/check_private.py refuses to commit an
    email address or a phone number to it, so config.yaml cannot hold them.
    They live in contact_private.yaml beside the résumés. Neither half is typed
    here.
    """
    if not PRIVATE.exists():
        raise ValueError(
            f"{PRIVATE} is missing. It holds the location, phone and email "
            "that config.yaml must not carry, because this repository is "
            "public. Create it rather than hardcoding them.")

    priv = {}
    for line in PRIVATE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        priv[k.strip()] = v.strip().strip('"\'')

    author = CONFIG["site"]["author"]
    parts = [priv.get("location"), priv.get("phone"), priv.get("email"),
             author.get("linkedin"), author.get("github"),
             CONFIG["site"].get("url"), author.get("substack"),
             f"ORCID {author['orcid_id']}" if author.get("orcid_id") else None]
    parts = [str(p).replace("https://", "") for p in parts if p]

    for required in ("location", "phone", "email"):
        if not priv.get(required):
            raise ValueError(f"{PRIVATE.name}: '{required}' is missing.")

    return " | ".join(parts)


def bullet(item) -> str:
    """A résumé bullet needs its own subject.

    ProjectItem.one_line is written for the GitHub profile table, where the
    repository name sits in the column beside it. Lifted into a bullet it
    arrives without a subject — "A suite of 23 correctness probes..." of what?
    So the title's own short form leads, taken from before the em dash, and the
    prose follows. Markdown emphasis is dropped: this is plain text.
    """
    label = item.title.split("—")[0].strip().rstrip(".,")
    text = item.one_line.replace("**", "").replace("`", "")
    if label and len(label) < 46 and not text.lower().startswith(label.lower()):
        return f"{label}: {text}"
    return text


def main():
    vocab = load_taxonomy()
    sections = load_work_sections(vocab)
    items = {i.id: i for s in sections for i in s.items}
    emp = load_employment(set(items))
    edu = load_education()

    out = [AUTHOR, emp.tagline, contact_line(), "", ""]

    out.append("EXPERIENCE")
    out.append("")
    for r in emp.roles:
        head = f"{r.role}, {r.org} | {r.dates}" if r.org else f"{r.role} | {r.dates}"
        out.append(head)
        out.append("")
        if r.note:
            out.append(f"- {r.note}")
        for wid in r.work_ids:
            out.append(f"- {bullet(items[wid])}")
        if not r.note and not r.work_ids:
            raise ValueError(
                f"employment.yaml: role '{r.role}' has neither a note nor "
                f"any work_ids, so it would print as a bare heading.")
        out.append("")

    out += ["", "EDUCATION & CERTIFICATIONS", ""]
    for d in edu.degrees:
        line = f"{d.degree} - {d.institution}"
        if d.thesis:
            line += f". Thesis: {d.thesis}"
        if d.advisor:
            line += f", under {d.advisor}"
        out.append(line)
    out.append("")
    for c in edu.certificates:
        out.append(f"- {c}")

    if edu.honours:
        out += ["", "", "HONOURS", ""]
        for h in edu.honours:
            out.append(f"- {h}")

    text = "\n".join(out).rstrip() + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")

    n_items = sum(len(r.work_ids) for r in emp.roles)
    pending = [r.role for r in emp.roles if r.needs_input]
    print(f"RESUME_MASTER.txt: {len(emp.roles)} roles, {n_items} project lines, "
          f"{len(edu.degrees)} degrees, {len(edu.certificates)} certificates, "
          f"{count_testimonials()} testimonials on file")
    if "[YOURS" in emp.tagline:
        print("  tagline is still a placeholder (employment.yaml)")
    for p in pending:
        print(f"  dates needed: {p}")
    if pending or "[YOURS" in emp.tagline:
        print("  -> qr/build_variant.py will refuse the PDF until these are filled.")


main()
