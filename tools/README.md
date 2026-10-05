# tools

Nothing in here is run by hand. Use `./build` at the repository root.

| generator | reads | template | writes |
| --- | --- | --- | --- |
| `build_work.py` | `data/work.yaml` | `templates/work.html` | `work.html` |
| `build_teaching.py` | `data/teaching.yaml` | `templates/teaching.html` | `teaching.html` |
| `build_speaking.py` | `data/appearances.yaml` | `templates/speaking.html` | `speaking.html` |
| `build_writing.py` | `data/writing.yaml` | `templates/writing.html` | `writing.html` |
| `build_contact.py` | `data/contact.yaml`, `config.yaml` | `templates/contact.html` | `contact.html` |
| `build_index.py` | `data/home.yaml`, `config.yaml`, data files | `templates/index.html` | `index.html` |
| `build_tags.py` | `data/TAGS.yaml`, data files | `templates/tags.html` | `tags.html` |
| `build_nav.py` | `config.yaml` / `NAV` list | — | top nav on every page |
| `malloy_chart.py` | numbers inside it | — | `assets/malloy-skills-tokens.svg` |
| `build_search.py` | the finished pages | — | `pagefind/`, search box |
| `check_private.py` | staged files | — | nothing — blocks commit |
| `sync_template.py` | repository sources | — | `../static-site-template/` |

Order matters and `./build` encodes it: the page generators run first using Jinja2 master layout (`templates/base.html`), then search indexes the finished pages, sync propagates to `static-site-template/`, and unit tests run.

Generated files are output. Editing one by hand is erased by the next build.
