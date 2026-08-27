# Dataset and Prompt Format Guide

Start from the raw data shape, then choose the Axolotl dataset entry. Do not pick a `type` based only on the training method name; choose it from columns, message structure, and masking needs.

## Quick Choice Table

| Data shape | Config pattern | Main checks |
| --- | --- | --- |
| OpenAI-style messages list | `type: chat_template` | `field_messages`, role/content mappings, `chat_template`, `roles_to_train` |
| ShareGPT-style `conversations` with `from`/`value` | `type: chat_template` | migrate from deprecated `sharegpt`, set mappings |
| Instruction rows | `type: alpaca` or related instruct type | required instruction/output fields or custom type dict |
| Raw text corpus, non-streaming | `type: completion` | text field, `sequence_len`, split behavior |
| Raw text corpus, streaming | `pretraining_dataset` with `type: pretrain` | `streaming: true`, `max_steps`, `text_column` |
| Segment-level custom masking | `type: input_output` | `segments` list of `{text, label}` |
| Pre-tokenized rows | empty `type:` | exact `input_ids`, `attention_mask`, `labels` columns |
| DPO/IPO/ORPO-like preference rows | `rl` plus preference dataset fields | route method choice to preference-tuning |
| KTO rows | `rl: kto` plus prompt/completion/label fields | route method choice to preference-tuning |
| Stepwise supervised reasoning rows | stepwise supervised dataset fields | `prompt`, `completions`, `labels` |

## Chat Template Datasets

Canonical modern chat config:

```yaml
chat_template: llama3
datasets:
  - path: data/chat.jsonl
    type: chat_template
    field_messages: messages
    message_property_mappings:
      role: role
      content: content
    roles_to_train:
      - assistant
```

For ShareGPT-like rows:

```yaml
chat_template: chatml
datasets:
  - path: data/sharegpt.jsonl
    type: chat_template
    field_messages: conversations
    message_property_mappings:
      role: from
      content: value
```

Important behavior:

- Legacy `type: sharegpt` is rejected; migrate it to `type: chat_template`.
- If a dataset entry has `type: chat_template` but no dataset-level `chat_template`, Axolotl defaults that dataset entry to `tokenizer_default` while a root `chat_template` may still override tokenizer behavior globally.
- If `chat_template_jinja` is set without `chat_template`, Axolotl treats the template mode as `jinja`.
- If `chat_template: jinja` is set, `chat_template_jinja` is required.
- Default role normalization maps `human` and `user` to `user`, `gpt` and `assistant` to `assistant`, `system` to `system`, and `tool` to `tool`.
- `message_field_training` can mark whole turns trainable or not; `message_field_training_detail` can mark character spans inside a message.
- `train_on_eos` accepts `all`, `turn`, `last`, or `none`; `train_on_eot` follows similar turn-boundary intent when EOT tokens are configured.

Use `python scripts/inspect_chat_dataset.py data.jsonl` to infer candidate `field_messages` and mappings from local JSON/JSONL rows before editing YAML.

## Instruction and Custom Prompt Types

Instruction-style formats include `alpaca`, `gpteacher`, `oasst`, `reflection`, `alpaca_chat`, and other prompt strategy names. For rows that do not match a built-in type, a dataset `type` can be a mapping:

```yaml
datasets:
  - path: data/custom.jsonl
    type:
      system_prompt: ""
      field_system: system
      field_instruction: input
      field_output: output
      format: "[INST] {instruction} [/INST]"
      no_input_format: "[INST] {instruction} [/INST]"
```

Use this when the data is instruction-like but column names or prompt formatting are custom. If the raw data is truly conversational, prefer `chat_template` instead of forcing it through an instruction template.

## Template-Free `input_output`

Use `type: input_output` when each row explicitly lists prompt segments and which segments should contribute labels:

```json
{"segments":[{"label":false,"text":"<s>User prompt\n"},{"label":true,"text":"Assistant answer</s>"}]}
```

Axolotl concatenates segment text as-is. The data author is responsible for BOS/EOS, spacing, newlines, and special tokens. With `train_on_inputs: false`, `label: false` segments receive ignored labels (`-100`); `label: true` segments are trained.

## Completion and Pretraining

For non-streaming raw text corpora:

```yaml
datasets:
  - path: data/corpus.jsonl
    type: completion
    field: text
```

For streaming pretraining:

```yaml
pretraining_dataset:
  - path: org/corpus
    type: pretrain
    text_column: text
    split: train
streaming: true
max_steps: 1000
```

`completion` pre-tokenizes the dataset before training and can split long text by `sequence_len`. `pretraining_dataset` is for large streaming corpora and should be validated through the pretraining/training flow rather than standalone preprocess.

## Pre-Tokenized Rows

For fully pre-tokenized data, leave `type:` empty and provide exactly these columns:

```json
{"input_ids":[271,299,99],"attention_mask":[1,1,1],"labels":[271,-100,99]}
```

The data must already contain BOS/EOS as intended. Labels set to `-100` are ignored by the loss. Do not rely on Axolotl to add template tokens for this path.

## Preference Dataset Shapes

For DPO/IPO/ORPO-style paired preferences, the data generally needs a prompt plus chosen/rejected completions or chat-message equivalents. For KTO, rows need a prompt/completion plus a binary label. This sub-skill can check that the dataset entry is list-shaped and fields are named consistently, but route loss choice, reference-model behavior, and method-specific hyperparameters to preference-tuning.

## Dataset Loading Fields

Common loader fields mirror Hugging Face `datasets.load_dataset` concepts:

```yaml
datasets:
  - path: org/dataset-or-local-file
    name: optional_config_name
    data_files:
      - train.jsonl
    split: train
    revision: main
    trust_remote_code: false
    ds_type: json
```

Use `ds_type` for local files or directories when Axolotl cannot infer the loader from an extension. Local JSON, CSV, Parquet, and Arrow files are common. Remote filesystems and private Hub datasets may need credentials or `hf_use_auth_token`; do not embed credentials in reusable configs.

## Mixed Datasets

Axolotl accepts multiple entries under `datasets`. Keep each entry explicit about its prompt type and fields. Mixed SFT formats are possible, but mixing SFT, preference, and pretraining objectives in one YAML is usually a routing error unless a specific Axolotl workflow documents it.
