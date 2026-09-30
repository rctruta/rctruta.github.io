# Working on this site

Rules for any agent — Claude, Cursor, or otherwise — touching this repository.
These are not style preferences. Each one exists because ignoring it cost
something.

## Generated files are output. Never edit them by hand.

| file | generated from | by |
| --- | --- | --- |
| `speaking.html` | `data/appearances.yaml` | `tools/build_speaking.mjs` |
| `tags.html`, and every tag row in `work.html` | `data/TAGS.yaml` | `tools/build_tags.py` |
| `assets/malloy-skills-tokens.svg` | numbers in the script | `tools/malloy_chart.py` |

Edit the data, run the tool, commit both. A hand edit to a generated file is
erased by the next build without warning.

```bash
node tools/build_speaking.mjs     # after changing appearances
python3 tools/build_tags.py       # after changing tags
python3 tools/malloy_chart.py     # after changing the study numbers
```

## Vocabulary is controlled, and the build enforces it

- **Appearances** — `data/TAXONOMY.md` fixes the exact words for `role`,
  `format`, `eventType`, and the spelling of every `org`. The Astro branch
  validates `appearances.yaml` against a schema; the build fails on anything
  outside the vocabulary.
- **Tags** — `data/TAGS.yaml` holds the vocabulary and which tags each project
  carries. `build_tags.py` exits non-zero on a tag that is not in the
  vocabulary, and on a project in the pages with no entry in the file.

**The tag rule:** a tag must name something at least two pieces of work share,
or something a reader would filter on. Implementation detail belongs in the
prose, where it already is. This was decided after an audit found 54 tags of
which 47 appeared exactly once — clicking one would have returned the page you
were already on.

## Never rename something that is published

A rename breaks every link anyone holds, and a static host has no server-side
redirects, so the only remedy is another file created solely to absorb damage
the rename caused. **The cheapest fix for a rename is not renaming.**

When a heading's wording is wrong, change the visible text and keep the `id`.
That is why `work.html` reads "Data Modeling & Data Engineering" above
`id="data-engineering"`.

Same for moving files, changing URLs, or restructuring a directory that works.

## Claims are gated

`.githooks/pre-commit` runs the verifier in `~/claude-docs-allowed/Resume/.claims`.
Every number on this site must be registered in `FACTS.yaml` with a source, and
third-party attribution is verified against the source system — the issue
tracker, the registry, the repository — never against an earlier draft.

The verifier makes a network call, so it can fail on a timeout. Retry before
concluding anything is wrong.

## Evidence about other people's software carries dates, not causation

State when a finding was measured, state when the upstream fixed it, link both,
and claim no connection between them without a public artifact proving one.
Name the nodes, not the edge.

## Writing

The prose is Ramona's. An agent supplies numbers, verification, structure and
mechanics. Quotations from private correspondence are anonymous; public
recommendations written under someone's own name keep that name.

## Type scale

Body is 17.5px. Anything acting as a heading must be larger. The scale is
`h2` 22 → `h3` 20 → `.role` 19 → `.inst` 17.5. This is recorded because a
subtitle was once set to 15.5px, below body size, and the resulting confusion
took several rounds to find.

## Anchors

`.topnav` is `position: sticky`, 63px tall. Every jump target needs
`scroll-margin-top` or it lands underneath the header. One rule covers the
whole site — do not add per-page offsets, and do not add a second rule.
