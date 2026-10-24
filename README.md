# Ramona C. Truta — Personal Website & Portfolio Architecture

Contract-driven, data-modeled static website. All content pages (`work.html`, `teaching.html`, `writing.html`, `speaking.html`, `tags.html`) are compiled directly from structured YAML data files in `data/`.

## Architecture & Data Flow

```
                                  +---------------------------------+
                                  |    config.yaml  (Meta Layer)    |
                                  |  Site Metadata, Author, Nav     |
                                  +---------------------------------+
                                                   |
                                                   v
                                  +---------------------------------+
                                  |   data/TAGS.yaml  (Taxonomy)    |
                                  |  Facets, Vocab, Project Tags    |
                                  +---------------------------------+
                                                   |
         +-----------------------+-----------------+-----------------------+-----------------------+
         |                       |                                         |                       |
         v                       v                                         v                       v
+------------------+    +------------------+                      +------------------+    +------------------+
|  data/work.yaml  |    |data/teaching.yaml|                      |data/writing.yaml |    |appearances.yaml  |
|  (Work Projects) |    | (Teaching Data)  |                      |  (Articles/Blog) |    |    (Speaking)    |
+------------------+    +------------------+                      +------------------+    +------------------+
         |                       |                                         |                       |
         v                       v                                         v                       v
     work.html             teaching.html                              writing.html           speaking.html
```

## Quickstart & Local Development

### Prerequisites
- Python 3.10+ (with `pyyaml`)
- `pre-commit` (`pip install pre-commit`)
- Node.js (for `pagefind` search indexing)

```bash
# Clone the repository
git clone https://github.com/rctruta/rctruta.github.io.git
cd rctruta.github.io

# Build all static pages from data/
./build

# Run unit tests directly
python3 -m unittest discover -s tests -t .
```

## Generated Files & Build Order

Never edit generated HTML files by hand. Run `./build` to recompile everything:

```bash
./build
```

Build steps executed by `./build`:
1. `tools/build_work.py` — Generates `work.html` from `data/work.yaml`.
2. `tools/build_teaching.py` — Generates `teaching.html` from `data/teaching.yaml`.
3. `tools/build_speaking.py` — Generates `speaking.html` from `data/appearances.yaml`.
4. `tools/build_writing.py` — Generates `writing.html` from `data/writing.yaml`.
5. `tools/build_contact.py` — Generates `contact.html` from `data/contact.yaml`.
6. `tools/build_index.py` — Generates home page from `data/home.yaml`.
7. `tools/build_rules_doc.py` — Generates rules documentation from taxonomy.
8. `tools/build_tags.py` — Generates `tags.html` from `data/TAGS.yaml`.
9. `tools/build_nav.py` — Generates navigation bar from `config.yaml`.
10. `tools/build_search.py` — Builds Pagefind search index over generated HTML files.
11. Pre-commit hooks verification & full unit test suite (`tests/`).
