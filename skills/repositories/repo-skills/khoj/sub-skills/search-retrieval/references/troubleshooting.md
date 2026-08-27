# Search Troubleshooting

## No Results

Check in this order:

1. Query text: empty `q` returns `[]` before search.
2. Ownership: search requires a valid `user` or `agent`; if neither owner is supplied internally, the adapter returns no entries. If an agent is supplied with a user, the agent must be accessible to that user.
3. Indexed content: the user or agent must actually have entries. If content was added but not indexed, route to content indexing/update guidance.
4. Filters: date, file, and word filters are ANDed with owner and content-type predicates. One bad filter can remove all candidates.
5. Date filters: unparseable date strings or non-intersecting ranges produce no useful date interval; indexed entries need extracted dates.
6. File filters: matching uses stored `file_path`; wildcard patterns are regex-expanded. Verify whether the stored path includes directories, source prefixes, or different separators.
7. Word filters: terms only match letters, digits, underscores, and hyphens inside quotes; matching is against raw entry text.
8. `max_distance`: an overly low value can remove all vector hits even when filters match.
9. Search type: restrictive `t` values filter by entry type. Try `t=all` when debugging type mismatch.

Use `scripts/inspect_query_filters.py 'your query'` to separate natural-language query text from filter terms before changing retrieval logic.

## Too Many or Noisy Results

- Lower `max_distance` or configure the search model's bi-encoder confidence threshold for callers that use the model default.
- Enable reranking with `r=true` when result order matters more than latency.
- Add precise `file:"..."`, `dt...`, or `+"word"` filters instead of relying only on semantic similarity.
- Keep `dedupe=true` for user-facing search unless repeated chunks are intentionally needed for debugging.
- Confirm the query is not mostly filter syntax; the embedded query should still contain meaningful natural-language text.

## Bad Filter Behavior

- Date syntax must be `dt` plus `:`, `=`, `==`, `>`, `>=`, `<`, or `<=`, followed by a quoted date phrase.
- Multiple date filters intersect; `dt>"1984-01-01" dt<"1984-01-01"` yields no valid range.
- File include filters are ORed, file exclude filters are negated, and then combined with the rest of the query predicates.
- `FileFilter.defilter()` removes include filters but can leave `-file:"..."` exclusions in the embedded query text. Account for this when comparing expected and actual embeddings.
- Word filters do not support multi-word phrases under the current regex; use separate word filters or change the implementation deliberately.

## Stale or Missing Index

Search relies on database entries and stored embeddings. If newly synced or edited content is absent:

- Confirm the relevant content source was indexed for the same user or agent being searched.
- Rebuild or update the index through Khoj's content update flow rather than changing search code first.
- If the configured bi-encoder changed, regenerate document embeddings so query and document vectors are comparable.
- If date filters fail on existing content, confirm dates were extractable from entry text at indexing time.

## Model Download or Backend Issues

Local models require transformer dependencies and access to model weights. Remote endpoints require valid endpoint URLs, API keys, and compatible response shapes.

Symptoms and likely causes:

- Server stalls or fails during first search/model setup: local model download or model load problem.
- Remote embedding failures: invalid endpoint, missing API key, rate limit, or unsupported endpoint type.
- Unexpected device errors: backend/device selection problem during local model load or inference.
- Results degrade after model config changes: documents need reindexing with the new bi-encoder.

Parser-only checks should import `khoj.utils.cli.cli` rather than the `khoj` console script, because the console script imports server startup code that can trigger migrations before argument parsing.

## User and Agent Isolation

The adapter builds an owner predicate from `user` and `agent`:

- User-only search returns entries for that user.
- Agent-only internal search returns entries for that agent.
- User plus agent search can include either owner, but helper-level access checks reject inaccessible agents.
- No owner returns no entries.

When a user reports missing results that another user can find, compare ownership, agent accessibility, and whether the same content was indexed for the same owner.

## Cross-Encoder Failures

If reranking via HTTP raises an HTTP error, Khoj logs the error and falls back to neutral cross scores instead of failing the response. If results appear in a strange order during a reranker outage, compare `score` and `cross_score`, disable `r`, or inspect inference endpoint health.

If local cross-encoder load or prediction fails outside the handled HTTP path, treat it as a model/backend setup issue. Prefer making reranking optional and preserving bi-encoder results where possible.
