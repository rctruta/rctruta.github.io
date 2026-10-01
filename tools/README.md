# tools

Nothing in here is run by hand. Use `./build` at the repository root.

| generator | reads | writes |
| --- | --- | --- |
| `build_speaking.mjs` | `data/appearances.yaml` | `speaking.html` |
| `build_writing.py` | `data/writing.yaml` | `writing.html` |
| `build_tags.py` | `data/TAGS.yaml`, `data/writing.yaml` | `tags.html`, every tag row |
| `build_nav.py` | the `NAV` list inside it | the top nav on every page |
| `malloy_chart.py` | numbers inside it | `assets/malloy-skills-tokens.svg` |
| `build_search.py` | the finished pages | `pagefind/`, the search box |
| `check_private.py` | staged files | nothing — it blocks the commit |

Order matters and `./build` encodes it: the tag index reads the writing data, so
writing runs first; search indexes the finished pages, so it runs last.

Generated files are output. Editing one by hand is erased by the next build.
