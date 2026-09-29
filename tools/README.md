# tools

`build_speaking.mjs` generates `speaking.html` from `data/appearances.yaml`.

    node tools/build_speaking.mjs

`speaking.html` is output. Edit the YAML, run the command, commit both.
`data/TAXONOMY.md` holds the exact vocabulary; the Astro branch validates
the same file against a schema.
