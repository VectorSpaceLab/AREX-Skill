# Graph read troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Empty result from a valid read | Wrong pot/source scope, too narrow filters, or no records exist yet. | Inspect pot/source state, broaden query, and check whether a write/ingest path has populated data. |
| `unsupported` or `not_implemented` include | Include or named view is requestable but not reader-backed in this runtime. | Run `potpie graph catalog` or `python ../../scripts/generate_agent_contract.py` and choose a reader-backed include/view. |
| Many unrelated results | Query is too broad or match mode favors lexical/vector recall over precision. | Add source/type/scope filters, use `search-entities`, or refine query terms. |
| Multiple entity keys for one concept | Entity normalization found several candidates. | Use `graph describe` and source/type filters before a write. |
| `graph status` fails | Daemon/backend is unavailable. | Route to `runtime`; check `potpie daemon status` before changing graph commands. |
| Timeline is empty but graph reads work | Event records may not exist for the selected scope/window. | Broaden time window, remove source filters, or confirm event-producing workflows ran. |
| A read returns planned/best-effort sections | The contract knows the include, but no concrete reader fully supports it yet. | Treat as advisory and avoid basing destructive changes on that section alone. |

## Empty versus unsupported

- **Empty** means the route is valid but no records matched the current filters.
- **Unsupported** means the route itself is not implemented or not reader-backed.
- Do not fix unsupported output by adding more data. Choose a supported include/view instead.
- Do not fix empty output by changing includes first. Verify pot/source/scope and whether data exists.

## Scope mismatch checklist

1. `potpie pot info`
2. `potpie pot linked`
3. `potpie source list`
4. `potpie graph status`
5. `potpie graph catalog`
6. Retry with explicit `--scope`, `--source`, `--type`, or equivalent filters from the current command help.

## Entity-resolution checklist

1. Use `graph search-entities` with the narrowest known type/source.
2. Inspect the candidate with `graph describe`.
3. If relationships matter, inspect `graph neighborhood`.
4. Only then route to `graph-write` with the canonical key.

## Staleness signal

If command names, include families, or ontology labels differ from this reference, regenerate the installed-package contract with `../../scripts/generate_agent_contract.py` and treat the generated skill as stale until refreshed.
