# Data contracts

Pipeline: YAML → validation → rendering adapters → templates → HTML → Pagefind.

## Schemas and validation

`schemas/*.schema.json` are authoritative JSON Schema Draft 2020-12 documents with stable `$id` URIs. Validation uses local schema files and requires no network access.

`tools/contracts.py` rejects duplicate YAML keys, aliases, unknown fields, invalid types, missing values and invalid dates. Mandatory relationship checks cover taxonomy references, IDs, normalized labels, anchors and local assets.

`tools/validate_site.py` checks generated IDs, local links, fragments and exact index membership per term. Every record is validated before publication filtering. Missing template variables fail rendering.

`--sources-only` is the pre-generation phase. The full build also validates generated output.

## Taxonomy

`data/TAGS.yaml` declares facets, kinds, concepts and an HTTPS namespace. Concept URIs use the namespace plus the stable concept key. Display labels and published HTML anchors are independent of identity.

- `alternate_labels`: unambiguous equivalent names.
- `search_terms`: discovery phrases, without equivalence assertions.
- `related`: references to other concepts; no self-links.
- `scope_note`: optional concept definition.

Records reference concept IDs. Work sections organize the page independently of taxonomy. The public index displays concepts used by published records; unused declarations remain valid.

## Content

- Work requires section and project IDs, titles, descriptions, activities and tags. Dates are optional and never inferred.
- Recognition requires attribution, date and an HTTP(S) source. Badge URLs require alternative text.
- Notes require text or a complete label/URL pair.
- Résumé fields contain approved text; draft placeholders fail validation.
- Appearances contains `guest_host_note` and `items`. Talks render; podcasts render when a URL exists.
- Teaching stores the outreach note at `service.outreach_note`. Degree years are metadata and are not displayed.
- Writing, Home, Contact and configuration have closed schemas.

## Index and search

The shared index projection contains record identity, kind, title, destination, concept IDs and an optional explicit date. Work and Teaching use source order; Writing and Speaking sort by date.

Counts represent record/concept relationships. Pagefind indexes generated public pages using the pinned dependency. Rebuilds replace obsolete search artifacts.

Search output is build-only. Its manifest records input and dependency hashes plus all generated artifact hashes. Validation rejects stale inputs, missing files and changed artifacts.

## Build and CI

Follow the setup in the root README and run `./build`. It validates sources, generates pages and search, runs declared checks, validates output and runs tests. CI repeats the build and rejects stale committed artifacts.

Privacy checks inspect staged content. Python dependencies and Pagefind are pinned. Public assets referenced by content must be included in the repository.

See [development and release](development-workflow.md) for required PR checks and deployment controls.

## Future work

See [standards and exports](decisions/001-portable-data-contracts.md) and [numerical provenance](decisions/002-claims-and-numerical-provenance.md). Navigation/search template consolidation and inline Markdown formatting remain separate tasks.
