# Axolotl Configuration Workflow

Axolotl runs are config-driven: a single YAML file describes the model, dataset source and prompt strategy, output locations, adapter/full-tune choice, training hyperparameters, and optional distributed/runtime features. Treat the YAML as the source of truth and use CLI overrides only for deliberate experiment changes.

## Minimal Config Skeleton

A practical SFT-style config has these sections:

```yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
adapter: lora

datasets:
  - path: data/train.jsonl
    type: chat_template
    field_messages: messages

output_dir: ./outputs/run-name
sequence_len: 2048
micro_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 0.0002
num_epochs: 1
```

Key rules:

- `base_model` identifies the model/tokenizer family; model-specific quirks belong in the model-loading/adapters sub-skill.
- At least one of `datasets` or `pretraining_dataset` is required.
- `datasets` is a list, even for one dataset.
- Every dataset entry normally needs `path`; most SFT entries also need `type` unless the data is already tokenized.
- Axolotl validation requires at least two of `micro_batch_size`, `gradient_accumulation_steps`, and `batch_size`.
- Keep `output_dir` and `dataset_prepared_path` project-relative or user-chosen; do not bake local machine paths into reusable examples.

## Dataset Sections

Use `datasets` for SFT-style, non-streaming pretraining with `type: completion`, preference datasets, and pre-tokenized rows. Use `pretraining_dataset` for streaming pretraining corpora:

```yaml
pretraining_dataset:
  - path: HuggingFaceFW/fineweb-edu
    type: pretrain
    text_column: text
    split: train
streaming: true
max_steps: 1000
```

When using `pretraining_dataset`, `axolotl preprocess` is not the right validation command; run training-time preprocessing checks through the pretraining workflow instead. Streaming pretraining needs `max_steps` because Axolotl cannot infer full dataset length.

## Schema and Installed Docs

Use these commands when an Axolotl installation is available:

- `axolotl config-schema` dumps the installed Pydantic schema for config keys.
- `axolotl agent-docs` shows agent-optimized docs bundled with the installed package.
- `axolotl agent-docs grpo`, `axolotl agent-docs sft`, and similar topic commands can clarify route-specific options.

The upstream config model is centered on `AxolotlInputConfig`; nested dataset config classes include SFT, pretraining, DPO, KTO, stepwise-supervised, and synthetic dataset shapes. Schema checks can change across Axolotl releases, so prefer the installed CLI over copied examples when exact field availability matters.

## Safe Structural Validation

Before invoking Axolotl, run the bundled lightweight checker:

```bash
python scripts/validate_axolotl_config.py config.yaml
```

It verifies YAML parsing, top-level object shape, `datasets`/`pretraining_dataset` presence, common dataset list mistakes, chat-template mapping shape, sample-packing warnings, and known conflicts such as `test_datasets` with nonzero `val_set_size`. It intentionally does not import Axolotl, load tokenizers, download datasets, or validate every schema field.

## Preprocess and Debug Flow

Use `axolotl preprocess config.yaml --debug` when the real tokenizer and Axolotl prompt strategy must materialize rows. The debug output is the best handoff for:

- label masking surprises, especially `-100` tokens;
- `chat_template` role or EOS/EOT handling;
- custom `chat_template_jinja` behavior;
- `input_output` segment concatenation;
- dataset cache and prepared-path issues.

Notes:

- If `dataset_prepared_path` is omitted, Axolotl warns and uses its default prepared-data path for preprocessing.
- If `dataset_prepared_path` is explicitly set, Axolotl may reuse prepared data when the dependent hash matches.
- Prompt-template code changes and user-defined formatting may not invalidate an existing prepared cache; clear or change the prepared path when checking new formatting.
- The preprocess command may need tokenizer/model access; use `--no-download` when the CLI should avoid its optional model-download behavior.
- `skip_prepare_dataset` and `pretraining_dataset` are signals that standalone preprocessing is not needed.

## CLI Overrides and Strictness

Axolotl CLI commands expose many config fields as overrides. Use overrides sparingly because they can hide the true run definition from the YAML. If a config uses strict override behavior, unknown or unintended override keys should be treated as failures rather than silent edits. When debugging a repro, put important values back into YAML and rerun structural validation.

## Packing and Validation Handoffs

`sample_packing` changes how examples are batched, not the raw prompt strategy. Important config-level interactions:

- `sample_packing: true` commonly pairs with `pad_to_sequence_len: true`.
- `eval_table_size` is incompatible with `eval_sample_packing` unless eval sample packing is disabled.
- If train packing and eval packing differ, Axolotl may need `remove_unused_columns: false`.
- Some attention backends do not isolate packed samples safely; route backend/performance decisions to distributed-and-performance.

Use this sub-skill to identify the config-level risk, then hand off backend-specific choices.
