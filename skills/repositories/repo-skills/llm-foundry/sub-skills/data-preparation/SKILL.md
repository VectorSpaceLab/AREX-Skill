---
name: data-preparation
description: "Prepare LLM Foundry pretraining, fine-tuning, raw-text,
  Delta/Databricks, and contrastive-pair data safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo-skill: llm-foundry
  coverage: data-preparation
license: Apache 2.0
---

# LLM Foundry data preparation

Use this sub-skill when the user needs to create, validate, inspect, or troubleshoot data for LLM Foundry pretraining, supervised fine-tuning, raw text conversion, Delta/Databricks export, StreamingDataset/MDS consumption, or contrastive-pair dataloaders.

## Route first

- **Data conversion and schemas:** read [references/data-formats.md](references/data-formats.md).
- **End-to-end prep recipes:** read [references/workflows.md](references/workflows.md).
- **Exact public CLI/API options:** read [references/cli-reference.md](references/cli-reference.md).
- **Errors, validation, and credentials:** read [references/troubleshooting.md](references/troubleshooting.md).
- **Safe local probe:** run `python scripts/llmfoundry_data_prep_smoke.py --help` from any directory, then use `--fixture PATH` for local JSONL/schema checks.

## Scope and boundaries

This sub-skill covers:

- Public `llmfoundry data_prep` commands: `convert_dataset_hf`, `convert_dataset_json`, `convert_finetuning_dataset`, `convert_text_to_mds`, and `convert_delta_to_json`.
- MDS/StreamingDataset split layouts, `remote`/`local`/`split`/`streams` cache fields, `max_seq_len`, tokenizer/concat choices, safe type handling, and split/cache validation.
- Pretraining text JSON/JSONL, local JSON, supervised fine-tuning prompt/response and chat schemas, target loss policies, raw text folders, Delta-export JSONL, and contrastive-pair formats.
- Data-prep API facts for `StreamingTextDataset`, `StreamingFinetuningDataset`, `build_text_dataloader`, `build_finetuning_dataloader`, and `convert_*_from_args` wrappers.

Route elsewhere:

- Training YAML launch details, optimizers, schedulers, callbacks, and checkpointing → `training-finetuning`.
- ICL/evaluation task datasets and Eval Gauntlet schemas → `evaluation`.
- Model registries, model internals, tokenizer registry extension, and package-wide API details → `package-apis-configuration`.

## Safe operating defaults

1. Prefer local schema validation before conversion. Use the bundled smoke script to inspect imports/signatures and to validate JSONL keys without downloading models or datasets.
2. Treat Hugging Face dataset loads, tokenizer loads, remote object stores, and Databricks queries as network/credential operations. Ask before running them unless the user explicitly authorized them.
3. Keep generated MDS outputs isolated by split, e.g. `out_root/train/index.json` plus shard files. Do not overwrite non-empty output folders; choose a new output root or clean intentionally.
4. Keep `allow_unsafe_types: false` for MDS reading unless the user understands that Pickle-like shard types can execute code during deserialization.
5. For supervised fine-tuning, default decoder-only target policy is `target_prompts: none`, `target_responses: last`; for encoder-decoder it must remain `none`/`last`.

## Provenance

This sub-skill distills public CLI definitions, data module signatures, data-prep README behavior, installed package facts, and data/tokenizer tests. Runtime instructions are self-contained; no source checkout, review artifact, or local path is required after this skill is loaded.
