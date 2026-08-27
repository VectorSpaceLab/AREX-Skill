# Graph Exploration Troubleshooting

## Search returns keyword-only results

**Symptoms**
- A semantic search behaves like a plain name search.
- Results look plausible but miss the expected related symbol.

**Likely causes**
- Embeddings are not available in the current environment.
- The query is too vague to prefer a structural match.
- The graph has no relevant nodes yet.

**Recovery**
1. Fall back to `query_graph_tool` or `traverse_graph_tool`.
2. Use exact names, file paths, or call relationships when possible.
3. Install the optional embeddings extra only if semantic search is actually needed.

## Flow analysis seems incomplete

**Symptoms**
- A clearly important entry point is missing from flow results.
- A decorator-based route or framework callback was not detected.

**Likely causes**
- The parser does not have the language/framework cue it needs.
- The repo is missing the specialized framework evidence that would mark an entry point.
- The graph is stale.

**Recovery**
1. Rebuild or update the graph.
2. Check whether the symbol is decorated, test-only, or in an unsupported language.
3. Use `get_affected_flows_tool` to see whether a change touched a flow even if the flow list is sparse.

## Community detection is sparse or missing

**Symptoms**
- `communities` output is tiny, empty, or falls back to simple grouping.

**Likely causes**
- The optional `igraph` dependency is missing.
- The repo is too small or too uniform to produce rich clusters.

**Recovery**
1. Treat the fallback as valid if `igraph` is intentionally absent.
2. Install the communities extra only when the workflow truly depends on community structure.
3. Use `architecture` and `list_flows` to get other structural signals.

## Refactor preview is incomplete

**Symptoms**
- A rename preview misses a call site or includes an unrelated symbol.
- A dead-code result includes something that clearly should not be removed.

**Likely causes**
- The symbol name is overloaded across languages or scopes.
- The graph has not yet resolved the target from a fresh build.

**Recovery**
1. Preview again with a more specific symbol name or file pattern.
2. Rebuild the graph if the repository changed recently.
3. Inspect the returned edits before applying anything.

## When to stop

Stop and ask for help when the missing result depends on:
- a not-yet-installed optional backend,
- a language the parser does not support,
- or repository history that is not present in the current checkout.