# Flow Troubleshooting

## Unexpected tuple/list/dict output

**Likely cause**: `parallel` and `diverter` return tuple-like outputs by default; named diverters can produce dicts; nested flows may preserve one-item tuple/list shapes.

**Recovery**

1. Replace heavy nodes with simple callables.
2. Assert shape after each primitive.
3. Use `_skip_items` or `_kept_items`, not both.
4. Convert output shape explicitly before handing data to RAG/agent/model nodes.

## `bind` passes the wrong value

**Likely cause**: bound values reference the original input or a named prior stage, not necessarily the current stage output.

**Recovery**

- Name pipeline stages in a context manager.
- Bind `p.input` when the later function needs the original input.
- Bind `p.stage_name` when it needs a prior output.
- Test with short strings/numbers before using modules.

## Conditional route does not fire

**Likely cause**: predicate checks the wrong input shape or `judge_on_full_input` is set incorrectly.

**Recovery**

- Decide whether the predicate should see the full input or converted value.
- Add a default route to distinguish false/no-match from a failed action.
- Keep predicate exceptions visible when they indicate invalid inputs.

## Loop does not stop

**Likely cause**: missing/incorrect stop condition or runtime limit expansion that does not increase the limit.

**Recovery**

- Prefer `count` while prototyping.
- Add a simple stop condition with a visible monotonic value.
- Avoid unbounded loops around model/provider calls.

## Parallel/concurrency side effects

**Likely cause**: parallel branches mutate shared state, use external services, or rely on multiprocessing-incompatible objects.

**Recovery**

- Start with `_concurrent=False` or sequential parallel where needed.
- Do not share mutable clients across process boundaries.
- Make provider/RAG/tool branches idempotent before enabling concurrency.
