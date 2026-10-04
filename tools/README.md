# tools

Nothing in here is run by hand. Use `./build` at the repository root.

| generator | reads | writes |
| --- | --- | --- |
| `build_work.py` | `data/work.yaml` | `work.html` |
| `build_teaching.py` | `data/teaching.yaml` | `teaching.html` |
| `build_speaking.mjs` | `data/appearances.yaml` | `speaking.html` |
| `build_writing.py` | `data/writing.yaml` | `writing.html` |
| `build_tags.py` | `data/TAGS.yaml`, data files | `tags.html`, tag rows |
| `build_nav.py` | `config.yaml` / `NAV` list | top nav on every page |
| `malloy_chart.py` | numbers inside it | `assets/malloy-skills-tokens.svg` |
| `build_search.py` | the finished pages | `pagefind/`, search box |
| `check_private.py` | staged files | nothing — blocks commit |
| `sync_template.py` | repository sources | `../static-site-template/` |

Order matters and `./build` encodes it: the tag index reads the writing data, so
writing runs first; search indexes the finished pages, so it runs last.

Generated files are output. Editing one by hand is erased by the next build.
