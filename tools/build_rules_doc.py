"""Write the kinds table into the application-rules document from the vocabulary."""
import pathlib
from config_loader import load_config
from model import load_taxonomy, load_appearances

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOCAB = load_config()["data"]["controlled_vocabulary"]
DOC = ROOT / "data" / "APPLICATION-RULES.md"

START, END = "<!-- kinds:start -->", "<!-- kinds:end -->"
ORG_START, ORG_END = "<!-- orgs:start -->", "<!-- orgs:end -->"


def table() -> str:
    kinds = load_taxonomy().kinds
    rows = sorted(kinds.items(), key=lambda kv: (kv[1].order, kv[0]))
    out = [f"<!-- generated from {VOCAB} by tools/build_rules_doc.py; edit the vocabulary -->",
           "", "| kind | Category | Description |", "| --- | --- | --- |"]
    out += [f"| `{k}` | `{m.category}` | {m.note} |" for k, m in rows]
    return "\n".join(out)


def orgs() -> str:
    """The authority list of org names, from the appearances that use them."""
    names = sorted({a.org for a in load_appearances(load_taxonomy()) if a.org},
                   key=str.lower)
    out = ["<!-- generated from data/appearances.yaml by tools/build_rules_doc.py;"
           " add an appearance, not a name -->", ""]
    out += [f"- `{n}`" for n in names]
    return "\n".join(out)


def _splice(text, start, end, body, label):
    if start not in text or end not in text:
        raise ValueError(f"{DOC.name} has no {start} / {end} markers for {label}")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{start}\n{body}\n{end}{tail}"


def main():
    text = DOC.read_text(encoding="utf-8")
    text = _splice(text, START, END, table(), "the kinds table")
    text = _splice(text, ORG_START, ORG_END, orgs(), "the org list")
    DOC.write_text(text, encoding="utf-8")
    n = len({a.org for a in load_appearances(load_taxonomy()) if a.org})
    print(f"{DOC.name}: kinds table from {VOCAB}, {n} org names from appearances.yaml")


if __name__ == "__main__":
    main()
