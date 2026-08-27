# ReAct tool protocol, caches, and failure control

## Tool exposure and order

`get_tools_definition()` exposes OpenAI function definitions in this exact order:

1. `search_papers`
2. `load_paper`
3. `read_section`
4. `get_full_paper`
5. `get_paper_preview`
6. `quick_preview`

The system prompt describes the first five explicitly but does not list `quick_preview`; the tool is nevertheless exposed to the model. Do not infer that an undocumented tool is unavailable—inspect the definition order above.

Every definition uses the OpenAI function-calling shape:

```json
{"type":"function","function":{"name":"...","description":"...","parameters":{"type":"object", ...}}}
```

The planning node passes all definitions with `tool_choice: "auto"`. The forced answer path passes `tools=None`, intentionally preventing another tool loop.

## Tool contracts

| Tool | Required inputs | Important behavior |
|---|---|---|
| `search_papers` | `query` | Calls `Reader.search`; defaults to `size=10`, `offset=0`, `source="arxiv"`, and `use_fine_rerank=False`. Supports authors, orgs, categories, venue, venue year, minimum citations, and date bounds. |
| `load_paper` | `arxiv_id` | Calls `Reader.head`; stores metadata in state. Must precede section/full-paper reads. |
| `read_section` | `arxiv_id`, exact `section_name` | Requires a loaded paper and an available exact section name; uses the section cache before calling `Reader.section`. |
| `get_full_paper` | `arxiv_id` | Requires a loaded paper; uses the full-paper cache before calling `Reader.raw`. |
| `get_paper_preview` | `arxiv_id` | Calls `Reader.preview` directly for a bounded overview; it does not require the paper to be loaded first and has no Agent cache. |
| `quick_preview` | `arxiv_ids` | Calls `Reader.brief` concurrently (up to five workers by default), preserves the input order in formatted output, and has no Agent cache. An empty list returns an error string. |

`search_papers` accepts `source` values `arxiv`, `biorxiv`, and `medrxiv`. It chooses the source-specific ID field when formatting results, with fallbacks across the three known ID fields. Its output includes total/showing counts, active filters, title, ID, score, citations, categories, venue, and a truncated abstract/TLDR.

`load_paper` stores title, abstract, authors, sections, token count, categories, publication date, and `loaded_sections={}`. It formats section names, section TLDRs, section token counts, and total token count for the model. If already in state it returns an “already loaded” message without another head request.

`read_section` requires exact name matching against the loaded paper's section list. A missing exact name returns an available-section list and does not call the Reader. A successful fetch is returned with start/end delimiters and written to both `state["paper_sections_cache"][arxiv_id][section_name]` and the paper's `loaded_sections`.

`get_full_paper` requires `arxiv_id` in state, then caches the raw content in `state["full_paper_cache"][arxiv_id]`. It can return a very large response; follow the prompt's token-count and progressive-reading guidance.

## State and cache lifetimes

`create_initial_state(papers=...)` initializes:

- `papers`: the supplied paper dictionary or `{}`;
- `messages`: an empty list accumulated by LangGraph;
- `paper_sections_cache`: empty nested map;
- `full_paper_cache`: empty map;
- `search_results_cache`: an empty list;
- `consecutive_failures=0`, `round=0`, and a fresh `start_time`.

The current search implementation receives the whole state as `state_cache` and writes raw results to `state["search_results"]`; it does not populate the predeclared `search_results_cache` list. Section and full-paper caches are per-query state and are discarded after the query. Only the final `papers` map is merged into `Agent.persistent_papers`, so a later query may fetch a section/full body again.

`format_paper_context()` puts only each persistent paper's ID, title, and the first 200 abstract characters into the new query's system prompt. Section bodies and prior messages are not automatically carried over.

## Correct call sequence

Use the following decision order when guiding a model or writing a fake client:

1. Search when no relevant persistent paper is present.
2. Load a candidate to obtain metadata and section TLDRs.
3. Prefer metadata/TLDRs for simple questions.
4. Use `get_paper_preview` for a bounded overview, or read one exact section after checking its token count.
5. Use `get_full_paper` only when comprehensive content is necessary.
6. Synthesize and wrap the final answer in `<answer>...</answer>` when ready.

After a tool-call assistant message, the graph executes all tool calls in that message in order, appends their results, and checks limits before planning another round. A tool-call result is a string; malformed JSON arguments are converted to `{}` and therefore normally produce an invalid-argument or missing-input result rather than raising to the graph.

## Error classification and recovery

`is_service_failure(result_text)` is a string-marker classifier. It returns true when a result contains any of:

- `the paper data service returned an error`
- `Error executing `
- `Failed to search`
- `Failed to fetch`
- `Failed to load`

The classifier returns false for empty strings and for normal recoverable messages such as “paper is not loaded” or “section not found.” It is intentionally broad: the generic `Error executing ...` prefix also counts as a service failure.

`ToolExecutor.execute_tool_call()` maps Reader exceptions as follows:

- `NotFoundError`: returns a recoverable “could not find” message, notes that a very recent paper may not be indexed, and tells the model not to retry the exact ID.
- `BadRequestError`: returns a recoverable invalid-arguments message so the model can correct the ID/query.
- `APIError` (including server, auth, and rate-limit subclasses): returns an `Error executing ...` service-side message. The model is told not to hammer the same call.
- Any other exception: returns `Error executing <tool>: ...`, which the marker classifier also counts as service failure.

A missing/unloaded paper and a wrong section are not evidence that the upstream service is down. Correct the tool order, ID, or section name and continue.

## Circuit breaker and budgets

For each tool-call round, `tool_call_node` sets `all_failed` only when every returned tool result is classified as a service failure. One successful/non-service result resets `consecutive_failures` to zero; an all-failure round increments it.

`check_limits_node` forces a final answer when either condition is true:

- `max_consecutive_failures > 0` and `consecutive_failures >= max_consecutive_failures` (default threshold 3), or
- `round >= max_llm_calls - 2` (approaching the call limit).

The forced request appends a user instruction asking for a final answer based only on gathered information. It sends no tools. If the model returns answer tags, the tags are stripped into `prediction`; otherwise the raw content is returned. Breaker termination is labelled `service_unavailable` (or `answer (service_unavailable)` with tags). Set `max_consecutive_failures=0` only when deliberately accepting repeated service retries.

The planning node also returns a timeout answer if elapsed time exceeds `max_time_seconds`, and an exceeded-call answer if the available count reaches zero. Normal planning rounds decrement `num_llm_calls_available`; the forced answer also decrements it. The graph uses `recursion_limit=100`, which is a LangGraph recursion guard rather than the user-facing call budget.
