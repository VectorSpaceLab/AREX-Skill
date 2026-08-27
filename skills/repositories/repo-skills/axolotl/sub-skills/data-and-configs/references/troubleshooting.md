# Data and Config Troubleshooting

Use this page symptom-first. Start with the bundled structural checker, then use Axolotl preprocessing only when real tokenizer/prompt-strategy behavior is needed.

## YAML Syntax or Shape Fails

Symptoms:

- parser error before Axolotl starts;
- `datasets` is treated as a mapping or string;
- config overrides do not appear to apply.

Fixes:

- Run `python scripts/validate_axolotl_config.py config.yaml`.
- Confirm the YAML root is a mapping, not a list.
- Confirm `datasets` and `pretraining_dataset` are lists when present.
- Quote strings that contain `:` or template delimiters.
- Keep CLI overrides minimal; move important overrides back into YAML for reproducibility.

## Missing Dataset Fields

Symptoms:

- validation says a dataset or pretraining dataset is required;
- loader complains about missing `path`;
- a local file cannot be inferred.

Fixes:

- Add either `datasets:` or `pretraining_dataset:`.
- Add `path` to each dataset entry unless using the built-in `synthetic` dataset.
- Add `type` for prompt strategy selection unless rows are pre-tokenized.
- Add `ds_type: json`, `csv`, `parquet`, or `arrow` when a local loader cannot be inferred.
- For streaming pretraining, include `text_column`, `streaming: true`, and `max_steps`.

## Wrong Dataset Type

Symptoms:

- `type: sharegpt` is rejected;
- assistant labels are missing;
- instruction fields cannot be found;
- completion data is accidentally treated as chat.

Fixes:

- Replace legacy `type: sharegpt` with `type: chat_template`.
- For ShareGPT-style data, set `field_messages: conversations` and map `role: from`, `content: value`.
- For OpenAI-style data, set `field_messages: messages` and map `role: role`, `content: content`.
- For raw text, use `type: completion` rather than `chat_template`.
- For explicit segment masking, use `type: input_output` with `segments`.
- For pre-tokenized rows, leave `type:` empty and verify exact token columns.

## Chat Roles or Label Masking Look Wrong

Symptoms:

- `axolotl preprocess --debug` shows too many `-100` labels;
- user turns are trained unexpectedly;
- assistant turns are ignored;
- `human`/`gpt` source roles do not map as intended;
- EOS/EOT labels differ from expectations.

Fixes:

- Run `python scripts/inspect_chat_dataset.py data.jsonl --field-messages FIELD` to preview roles and keys.
- Set `message_property_mappings` explicitly.
- Set `roles` when source role names are nonstandard.
- Set `roles_to_train` to the canonical roles that should contribute labels, usually `assistant`.
- Inspect `train_on_eos` and `train_on_eot`; valid EOS choices are `all`, `turn`, `last`, and `none`.
- If the tokenizer lacks a default template, set a concrete `chat_template` such as `chatml`, `llama3`, or `gemma`, or provide `chat_template_jinja`.

## Custom Jinja Template Fails

Symptoms:

- validation says `chat_template_jinja` is required;
- rendered prompts omit fields;
- EOT/EOS tokens are inconsistent.

Fixes:

- Set `chat_template: jinja` with `chat_template_jinja`, or set only `chat_template_jinja` and let Axolotl infer jinja mode.
- Confirm the template references fields provided by `message_property_mappings`.
- If the template uses EOT tokens different from the tokenizer EOS token, configure `eot_tokens` and check whether each EOT is a single tokenizer token.
- Route tokenizer-special-token changes to model-loading-and-adapters.

## Preprocess Downloads or Model Access Fails

Symptoms:

- preprocessing needs Hub access;
- tokenizer or model metadata cannot be fetched;
- private dataset access fails.

Fixes:

- Use `axolotl preprocess config.yaml --debug --no-download` when optional model download should be skipped.
- Confirm `base_model`, tokenizer access, and private dataset credentials outside reusable skill content.
- If `pretraining_dataset` or `skip_prepare_dataset` is set, do not use standalone preprocess as the primary check.
- Treat full tokenizer/model errors as runtime environment issues; this sub-skill only covers config/data structure.

## Prepared Dataset Cache Surprise

Symptoms:

- changes to prompt formatting do not show up;
- training appears to reuse old tokenized rows;
- debug output differs from expected edited data.

Fixes:

- Clear or change `dataset_prepared_path` when changing prompt logic, `chat_template_jinja`, or custom format code.
- Leave `dataset_prepared_path` empty for robust example YAMLs that should not accidentally reuse a prior cache.
- Set `dataset_prepared_path` deliberately when repeated interactive runs should reuse a known prepared cache.

## Packing Confusion

Symptoms:

- `sample_packing` is blamed for wrong labels;
- eval packing conflicts with debug tables;
- packed samples appear to cross-attend.

Fixes:

- First debug prompt labels without assuming packing is the cause.
- `sample_packing` improves throughput by packing tokenized sequences; it does not choose the prompt strategy.
- Pair packing with suitable attention/backend settings through distributed-and-performance.
- Set `eval_sample_packing: false` if using features that conflict with packed eval, such as some debug/eval table flows.

## Validation and Test Dataset Conflicts

Symptoms:

- config validation rejects `test_datasets` with `val_set_size`;
- eval behavior is confusing.

Fixes:

- Do not set nonzero `val_set_size` with explicit `test_datasets`.
- Use a held-out split through `split`, `test_datasets`, or validation split logic, not all at once.
- Keep preference-method evaluation decisions in preference-tuning.

## Hard Cases to Test

- Mixed chat role names: rows use `from: human`, `from: assistant`, and a custom `from: bot`, causing assistant labels to disappear unless `roles` and mappings are explicit.
- SFT-to-DPO switch: a config changes from `type: alpaca` JSONL to DPO chat data but keeps old columns, so `rl`, `field_messages`, chosen/rejected fields, and mappings must all change together.
