# verl Reward Functions

## Reward data contract

Reward managers receive a `DataProto`. For each sample, they read:

- response tokens from tensor fields such as `responses` and `attention_mask`;
- `data_source` from `non_tensor_batch`;
- `reward_model["ground_truth"]` from `non_tensor_batch`;
- optional `extra_info` from `non_tensor_batch`.

The tokenizer decodes generated response tokens into `solution_str`, then the configured reward function is called with dataset metadata and the decoded response.

## Built-in default reward dispatch

`verl.utils.reward_score.default_compute_score` routes by `data_source`:

| `data_source` pattern | Scorer family |
| --- | --- |
| `openai/gsm8k` | GSM8K exact answer after `####`, with optional format score. |
| `lighteval/MATH`, `DigitalLearningGmbH/MATH-lighteval`, `HuggingFaceH4/MATH-500` | MATH scorer. |
| `math_dapo`, `math`, `math_dapo_reasoning`, or names starting with `aime` | DAPO math scorer. |
| Numina math source names | Prime math scorer. |
| `codecontests`, `apps`, `codeforces`, `taco` | Sandbox Fusion when configured, otherwise Prime Code. |
| `hiyouga/geometry3k` | Geo3K scorer. |
| `searchR1_*` QA names | Search-R1-like exact/subexact QA scorer. |

If `data_source` is not recognized and no custom scorer replaces dispatch, reward computation raises `NotImplementedError`.

## Ground-truth alignment

The `reward_model.ground_truth` value must match the scorer, not merely the raw dataset answer.

- GSM8K preprocessing extracts the value after `####`, removes commas, and stores only the final answer string.
- MATH-style examples store a solution string suitable for symbolic/string math scoring.
- Tool-call examples may store JSON strings or structured values expected by the custom reward or tool evaluator.
- Search-style rewards can expect dictionaries with targets rather than plain strings.

When a dataset has `reward_model.style == "rule"`, treat missing `ground_truth` as a schema error unless the specific reward path is known not to need it.

## Custom reward functions

Configure custom reward functions with:

- `custom_reward_function.path`: Python file containing the reward function.
- `custom_reward_function.name`: function name inside that file; leave unset when the file exposes `compute_score` and only one reward is being tested.

The recommended function signature is:

```python
def compute_score(data_source, solution_str, ground_truth, extra_info=None):
    return 1.0
```

Current managers may also pass additional keyword arguments such as reward-model tokenizer, router address, sandbox URL, semaphores, memory limits, rollout scores, or DAPO settings. For robust custom rewards, accept `**kwargs` if the function may be reused across managers:

```python
def compute_score(data_source, solution_str, ground_truth, extra_info=None, **kwargs):
    ...
```

Return a number, boolean, tuple/list whose first item is numeric, or a dictionary containing richer reward information when using managers that collect `reward_extra_info`. Numeric and boolean returns are converted to floats by default dispatch.

## Reward manager notes

- Naive and DAPO reward managers place the scalar reward on the last response token.
- DAPO overlong-buffer penalties require a valid `max_resp_len` when enabled and subtract from the computed score for overlong responses.
- Batch reward managers can call batched scorers with `data_sources`, `solution_strs`, `ground_truths`, and `extra_infos`.
- Experimental reward-loop managers may merge tool extra fields into `extra_info` and can call custom functions with reward-router and reward-model tokenizer context.

## Practical review checklist

Before using a dataset with a reward function:

1. Pick the scorer path: built-in dispatch by `data_source`, custom function, reward model, remote reward, or sandbox-backed code scoring.
2. Verify `ground_truth` has exactly the type and normalization expected by that scorer.
3. Ensure the prompt instruction asks the model to emit the answer format the scorer extracts, such as final answer after `####` for GSM8K.
4. Keep raw answer and raw question in `extra_info` when debugging extraction mismatches.
5. If using custom code, import the reward module in a tiny local smoke test before launching distributed training.
