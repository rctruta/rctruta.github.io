# Numerical provenance

Status: planned; not implemented.

Structural validation checks document shape and references. It does not establish factual truth.

A future provenance system should:

- Distinguish assertions, attributed statements and derived measurements.
- Assign stable claim IDs with units, scope, dates and limitations.
- Reference versioned evidence and reproducible computations.
- Fail on missing evidence, changed sources or mismatched values.
- Maintain one authoritative source per measurement.
- Test supported claims and deliberate mismatches independently.

Specify this system separately before implementation. Avoid generic number scanning and optional private dependencies.
