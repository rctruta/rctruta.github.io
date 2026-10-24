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

## Generated Files & Build Order

Never edit generated HTML files by hand. Run `./build` to recompile everything:

```bash
./build
```

Build steps executed by `./build`:
1. `tools/test_tools.py` — Runs standard unit test suite over YAML schemas and HTML anchor contracts.
2. `tools/build_work.py` — Generates `work.html` from `data/work.yaml`.
3. `tools/build_teaching.py` — Generates `teaching.html` from `data/teaching.yaml`.
4. `tools/build_speaking.mjs` — Generates `speaking.html` from `data/appearances.yaml`.
5. `tools/build_writing.py` — Generates `writing.html` from `data/writing.yaml`.
6. `tools/build_tags.py` — Generates `tags.html` and injects tag rows from `data/TAGS.yaml`.
7. `tools/build_nav.py` — Generates navigation bar from `config.yaml`.
8. `tools/malloy_chart.py` — Generates SVG charts.
9. `tools/build_search.py` — Builds Pagefind search index over generated HTML files.
10. `tools/sync_template.py` — Propagates build scripts and data schemas to `static-site-template/`.
