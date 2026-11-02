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

**Never edit generated HTML files by hand.** Edit the data in `data/`, run `./build`, and include generated HTML with the source changes. `pagefind/` and `dist/` are build-only:

```bash
./build
```

`./build` executes generators in the correct dependency order, builds the search index, runs pre-commit linters, and verifies the test suite.

## Controlled Vocabulary & Taxonomy

- **Appearances:** `schemas/appearances.schema.json` defines the allowed values for `role`, `format`, `eventType`, and organization names.
- **Tags:** `data/TAGS.yaml` defines the taxonomy. Records use stable concept IDs; templates resolve display labels. A tag must describe a common attribute shared by projects, or a dimension readers would filter on.
- Project IDs are unique within the Work page; assigned concept IDs must exist in `data/TAGS.yaml`.
- JSON Schemas in `schemas/` are authoritative structural contracts. Cross-record validators in `tools/contracts.py` are mandatory. Never weaken a check, add exclusions or silently omit invalid records to pass a build.
- Consult `docs/contracts.md` and `docs/decisions/001-portable-data-contracts.md` before changing data models or standards integration.
- Preserve published anchors when changing labels. Schema `$id` and taxonomy namespace are explicit portability decisions.

## Design & Layout Conventions

- **Type Scale:** Body font is 17.5px. Heading hierarchy: `h2` 22px → `h3` 20px → `.role` 19px → `.inst` 17.5px.
- **Sticky Navigation:** `.topnav` is `position: sticky` (63px tall). Jump targets require `scroll-margin-top` to avoid landing underneath the header.
- **Links & Metadata:** Visible metadata belongs in `span.meta`. Avoid tooltips or hover-only text for essential details to maintain mobile accessibility.

## Code Standards & Hygiene

- **Branches:** Create a work branch before editing. Never commit or push directly to `main`.
- **Pull requests:** Submit changes through a PR. Required CI must pass before merge.
- **Git actions:** The owner runs commit, push and merge commands. Agents provide the commands but do not execute them. Do not rewrite published history or bypass hooks or repository protection.
- **Staging:** Stage explicit file paths after reviewing the diff. Do not use bulk staging commands.

- **Testing:** Run `.venv/bin/python -m unittest discover -s tests -t .` to verify all page contracts.
- **Secrets & Privacy:** PII and credentials must never be committed. `gitleaks` and `tools/check_private.py` run on commit to prevent accidental exposures.
- **Git Commits:** Use standard Conventional Commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`).
- **Commit validation:** The `commit-msg` hook and CI use pinned commitlint. Validate proposed messages before requesting approval. Do not bypass hooks.

## Public writing

Keep comments, docstrings and documentation concise and technical. Exclude incident histories, personal context, chat references and agent narratives.
