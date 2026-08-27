# Data and Reward Troubleshooting

## `apply_chat_template` fails or rows are filtered out

Likely cause: `prompt` is a string, empty list, or malformed message object. verl expects a chat-template-compatible list of messages under the configured prompt key.

Fix:

- Convert plain prompts to `[ {"role": "user", "content": prompt_text} ]`.
- Ensure every message has string `role` and a `content` value.
- For structured content, use content parts with `type` plus `text`, `image`, `video`, or `audio` keys.
- Run `scripts/validate_verl_parquet.py` and inspect `prompt` failures before tokenization.

## Missing `reward_model.ground_truth`

Likely cause: preprocessing copied the raw dataset answer to another field or omitted reward metadata.

Fix:

- Add `reward_model: {"style": "rule", "ground_truth": extracted_answer}` for rule-based rewards.
- For GSM8K, extract the value after `####` and remove commas to match the default scorer.
- Keep raw answer in `extra_info.answer` if the extraction rule needs auditability.

## Reward is always zero despite valid generations

Likely cause: answer format and scorer extraction do not agree.

Fix:

- Align prompt instruction with reward extraction, for example ask for final answer after `####` when using GSM8K scorer.
- Compare one decoded `solution_str` against `ground_truth` using the intended reward function outside training.
- Confirm the stored `ground_truth` is normalized as the scorer expects: string, number-like string, boxed math answer, JSON string, or target dictionary.

## `NotImplementedError: Reward function is not implemented`

Likely cause: `data_source` is not recognized by default dispatch.

Fix:

- Use a supported built-in `data_source` only when its scorer semantics truly match the dataset.
- Otherwise provide `custom_reward_function.path` and optionally `custom_reward_function.name`.
- Keep `data_source` stable and descriptive because it is used in metrics and reward routing.

## Custom reward import or call fails

Likely cause: the configured file path/name is wrong or the function signature is too narrow.

Fix:

- Ensure the Python file exists on the training workers and exposes the configured function.
- Use `compute_score` as the function name when leaving `custom_reward_function.name` unset.
- Prefer `def compute_score(data_source, solution_str, ground_truth, extra_info=None, **kwargs): ...` for compatibility with reward managers that pass extra context.
- Return a numeric-compatible value or a dictionary accepted by the selected manager.

## Multimodal placeholder mismatch

Likely cause: prompt content contains `<image>`, `<video>`, or `<audio>` but the corresponding modality column is missing or the counts differ.

Fix:

- Add `images`, `videos`, or `audios` columns with the same number of entries as placeholders.
- Use structured content parts directly when the processor expects them.
- Do not rely on raw modality columns being present after dataset item access; verl converts them into `raw_prompt` and removes original modality columns from returned samples.

## Tool or agent data misses per-sample settings

Likely cause: tool settings were stored outside `extra_info`.

Fix:

- Put `tools_kwargs`, `interaction_kwargs`, and `need_tools_kwargs` inside `extra_info`.
- Ensure `extra_info.index` is stable for debugging warnings and rollouts.
