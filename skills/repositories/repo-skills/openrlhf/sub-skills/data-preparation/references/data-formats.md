# OpenRLHF Data Formats

OpenRLHF loads local JSON/JSONL/CSV/Parquet/Arrow files, local `datasets.Dataset.save_to_disk` directories, local dataset scripts, and Hub/ModelScope datasets through the HuggingFace `datasets` loader path. The training CLIs then map columns into mode-specific dataset classes.

## Common Loading and Mixing

- `--data.dataset` accepts one dataset path/name or a comma-separated list.
- `--eval.dataset` uses the same loading conventions for evaluation data where supported.
- `--data.dataset_split` defaults to `train`; evaluation split defaults vary by CLI.
- `--data.max_samples` caps rows after loading.
- `--data.dataset_probs` is a comma-separated float list used for interleaving multiple datasets; its length must equal the comma-separated dataset count.
- Dataset paths may include `dataset@data_dir`; OpenRLHF splits on `@` and passes the right side as `data_dir`.

## SFT Records

SFT uses `openrlhf.datasets.sft_dataset.SFTDataset` through `openrlhf.cli.train_sft`.

Default keys and relevant flags:

- `--data.input_key input`: prompt, text, or chat trajectory field.
- `--data.output_key None`: assistant response field for prompt/response SFT.
- `--data.input_template 'User: {}\nAssistant: '`: string template for non-chat prompt records; ignored in pretrain mode and typically not used with chat templates.
- `--data.apply_chat_template`: use the tokenizer chat template.
- `--data.tokenizer_chat_template`: override tokenizer chat template text.
- `--data.multiturn`: compacted multiturn loss over assistant messages; requires `--data.apply_chat_template`.
- `--data.max_len 2048`: tokenized prompt + response limit.

Plain prompt/response shape:

```json
{"question": "Explain RLHF in one sentence.", "response": "RLHF aligns model behavior using preference or reward feedback."}
```

Typical flags:

```bash
--data.input_key question --data.output_key response --data.input_template $'User: {}\nAssistant: '
```

Chat-template prompt/response shape can use strings or message lists. If `output_key` is set and chat templates are enabled, OpenRLHF templates the prompt with `add_generation_prompt=True`, templates prompt plus response, and slices the response suffix.

```json
{"messages": [{"role": "user", "content": "Summarize this."}], "answer": [{"role": "assistant", "content": "Short summary."}]}
```

Multiturn SFT shape places the whole trajectory in `input_key` and should not use `output_key`:

```json
{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}, {"role": "user", "content": "Name one use."}, {"role": "assistant", "content": "Preference tuning."}]}
```

In multiturn mode, OpenRLHF computes loss ranges for every assistant message. Records with missing prompt/response text or prompt token length `>= max_len - 2` are filtered out.

## Reward Model Records

Reward model training uses `openrlhf.datasets.reward_dataset.RewardDataset` with `is_dpo=False` through `openrlhf.cli.train_rm`.

Default keys and flags:

- `--data.prompt_key None`: optional shared prompt or chat prefix.
- `--data.chosen_key chosen`: preferred completion or preferred chat continuation.
- `--data.rejected_key rejected`: rejected completion or rejected chat continuation.
- `--data.input_template None`: optional string template applied only when `prompt_key` is set and chat templates are disabled.
- `--data.apply_chat_template`: use tokenizer chat templates.
- `--data.max_len 512`: tokenized chosen/rejected sequence length.
- Optional `margin`: numeric margin used by reward loss when present and non-null; defaults to `0` otherwise.

Pair-only shape:

```json
{"chosen": "The helpful answer.", "rejected": "The unsafe or lower-quality answer.", "margin": 0.5}
```

Prompted shape:

```json
{"prompt": "What is 2+2?", "chosen": "4", "rejected": "5"}
```

With chat templates and `prompt_key`, `prompt`, `chosen`, and `rejected` are expected to be chat-message lists that can be concatenated before template application.

## DPO Records

DPO uses the same `RewardDataset` preprocessing with `is_dpo=True` through `openrlhf.cli.train_dpo`.

Default keys and flags:

- `--data.prompt_key None`
- `--data.chosen_key chosen`
- `--data.rejected_key rejected`
- `--data.input_template None`
- `--data.apply_chat_template`
- `--data.max_len 512`

When `prompt_key` is set, OpenRLHF treats the prompt as the shared prefix and chosen/rejected as completions. When no `prompt_key` is set and chat templates are enabled, DPO derives the prompt from `chosen[:-1]` and slices both chosen and rejected after that prompt; this means chosen and rejected must be comparable chat trajectories with the same preceding conversation.

Recommended explicit-prompt shape:

```json
{"prompt": [{"role": "user", "content": "Pick a safe answer."}], "chosen": [{"role": "assistant", "content": "Safe answer."}], "rejected": [{"role": "assistant", "content": "Unsafe answer."}]}
```

For string data without chat templates:

```json
{"prompt": "Question: 2+2\nAnswer:", "chosen": " 4", "rejected": " 5"}
```

DPO filters samples whose prompt token length is `>= max_len - 2`, so long prompts can silently reduce usable data.

## PPO and RL Prompt Records

PPO/RL prompt data uses `openrlhf.datasets.prompts_dataset.PromptDataset` through `openrlhf.cli.train_ppo_ray`.

Relevant flags:

- `--data.prompt_dataset`: prompt dataset path/name for PPO/RL training.
- `--data.prompt_split train`: split for prompt data.
- `--data.input_key input`: prompt field.
- `--data.label_key None`: optional label field for reinforced fine-tuning/reward functions.
- `--data.input_template None`: string template when not applying chat templates.
- `--data.apply_chat_template`: use tokenizer chat template with `add_generation_prompt=True`.
- `--data.image_key images`: image references for VLM prompts.
- `--data.max_images_per_prompt 0`: text-only unless greater than zero.
- Optional `datasource`: preserved and returned by the prompt dataset; defaults to `default`.

Text prompt shape:

```json
{"prompt": "Solve: 3*7", "label": "21", "datasource": "math"}
```

Chat prompt shape:

```json
{"context_messages": [{"role": "user", "content": "Solve: 3*7"}], "datasource": "math"}
```

With `--data.apply_chat_template`, a string prompt is wrapped as a single user message. A message-list prompt is deep-copied and each string `content` containing `<image>` is converted to multimodal content entries.

## VLM Image Prompts

OpenRLHF VLM prompt preprocessing recognizes literal `<image>` tags in prompt text or message content. The prompt dataset stores `data[image_key]` alongside the prompt. Later VLM utilities load image references as local paths, URLs, base64 strings, raw bytes, or PIL objects.

Example JSONL record:

```json
{"prompt": "<image>What object is highlighted?", "images": ["relative/or/accessible/image.png"], "datasource": "vlm"}
```

Important constraints:

- `--data.max_images_per_prompt > 0` activates VLM constraints in PPO/RL training.
- VLM training does not support a critic model and does not support `--ds.packing_samples` because packing breaks image-token and pixel-value alignment.
- The number of `<image>` placeholders should match the number of non-null image references for each record.
- If image references are present but none load successfully, OpenRLHF raises instead of silently falling back to text-only processing.

## Chat Template Implications

- Do not pass already-rendered chat strings with `--data.apply_chat_template`; pass role/content messages or plain user strings.
- Do not combine `--data.input_template` and `--data.apply_chat_template` for the same formatting purpose.
- SFT and reward/DPO slice response/completion text by rendering prompt and prompt-plus-response; malformed role order can produce empty or unexpected response slices.
- For VLM, `<image>` inside string content becomes structured content (`{"type": "image"}` plus text chunks) before chat-template rendering.
