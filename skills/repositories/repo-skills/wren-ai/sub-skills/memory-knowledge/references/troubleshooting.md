# Memory Troubleshooting

## `wren memory fetch` says the memory extra is missing

The lightweight fallback supports durable query-pair storage and recall, but
semantic schema retrieval needs the optional stack:

```bash
pip install "wrenai[memory]"
```

Do not install it unless semantic retrieval is actually needed; it has a much
larger footprint than the base CLI.

## Index is stale or `check` reports drift

Keep `knowledge/sql/` as the recovery source. Rebuild derived state:

```bash
wren memory index
wren memory check
```

Avoid deleting source pairs to clear an index. `wren memory reset` removes
only the derived index and preserves durable pair files.

## Memory commands cannot locate a project or MDL

Run from a Wren project, provide the command's explicit MDL/path option, or
fix project discovery. Build the project before commands that need
`target/mdl.json`.

## Concurrent indexing problems

Do not run `wren memory index` while an agent/toolkit is actively using the
same project. Reindexing can recreate derived structures; wait for active
queries to finish or use a separate staged project copy.

## Wrong business answer despite valid SQL

Inspect `wren context instructions`, relevant knowledge rules, stored pairs,
and model descriptions. Dry-plan validates semantics and dialect shape, not
whether a missing business convention was modeled.
