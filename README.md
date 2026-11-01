# Contract-driven static portfolio

A static portfolio generated from public YAML documents and governed by portable JSON Schemas. Work, teaching, writing and appearances share a controlled taxonomy and a validated index projection.

## Local setup

Requires Python 3.12+ and Node.js 22.12+. Install from the checked-in dependency versions:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
npm ci
pipx install pre-commit==4.5.1
```

If pre-commit is already installed, reuse it. Select the repository's checked-in hook explicitly:

```sh
git config core.hooksPath .githooks
```

This is a local Git setting, not something cloning installs automatically. CI runs required checks independently of local hooks. A normal build also runs all declared pre-commit checks. Initial tool installation requires network access.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
fix(links): validate local destinations
```

The `commit-msg` hook runs pinned commitlint with the conventional configuration. CI checks incoming commit ranges independently. Breaking source-format changes use `!` and a `BREAKING CHANGE:` footer. Keep messages concise and technical.

Validate a draft without committing:

```sh
npm run lint:commits -- --edit path/to/message.txt
```

## Build and validate

```sh
./build
```

The build selects `.venv/bin/python` when available; `PYTHON` may select another prepared interpreter. It validates sources first, generates pages and index, rebuilds pinned Pagefind output, runs declared checks, validates final links/anchors/index membership, and runs tests. Invalid input stops the command; it is never skipped.

For read-only validation or tests using the prepared environment:

```sh
.venv/bin/python tools/validate_site.py --sources-only
.venv/bin/python tools/validate_site.py
.venv/bin/python -m unittest discover -s tests -t .
```

The first command is the pre-generation phase. The second additionally requires existing generated output. Neither modifies source files. Generated HTML and `pagefind/` are committed artifacts; do not edit them manually.

## Architecture and contracts

- `config.yaml`: site metadata and navigation.
- `data/TAGS.yaml`: stable concept IDs, display labels, facets, search terms and relationships.
- `data/*.yaml`: content, referencing concept IDs.
- `schemas/*.schema.json`: authoritative JSON Schema Draft 2020-12 documents.
- `tools/contracts.py`: YAML parsing, schema enforcement and cross-record rules.
- `tools/model.py`: validated rendering adapters.
- `templates/`: shared page layout and page templates.
- `tools/build_*.py`: generators called in dependency order by `./build`.
- `tests/`: invalid-input, preservation and output checks.

See [contract rules](docs/contracts.md), the [accepted standards decision and future roadmap](docs/decisions/001-portable-data-contracts.md), and [contributor instructions](AGENTS.md).

## Reuse

Replace public data and site configuration, choose a namespace for your concepts, and adapt schema `$id` URIs before publishing your own schema authority. Preserve concept identities separately from labels and HTML anchors. Follow validation errors rather than adding exceptions. Private resume drafts and employment data are not required to build the site.

SKOS export, ODCS integration and OWL translation are recorded future work, not implemented features. The current site does not verify the factual truth of prose claims merely because their document structure validates.

[Numerical provenance](docs/decisions/002-claims-and-numerical-provenance.md) is planned separately.

CI runs the build and refuses stale committed HTML, rules documentation or search artifacts. This repository does not automatically publish from its build command.
