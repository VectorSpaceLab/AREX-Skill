# Data Troubleshooting

Use this matrix when a torchtune dataset config validates syntactically but fails while loading, transforming, packing, collating, or producing useful loss.

## Invalid Message Roles or Order

Symptoms:

- `KeyError` in `ShareGPTToMessages` for a role such as `bot`, `assistant`, or `human_user`.
- `ValueError` from `validate_messages` about assistant before user, two consecutive user messages, system message after index 0, or short conversations.
- Tool or `ipython` messages fail ordering checks.

Fixes:

- For ShareGPT, convert raw roles to `system`, `human`, and `gpt` before using `conversation_style: sharegpt`.
- For OpenAI, use `role` values `system`, `user`, `assistant`, `tool`, or `ipython`.
- Keep a system prompt only as the first message; use `new_system_prompt` when replacing inconsistent system prompts.
- Ensure each trainable chat sample has at least one user/assistant turn.
- For tool-call traces, mark assistant tool-call messages with `ipython=True` only when constructing `Message` objects directly, and use `eot=False` around tool returns.
- Run `scripts/validate_messages_jsonl.py` with `--shape conversations` or `--shape messages` to get line-specific failures before training.

## Bad `column_map`

Symptoms:

- Builder errors such as expected key `input`, `output`, `chosen`, `rejected`, `messages`, or `conversations` in `column_map`.
- Dataset loads but each sample raises `KeyError` for a renamed raw column.
- Image config errors about `image_dir` requiring an `image` key.

Fixes:

- Remember `column_map` maps torchtune expected keys to raw dataset keys, for example `{"input": "prompt", "output": "response"}`.
- For `chat_dataset`, use `conversation_column` instead of a general `column_map`.
- For `preference_dataset`, map only `chosen` and `rejected` unless using a custom transform.
- For multimodal `InputOutputToMessages`, include `image` in `column_map` whenever `image_dir` is set.
- Inspect one raw row with a local JSONL viewer or a tiny `datasets.load_dataset(...)[0]` probe before writing the final config.

## Masking Strategy Confusion

Symptoms:

- Labels are all `-100`, or loss is unexpectedly low/zero.
- User prompt tokens are included in loss when they should not be.
- Alpaca samples train on prompts unexpectedly.
- Multimodal user messages do not contribute to loss even with train-on-all behavior.

Fixes:

- Prefer `masking_strategy` for custom transforms: `train_on_assistant` for assistant-only SFT, `train_on_all` for prompt+answer training, and `train_on_last` for last-turn-only training.
- Treat legacy builder `train_on_input=False` as assistant-only masking and `train_on_input=True` as prompt+assistant masking.
- Note that `AlpacaToMessages` defaults to `train_on_all`; override when assistant-only loss is desired.
- Note that multimodal user messages are always masked by torchtune masking logic.
- Print or assert a tiny tokenized sample's `labels` before launching a long run.

## Missing or Misplaced Images

Symptoms:

- File-not-found errors while loading a multimodal sample.
- Image special token appears in text but no image is loaded, or an image is prepended when the prompt expected an inline placeholder.
- VLM model transform raises on missing `encoder_input` or image tensor shape.

Fixes:

- For local image paths, set `image_dir` to the dataset image root and keep row image values relative to that root.
- For `multimodal_chat_dataset`, set `image_tag` to the exact placeholder in the text. If `image_tag` is `None`, the image is prepended to the first user message.
- Use only one image path per sample with `multimodal_chat_dataset`; use a custom transform for multi-image rows.
- Validate paths with `scripts/validate_messages_jsonl.py --image-key image --image-root <root> --check-image-paths`.
- Pair multimodal datasets with a VLM `model_transform`, not a text-only tokenizer.

## Packed Dataset Sequence Length

Symptoms:

- `PackedDataset requires a max_seq_len to be set on the tokenizer.`
- `Dataset sample is too long` when packing.
- `ConcatDataset can't process a mix of packed and non-packed datasets.`
- Multimodal builder rejects `packed=True`.

Fixes:

- Set `tokenizer.max_seq_len` or the model transform equivalent before `packed=True`.
- Use `split_across_pack=True` for text completion or other continuous corpora where splitting samples is acceptable.
- Keep `split_across_pack=False` for instruction/chat SFT unless splitting examples across packs is intentional.
- Do not mix packed and unpacked children in `ConcatDataset`.
- Do not request packing for built-in multimodal builders or preference datasets.

## Local vs Hugging Face Source

Symptoms:

- `load_dataset` cannot find a local file.
- `split` errors differ between local file and HF repository loading.
- A JSONL file is treated as an unexpected field layout.

Fixes:

- Use `source: json` with `data_files` for local `.json` or `.jsonl` rows; use `source: csv` for CSV; use `source: text` for line-oriented text.
- Use a dataset repository name only when loading from Hugging Face.
- Set `split: train` for local files unless intentionally using a named split mapping.
- Pass Hugging Face loader kwargs such as `name`, `data_dir`, or `data_files` through the dataset config, not inside the tokenizer config.

## Tokenizer or Model Transform Mismatch

Symptoms:

- `model_transform returned ... Must return 'tokens' and 'mask'`.
- Chat prompts decode with the wrong role tags.
- Image rows produce text tokens but no image encoder inputs.
- Labels are shifted correctly but the model loss does not match expected assistant spans.

Fixes:

- Text-only SFT builders can receive a model tokenizer because tokenizers implement message tokenization.
- Multimodal builders require a model transform that performs both tokenization and image preprocessing.
- Choose prompt templates from the target model family; do not apply a generic ChatML template to a tokenizer that expects model-specific tags unless that model supports it.
- If using `AlpacaToMessages`, avoid stacking another Alpaca prompt template in the tokenizer.
- Cross-check tokenizer/model transform setup with [models-and-modules](../../models-and-modules/SKILL.md).

## Collator Padding and Ignore Index

Symptoms:

- Dataloader raises missing `tokens`/`labels` or missing `chosen_*` keys.
- Label padding contributes to loss.
- Left padding with `pad_to_multiple_of` fails.
- Packed samples are padded twice.

Fixes:

- Use `padded_collate_sft` for SFT and text-completion samples with `tokens` and `labels`.
- Use `padded_collate_dpo` for preference samples.
- Use `padded_collate_packed` for packed samples.
- Use tokenizer pad ID for input padding and `CROSS_ENTROPY_IGNORE_IDX` (`-100`) for label padding.
- Do not left-pad with `pad_to_multiple_of > 1`; use right padding for multiple-of padding.

## Tiny Debug Recipe

Before launching a full run, create or inspect one tiny local JSONL row, run the bundled validator, then instantiate the dataset through `tune validate` or a minimal Python probe that only loads the first sample. Avoid downloading large HF datasets or starting training while debugging schema and masking.

Recommended hard cases for verification:

- Mixed chat JSONL with one malformed role and one missing local image path; the validator should report exact line numbers and suggested fixes.
- Preference JSONL where `chosen` and `rejected` have mismatched prompt turns or unexpected prompt masking; the agent should identify whether the issue is schema, masking, or collator selection.
