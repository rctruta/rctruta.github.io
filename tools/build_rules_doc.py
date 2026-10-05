"""Write the kinds table into the application-rules document from the vocabulary.

    python3 tools/build_rules_doc.py

The table listing every content kind and its category was typed into the
document and also declared in the controlled vocabulary. Two copies, agreeing
by luck, in the one document that says how the vocabulary is applied.

Only the table is generated. The rest of the document is prose rules for a
person, and prose is not data.
"""
import pathlib
from config_loader import load_config
from model import load_taxonomy

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOCAB = load_config()["data"]["controlled_vocabulary"]
DOC = ROOT / "data" / "APPLICATION-RULES.md"

START, END = "<!-- kinds:start -->", "<!-- kinds:end -->"


def table() -> str:
    kinds = load_taxonomy().kinds
    rows = sorted(kinds.items(), key=lambda kv: (kv[1].order, kv[0]))
    out = [f"<!-- generated from {VOCAB} by tools/build_rules_doc.py; edit the vocabulary -->",
           "", "| kind | Category | Description |", "| --- | --- | --- |"]
    out += [f"| `{k}` | `{m.category}` | {m.note} |" for k, m in rows]
    return "\n".join(out)


def main():
    text = DOC.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise ValueError(f"{DOC.name} has no {START} / {END} markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    DOC.write_text(f"{head}{START}\n{table()}\n{END}{tail}", encoding="utf-8")
    print(f"{DOC.name}: kinds table written from {VOCAB}")


if __name__ == "__main__":
    main()
