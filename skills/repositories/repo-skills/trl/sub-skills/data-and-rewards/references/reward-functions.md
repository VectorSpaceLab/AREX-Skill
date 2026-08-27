# Reward Functions

TRL exposes built-in reward helpers primarily for GRPO and RLOO-style training. Reward functions receive batched data from trainers and should return one reward per completion. They must tolerate extra keyword arguments because trainers pass columns such as prompts, completions, solutions, and token ids.

## Completion message rewards

These functions expect completions shaped like `list[list[dict[str, str]]]`, where each inner list contains the generated assistant message and the message has `content`.

### `accuracy_reward(completions, solution, log_extra=None, **kwargs)`

Checks whether each completion matches the ground-truth solution using `math_verify` parsing and verification.

- Returns `1.0` for verified correct answers and `0.0` for parseable but wrong answers.
- Returns `None` when the gold solution is unparseable; trainers can skip that reward for the example.
- Raises `ImportError` if the optional `math_verify` dependency is unavailable.
- Uses boxed LaTeX extraction for answers, so math completions should put final answers in a parseable final form.
- If `log_extra` is supplied by a trainer, it logs solution and parsed answer diagnostics.

### `reasoning_accuracy_reward(completions, solution, reasoning_delimiters=None, log_extra=None, **kwargs)`

Removes reasoning content and verifies only the final answer.

- Defaults `reasoning_delimiters` to `["</think>"]`.
- Returns `0.0` when the completion lacks a reasoning delimiter, because incomplete reasoning is penalized rather than skipped.
- Like `accuracy_reward`, returns `None` when the gold solution is unparseable and requires `math_verify`.
- Use custom delimiters for non-`<think>` reasoning formats.

### `think_format_reward(completions, **kwargs)`

Checks for exactly one leading `<think>...</think>` block and returns `1.0` for valid format or `0.0` otherwise.

- Accepts multiline reasoning.
- Rejects missing closing tags, missing opening tags, nested `<think>` tags, and `<think>` blocks that do not start the completion.
- Does not verify answer correctness; combine with an accuracy or task-specific reward when needed.

## Token-id rewards

These functions return picklable callable objects. They operate on `completion_ids`, not completion text.

### `get_repetition_penalty_reward(ngram_size=3, max_penalty=-1.0)`

Creates a callable named `repetition_penalty_reward` that penalizes repeated token n-grams.

- Returns `0.0` for completions shorter than `ngram_size` or with no repeated n-grams.
- Returns a value in `[max_penalty, 0.0]` based on the fraction of repeated n-grams.
- Raises `ValueError` if `max_penalty` is positive.
- Accepts and ignores extra trainer kwargs.

### `get_soft_overlong_punishment(max_completion_len, soft_punish_cache)`

Creates a callable named `soft_overlong_punishment_reward` that penalizes overlong completions.

- Returns `0.0` when length is at most `max_completion_len - soft_punish_cache`.
- Returns a linear negative penalty between that boundary and `max_completion_len`.
- Returns `-1.0` when length exceeds `max_completion_len`.
- Use this as a length-shaping penalty, not as a positive reward for short answers.

## Mixed reward design

For mixed math/coding GRPO, combine rewards by interface and skip behavior:

- Use math rewards only on rows with parseable math `solution`; expect `None` on non-math or unparseable gold rows.
- Use format rewards such as `think_format_reward` across all rows if the model should always emit a reasoning block.
- Use token-id penalties for general anti-repetition or length shaping across all rows.
- For coding tasks, add a custom reward that returns `None` for rows it cannot judge rather than forcing `0.0` on unrelated tasks.
- Validate each reward independently on a tiny batch before passing the list into a trainer.

Example shape for direct reward testing:

```python
completions = [[{"role": "assistant", "content": "<think>x</think> answer"}]]
completion_ids = [[1, 2, 3, 2, 3]]
```

The text rewards use `completions`; token-id penalties use `completion_ids`.
