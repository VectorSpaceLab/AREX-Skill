# Search Troubleshooting

Read this when a search or recall query returns nothing, raises a validation error, or uses the wrong mode.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `code_query requires query_type=SearchType.CODE` | The user asked for code traversal but did not select CODE mode. | Switch to `SearchType.CODE` and provide the structured code query payload. |
| `skills/tools require query_type=SearchType.AGENTIC_COMPLETION` | The query is trying to use agentic tools in a non-agentic mode. | Switch to `AGENTIC_COMPLETION` or remove the tool/skill overrides. |
| `neighborhood_depth` or `neighborhood_seed_top_k` validation errors | One of the search depth knobs is zero, negative, or not an integer. | Set a positive integer or remove the knob. |
| `node_name_filter_operator` rejected | The operator is not `AND` or `OR`. | Use one of the accepted values exactly. |
| `recall` ignores the graph and only uses session scope | The query was routed with session-only intent or `session_id` only. | Pass a dataset, a query type, or an explicit `scope` to broaden the search. |
| Search returns empty results | Wrong dataset, wrong `SearchType`, too small `top_k`, or the graph was never built. | Broaden the query, confirm the dataset, run `cognify` first, or switch modes. |
| Results look like the wrong retrieval family | `auto_route=True` picked a different mode than the user expected. | Set `query_type` explicitly or explain the router choice using the query intent. |
| `graph_context` appears in old notes | That scope name is deprecated. | Use `scope="graph"` instead. |

## Safe next checks

1. Run the decision helper:

   ```bash
   python scripts/choose_search_mode.py --help
   ```

2. Re-read the search mode table if the user wants a different trade-off.
3. If the underlying issue is provider/backend related, route to
   [configuration-backends](../../configuration-backends/SKILL.md).
