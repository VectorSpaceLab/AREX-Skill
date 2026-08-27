---
name: data-and-configs
description: "Guides agents to write, inspect, and debug Axolotl YAML configs,
  dataset formats, chat_template mappings, preprocessing, and config-schema
  issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Configs

Use this sub-skill when an agent needs to write an Axolotl config YAML, choose or fix a dataset `type`, debug `chat_template` labels, inspect dataset columns, run `axolotl preprocess --debug`, or reason about `axolotl config-schema` output.

## Fast Routing

- For YAML structure, required sections, preprocessing cache behavior, and config-schema workflows, use [configuration.md](references/configuration.md).
- For `datasets`, `pretraining_dataset`, `chat_template`, `alpaca`, `input_output`, `completion`, pre-tokenized, and preference-data shape choices, use [data-formats.md](references/data-formats.md).
- For common errors and symptom-driven fixes, use [troubleshooting.md](references/troubleshooting.md).
- To preview a local JSON/JSONL chat dataset and infer `field_messages` plus `message_property_mappings`, run `python scripts/inspect_chat_dataset.py data.jsonl` using [inspect_chat_dataset.py](scripts/inspect_chat_dataset.py).
- To run a safe structural YAML check without importing Axolotl, run `python scripts/validate_axolotl_config.py config.yaml` using [validate_axolotl_config.py](scripts/validate_axolotl_config.py).

## Workflow

1. Classify the training/data family first: SFT-style `datasets`, streaming `pretraining_dataset`, preference data with `rl`, or fully pre-tokenized rows.
2. Map the raw columns to an Axolotl prompt strategy before editing hyperparameters; most data bugs come from `type`, `field_messages`, `message_property_mappings`, `roles_to_train`, or masking fields.
3. Use the bundled scripts for local structural checks only; they do not load models, tokenizers, remote datasets, or the Axolotl package.
4. Use `axolotl config-schema` or `axolotl agent-docs` for installed-package schema details when available.
5. Use `axolotl preprocess config.yaml --debug` when tokenized samples, labels, EOS/EOT handling, or sample packing must be confirmed with the real tokenizer and prompt strategy.

## Boundaries

This sub-skill covers config shape, dataset loading fields, prompt strategy selection, preprocessing/debug handoffs, and schema-level validation. Route actual SFT/pretraining execution, preference-method tuning, GRPO/EBFT rewards, model/tokenizer/adapter quirks, distributed launch/performance, and broad CLI operations to the root skill router or the matching sibling sub-skill.
