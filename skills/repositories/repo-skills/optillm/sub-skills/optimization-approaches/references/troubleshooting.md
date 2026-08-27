# Approach Troubleshooting

## Empty, `None`, or truncated provider responses

Approach tests cover graceful handling for some bad provider outputs. If a real request fails:

1. Check raw provider behavior with `none` direct proxy.
2. Lower `max_tokens` or set provider-specific max-token fields correctly.
3. Avoid passing a truncated response into a second pipeline stage without validation.
4. Prefer approaches with explicit response guards (`re2`, `leap`, self-consistency/rto paths) when provider reliability is weak.

## Multi-call cost or latency is too high

- Reduce `n`, BoN candidates, MCTS simulations/depth, MARS agents/iterations, and CePO planning counts.
- Start with `re2` or `cot_reflection` before `moa`, `cepo`, or `mars`.
- Use a faster/lower-cost base model for critique/verification only when quality is acceptable.
- Avoid `a|b|c` parallel composition unless multiple alternative outputs are useful.

## Provider lacks multiple-completion support

If the endpoint does not support `n` or multiple choices, avoid workflows that depend on one provider call returning many candidates. Use sequential or single-response approaches first: `re2`, `cot_reflection`, `leap`, `plansearch`, `rstar`, `rto`, `self_consistency`, or `z3`.

## MCTS parameters appear to leak across requests

Current dispatch reads MCTS parameters from per-request config with server defaults as fallback. If behavior appears cross-request contaminated, verify that client code is not mutating shared request dictionaries and run a focused parser/dispatch test.

## Z3 or math verification fails

Symptoms include missing `z3`, `sympy`, or `math_verify`, invalid generated solver code, or timeouts.

Recovery:

- Check package dependencies with the root `inspect_optillm.py` helper.
- Keep solver-generated code bounded and inspectable.
- Fall back to LLM-only reasoning if the problem is not symbolic or constraints cannot be extracted reliably.

## CePO config issues

- Confirm the selected config file contains all required `CepoConfig` fields.
- Match token budgets to provider limits.
- If `rating_model` is set, ensure that model is accessible through the provider.
- If majority rating gives wrong answers, inspect extraction format and `last_n_chars` style assumptions in evaluation code before trusting scores.

## MARS answer extraction issues

- For numerical answers, `answer_extraction_mode: auto` can help compare solutions.
- For proof tasks, stripping thinking or extracting only the final answer can remove necessary proof context.
- For code generation, preserve code blocks and check whether thinking tags help or hurt downstream evaluators.

## Parallel/pipeline composition surprises

`&` pipelines pass the response of one approach as the next query. That can be powerful but can also amplify formatting artifacts. If the second stage misunderstands the first output, add a simpler chain or use a single stronger approach.

`|` parallel composition returns multiple responses. Ensure the client and downstream code can handle list-like content or multiple choices.
