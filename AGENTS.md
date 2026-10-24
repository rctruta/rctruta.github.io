# Working on this site

Guidelines for contributors and AI coding assistants working in this repository.

## Architecture

This website is a contract-driven, static portfolio. Content pages are compiled from structured YAML data files in `data/`:

| Generated Page | Source Data | Generator Tool |
| --- | --- | --- |
| `work.html` | `data/work.yaml` | `tools/build_work.py` |
| `teaching.html` | `data/teaching.yaml` | `tools/build_teaching.py` |
| `speaking.html` | `data/appearances.yaml` | `tools/build_speaking.py` |
| `writing.html` | `data/writing.yaml` | `tools/build_writing.py` |
| `tags.html` | `data/TAGS.yaml` + data files | `tools/build_tags.py` |
| `contact.html` | `data/contact.yaml` + `config.yaml` | `tools/build_contact.py` |
| `index.html` | `data/home.yaml` + `config.yaml` | `tools/build_index.py` |
| Top navigation | `config.yaml` | `tools/build_nav.py` |
| `pagefind/` | Generated HTML pages | `tools/build_search.py` |

### The Build Script

**Never edit generated HTML files by hand.** Edit the data in `data/`, run `./build`, and commit both the data and the generated output:

```bash
./build
```

`./build` executes generators in the correct dependency order, builds the search index, runs pre-commit linters, and verifies the test suite.

## Controlled Vocabulary & Taxonomy

- **Appearances:** `data/APPLICATION-RULES.md` defines the allowed values for `role`, `format`, `eventType`, and organization names.
- **Tags:** `data/TAGS.yaml` defines the taxonomy. A tag must describe a common attribute shared by projects, or a dimension readers would filter on.
- All project IDs and tagged entries must be registered in `data/TAGS.yaml`.

## Design & Layout Conventions

- **Type Scale:** Body font is 17.5px. Heading hierarchy: `h2` 22px → `h3` 20px → `.role` 19px → `.inst` 17.5px.
- **Sticky Navigation:** `.topnav` is `position: sticky` (63px tall). Jump targets require `scroll-margin-top` to avoid landing underneath the header.
- **Links & Metadata:** Visible metadata belongs in `span.meta`. Avoid tooltips or hover-only text for essential details to maintain mobile accessibility.

## Code Standards & Hygiene

- **Testing:** Run `python3 -m unittest discover -s tests -t .` to verify all page contracts.
- **Secrets & Privacy:** PII and credentials must never be committed. `gitleaks` and `tools/check_private.py` run on commit to prevent accidental exposures.
- **Git Commits:** Use standard Conventional Commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`).
