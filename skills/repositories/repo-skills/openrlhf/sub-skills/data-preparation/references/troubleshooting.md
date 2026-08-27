# Data Preparation Troubleshooting

## Missing Keys

Symptom: preprocessing crashes with a key error, or the validator reports `missing key`.

Fixes:

- Confirm the mode-specific key flags match the dataset columns.
- For SFT, use `--data.input_key` and, for prompt/response data, `--data.output_key`.
- For reward/DPO, use `--data.prompt_key`, `--data.chosen_key`, and `--data.rejected_key`; do not use top-level `--chosen_key` spelling in new commands.
- For PPO/RL prompts, use `--data.input_key`, optional `--data.label_key`, and optional `--data.image_key`.

## Null or Empty Values

Symptom: SFT samples disappear, response slices are empty, or validator reports null/empty fields.

Fixes:

- Remove rows where required prompt/completion/preference values are null or empty.
- For SFT, remember OpenRLHF filters non-pretrain samples when prompt or response is empty.
- For reward/DPO, keep both chosen and rejected populated; identical chosen/rejected pairs are usually data bugs.

## Prompt and Template Mismatch

Symptom: rendered prompts contain duplicated `User:`/`Assistant:` markers, or responses are sliced incorrectly.

Fixes:

- Use `--data.input_template` only for plain string prompts.
- Use `--data.apply_chat_template` only for strings that should become one user message or for role/content message lists.
- Do not feed already-rendered model-specific chat text into `--data.apply_chat_template`.
- If overriding `--data.tokenizer_chat_template`, validate with a few manual tokenizer renders before training.

## Chosen and Rejected Format Confusion

Symptom: DPO or RM treats the whole conversation as completion, or prompt lengths differ between chosen and rejected.

Fixes:

- Prefer explicit `--data.prompt_key` for DPO and reward data when possible.
- With chat templates and no `prompt_key` in DPO, make `chosen` and `rejected` full comparable trajectories sharing the same prefix and differing in the final assistant answer.
- With `prompt_key`, keep `chosen` and `rejected` as continuations, not full duplicate prompts, unless the code path expects chat-message concatenation.

## Dataset Probability Mismatch

Symptom: startup assertion fails while blending datasets.

Fixes:

- Count comma-separated entries in `--data.dataset` or `--data.prompt_dataset`.
- Count comma-separated floats in `--data.dataset_probs` or prompt-prob equivalents.
- Ensure the counts match exactly; OpenRLHF asserts this before interleaving.

## Max Length Truncation and Filtering

Symptom: SFT/DPO data count is much smaller than expected, or completions lose EOS behavior.

Fixes:

- SFT filters non-pretrain samples when prompt token length is `>= --data.max_len - 2`.
- DPO filters samples when prompt token length is `>= --data.max_len - 2`.
- Reward and DPO append EOS and force the final token to EOS after tokenization, but overlong records can still truncate useful content.
- Use the validator `--max-len-chars` as a rough early warning, then verify exact token lengths with the target tokenizer when available.

## Chat Template Misuse in Multiturn SFT

Symptom: assertion says chat template must be enabled, or assistant turns receive no loss.

Fixes:

- Set `--data.multiturn --data.apply_chat_template` together.
- Put the full role/content trajectory in `--data.input_key`.
- Do not set a separate `--data.output_key` for normal compacted multiturn records.
- Ensure at least one message has `role: assistant`.

## Multimodal Image Mismatches

Symptom: VLM processing raises about failed image loading, placeholder tokens remain without pixel values, or vLLM image alignment fails.

Fixes:

- Count `<image>` tags in the prompt or message content and compare them with non-null entries in `--data.image_key`.
- Keep image references accessible from the training workers: local paths, URLs, base64 strings, raw bytes, or PIL objects are supported by OpenRLHF utilities.
- If references are present but all fail to load, OpenRLHF raises instead of treating the sample as text-only.
- Do not combine VLM training with `--ds.packing_samples`; OpenRLHF asserts against packing when `--data.max_images_per_prompt > 0` because packing breaks image-token/pixel-value alignment.

## Packing and Ring Attention Surprises

Symptom: CLI forces or asserts `--ds.packing_samples`, or warns about flash attention.

Fixes:

- SFT/RM/DPO require packing when ring attention is enabled.
- PPO/RL may auto-enable packing for ring attention or dynamic batching, but VLM PPO forbids packing.
- If packing is enabled, use a flash-attention implementation as recommended by the CLI warnings.
