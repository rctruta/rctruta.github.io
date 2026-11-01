# Portable data contracts

## Standards

- JSON Schema Draft 2020-12 defines document structure.
- Cross-record validators enforce references and publishing rules.
- Stable concept IDs, labels and relationships align with SKOS semantics.
- ODCS integration is deferred until a dataset consumer requires it.

## Planned exports

**SKOS:** export stable concept URIs, labels, scope notes and explicit relationships. Validate the supported SKOS subset and preserve website anchors.

**ODCS:** describe a defined dataset interface, ownership, compatibility and executable quality checks. Pin the specification version and derive structural definitions from one authoritative source.

**OWL:** define a separate mapping when required. SKOS concepts do not automatically become OWL classes.

Exports must be deterministic and tested against the validated source. Search keywords must not become semantic relationships automatically.

## References

- [JSON Schema](https://json-schema.org/specification)
- [SKOS](https://www.w3.org/TR/skos-reference/)
- [ODCS](https://bitol-io.github.io/open-data-contract-standard/)
