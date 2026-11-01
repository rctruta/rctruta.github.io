# Build tools

Use `./build` from the repository root; it encodes generation order and required validation. Do not edit generated pages.

| Component | Responsibility |
| --- | --- |
| `contracts.py` | Strict YAML, authoritative JSON Schemas, references and index projection |
| `validate_site.py` | Source checks plus final links, anchors and per-term index membership |
| `config_loader.py` | Validated site configuration |
| `model.py` | Rendering adapters for validated public data |
| `build_work.py` | Work page |
| `build_teaching.py` | Teaching page |
| `build_speaking.py` | Speaking page |
| `build_writing.py` | Writing page |
| `build_contact.py` | Contact page |
| `build_index.py` | Home page |
| `build_rules_doc.py` | Derived kinds and organization tables |
| `build_tags.py` | Faceted Index from the shared validated projection |
| `build_nav.py` | Existing navigation postprocessor |
| `build_search.py` | Pinned Pagefind index and search shell |
| `page.py` | Shared rendering helpers |
| `bio.py` | Render the source bio for different destinations |
| `check_private.py` | Inspect staged content, or tracked working files with `--all-files` |
| `check_contracts.sh` | Interpreter selection for the local contract hook |

See [the contract documentation](../docs/contracts.md) for validation boundaries and deferred cleanup. No missing template-sync or chart-generator command is part of this build.
