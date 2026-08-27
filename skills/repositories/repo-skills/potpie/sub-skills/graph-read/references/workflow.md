# Graph read workflow reference

Potpie offers root convenience reads and graph workbench reads. Use the simplest command that returns the identity and context needed for the next step.

## Command matrix

| Goal | Command | Use when |
| --- | --- | --- |
| Intent-driven context package | `potpie resolve ...` | You want agent-facing context for a task or intent. |
| Broad memory search | `potpie search ...` | You need free-text retrieval across stored context. |
| Discover graph surface | `potpie graph catalog` | You need supported subgraphs, views, includes, or labels. |
| Named read view | `potpie graph read ...` | You know the subgraph/view and need structured output. |
| Find entity keys | `potpie graph search-entities ...` | You need canonical entity keys before describe/neighborhood/write. |
| Entity explanation | `potpie graph describe <entity-key>` | You need labels, properties, or attached evidence for one entity. |
| Local graph context | `potpie graph neighborhood <entity-key>` | You need nearby relationships around an entity. |
| Inspect graph object | `potpie graph inspect ...` | You need a focused read/admin inspection of one graph object. |
| Export graph data | `potpie graph export <file>` | You need a portable graph snapshot; confirm file argument and sensitivity. |
| Recent events | `potpie timeline recent ...` | You need chronology, change history, or event recency. |
| Readiness probe | `potpie graph status` | You need read-side graph readiness, not root runtime status. |

## Choosing the read path

1. If the user asks in natural language and does not know graph names, start with `resolve` or `search`.
2. If the user needs typed graph output, run `graph catalog` and choose a documented subgraph/view.
3. If a later write needs an entity key, use `graph search-entities` first.
4. If the result is empty, confirm pot/source state and scope filters before broadening the query.
5. If the result says unsupported, change the include/view rather than retrying the same call.

## Named view and include notes

- Potpie's graph contract is versioned around graph contract `v1.5` and ontology `2026-06-graph` in this repo version.
- The graph surface distinguishes **reader-backed includes** from **planned/requestable includes**. A planned include may be accepted by the contract but return best-effort or unsupported output.
- Use `../../scripts/generate_agent_contract.py` from the root skill to inspect the installed package's current intent/include manifest when the skill may be stale.

## Scope and source handling

Read commands are meaningful only in the correct pot/source context. Before treating an empty response as absent data:

```bash
potpie pot info
potpie pot linked
potpie source list
potpie graph status
```

Then retry with explicit scope/source filters or broaden the query deliberately.

## Output interpretation

| Result pattern | Meaning | Next step |
| --- | --- | --- |
| Empty list / no matches | Query was valid but found no records in the selected scope. | Broaden query, check pot/source, or create data through write paths. |
| Unsupported include/view | The requested include/view is not backed by this runtime. | Use `graph catalog` or generated contract output to choose a supported include. |
| Ambiguous entity results | Search matched multiple canonical keys. | Use `graph describe` or narrower type/source filters before writing. |
| Daemon unavailable | CLI import worked, but graph service cannot answer. | Route to `runtime` and inspect daemon/backend. |

## Good read-to-write handoff

When a read will drive a write, capture:

- pot/source context,
- command and filters used,
- canonical entity key(s),
- evidence/snippet identifiers,
- whether the result was reader-backed or best-effort.

Then route to `graph-write` for proposal or record creation.
