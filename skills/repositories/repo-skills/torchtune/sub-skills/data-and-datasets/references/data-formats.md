# Data Formats

This reference helps agents choose and configure torchtune dataset builders. The common pipeline is: raw row from `datasets.load_dataset` -> message transform -> model/tokenizer transform -> collator or packed sample.

## Source Selection

- Hugging Face source: set `source` to the dataset repository name and pass `split`, `name`, `data_dir`, or other `load_dataset` kwargs as needed.
- Local JSON/JSONL/CSV source: set `source: json` or `source: csv`, pass `data_files`, and usually set `split: train`.
- Local text source: set `source: text`, pass `data_files`, and use `column: text` unless the loaded table exposes a different text column.
- Remote file source: use the same `source` value as local file loading and pass URL strings in `data_files`; be explicit about `split`.
- Avoid embedding absolute local checkout paths in reusable configs; use project-relative dataset paths or documented user-provided paths.

## Message Rows

`torchtune.data.Message` is the common unit expected by tokenizers and model transforms.

```python
Message(role, content, masked=False, ipython=False, eot=True)
```

Valid roles are `system`, `user`, `assistant`, `ipython`, and `tool`. Text content can be a string; multimodal content is a list such as `[{"type": "image", "content": image}, {"type": "text", "content": prompt}]`. `validate_messages(messages)` rejects conversations that are too short, put a system message after index 0, place an assistant before a user/tool/ipython predecessor, contain consecutive user messages, or put tool/ipython messages after a non-tool-call assistant.

Use `mask_messages(messages, masking_strategy)` with:

- `train_on_all`: train on user and assistant text, except multimodal user messages remain masked.
- `train_on_assistant`: mask all non-assistant messages.
- `train_on_last`: mask everything except the last assistant message.

Many dataset builders expose legacy `train_on_input`; treat `True` as train-on-prompt behavior and `False` as assistant-only behavior. New custom transforms should prefer `masking_strategy` when the transform supports it.

## Instruct SFT

Use `torchtune.datasets.instruct_dataset` when each row has one user prompt and one assistant answer.

Expected raw shape:

```json
{"input": "Question", "output": "Answer"}
```

Config fragment:

```yaml
dataset:
  _component_: torchtune.datasets.instruct_dataset
  source: json
  data_files: data/instruct.jsonl
  split: train
  column_map:
    input: prompt
    output: response
  train_on_input: False
  packed: False
```

Use `InputOutputToMessages` directly in custom builders. If the row includes an image column, include `image` in `column_map` and pass `image_dir` only when image paths are relative to a known dataset directory.

## Alpaca SFT

Use `torchtune.datasets.alpaca_dataset` or `torchtune.data.AlpacaToMessages` for `instruction`/`input`/`output` rows. `input` is optional, but `instruction` and `output` are required in `column_map` when remapping columns. The default masking for `AlpacaToMessages` is train-on-all; override it deliberately if only assistant loss is desired.

## Chat SFT

Use `torchtune.datasets.chat_dataset` for a single conversation column. Choose `conversation_style: sharegpt` for `from`/`value` rows and `conversation_style: openai` for `role`/`content` rows.

ShareGPT row:

```json
{"conversations": [{"from": "human", "value": "Hi"}, {"from": "gpt", "value": "Hello"}]}
```

OpenAI row:

```json
{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]}
```

Config fragment:

```yaml
dataset:
  _component_: torchtune.datasets.chat_dataset
  source: json
  data_files: data/chat.jsonl
  split: train
  conversation_column: messages
  conversation_style: openai
  train_on_input: False
  new_system_prompt: null
```

If raw role names or content keys do not match either style, write a custom `Transform` that returns `{"messages": list[Message]}` and wrap it with `SFTDataset`.

## Preference Data

Use `torchtune.datasets.preference_dataset` for DPO/reward-model data. Each row needs `chosen` and `rejected`, each containing a valid OpenAI-style list of messages with the same prompt context and different assistant response.

```json
{
  "chosen": [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Better"}],
  "rejected": [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Worse"}]
}
```

Config fragment:

```yaml
dataset:
  _component_: torchtune.datasets.preference_dataset
  source: json
  data_files: data/preferences.jsonl
  split: train
  column_map:
    chosen: chosen_conversations
    rejected: rejected_conversations
  train_on_input: False
```

`PreferenceDataset` emits `chosen_input_ids`, `chosen_labels`, `rejected_input_ids`, and `rejected_labels`. Use `padded_collate_dpo`, not the SFT collator, for these batches. Packing is not supported for preference datasets.

## Text Completion

Use `torchtune.datasets.text_completion_dataset` for unstructured text. It encodes a text column directly and emits `tokens` and next-token-shifted `labels`.

```yaml
dataset:
  _component_: torchtune.datasets.text_completion_dataset
  source: text
  data_files: data/corpus.txt
  split: train
  packed: True
  split_across_pack: True
```

For JSON/CSV corpora, set `column` to the text-bearing column. `add_eos` controls whether EOS is appended before label shifting.

## Multimodal Text+Image

Use builders from `torchtune.datasets.multimodal` when rows contain images.

- `multimodal_chat_dataset`: ShareGPT-style conversations plus one image path per sample; supports `image_tag` placement in the text.
- `vqa_dataset`: `input`/`image`/`output` rows via `InputOutputToMessages`.
- `llava_instruct_dataset`: LLaVA-style conversation rows.
- `the_cauldron_dataset`: Cauldron-style `texts` and `images` rows.

Multimodal builders take `model_transform`, not just a text tokenizer, because image preprocessing is model-specific. They expect the model transform to return at least `tokens` and `mask`, and may also return `encoder_input`. Multimodal packing is rejected by the built-in builders.

Example fragment:

```yaml
dataset:
  _component_: torchtune.datasets.multimodal.multimodal_chat_dataset
  source: json
  data_files: data/vlm_chat.jsonl
  split: train
  column_map:
    conversations: dialogue
    image: image_path
  image_tag: "<image>"
  image_dir: data/images
```

When validating local image rows, check that paths resolve relative to `image_dir` and that the prompt has the expected image placeholder when `image_tag` is not `null`.

## Prompt Templates

Prompt templates format `Message` text before or during tokenization. Built-ins in `torchtune.data` include `PromptTemplate`, `ChatMLTemplate`, `GrammarErrorCorrectionTemplate`, `QuestionAnswerTemplate`, and `SummarizeTemplate`; model packages also provide model-specific templates.

Guidelines:

- Keep dataset transforms responsible for row-to-message conversion.
- Keep model/tokenizer transforms responsible for model-specific prompt tags, BOS/EOS, image tokens, and token masks.
- Verify that the tokenizer prompt template matches the target model family; a valid dataset can still train poorly with the wrong chat template.
- Remember that assistant prompt-template tags can be included in loss, while system/user tags are often masked depending on message masks.

## Packing and Concatenation

`PackedDataset(ds, max_seq_len, padding_idx=0, max_packs=None, split_across_pack=False)` greedily packs tokenized samples into fixed-length examples with `tokens`, `labels`, `input_pos`, `seq_lens`, and block-causal attention masks. Builders that support `packed=True` require `tokenizer.max_seq_len` or equivalent model transform length.

Use `split_across_pack=True` for pretraining-style continuous text when splitting long samples is acceptable. Keep it `False` for instruction/chat fine-tuning unless truncation across examples is intended. If a sample is longer than `max_seq_len` and splitting is disabled, increase `max_seq_len`, filter/truncate upstream, or enable splitting.

`ConcatDataset` can combine datasets, but it rejects a mix of packed and non-packed datasets. Ensure all child datasets emit compatible sample keys and use the same collator expectations.

## Collators

- `padded_collate_sft(batch, padding_idx=0, ignore_idx=-100, pad_to_multiple_of=1, stack_on_new_dim=False, cp_degree=1)` pads SFT/text-completion `tokens` and `labels`.
- `padded_collate_dpo(batch, padding_idx=0, ignore_idx=-100)` pads preference `chosen_*` and `rejected_*` keys.
- `padded_collate_packed` is for already packed samples.
- `padded_collate_tiled_images_and_mask` handles tiled multimodal encoder inputs.

Use tokenizer pad IDs for `padding_idx` and `CROSS_ENTROPY_IGNORE_IDX` (`-100`) for label padding unless a recipe explicitly overrides them. Do not use an SFT collator on preference outputs or a DPO collator on SFT outputs.
