---
name: language-models
description: "Routes AXLearn GPT-family trainer catalogs, tokenizer variants,
  MoE configs, and flash-attention workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# language-models

Use this sub-skill for AXLearn's decoder-only language-model catalogs and related tokenizer/model-family helpers.

Typical triggers:

- GPT, C4, Pajama, Fuji, Gala, Honeycrisp, Qwen, or MoE model names.
- Long-context, flash-attention, RoPE, ALiBi, or mesh-shape questions in `axlearn.experiments.text.gpt`.
- Tokenizer files such as `bpe_32k.json`, `bpe_128k.json`, `Llama-3-tokenizer.json`, or Fuji v3 vocabulary helpers.
- Queries about `tokamax`, `qwix`, `FlashAttention`, or the model-specific trainer catalogs.

If the user is only asking about the shared trainer runtime, `config_for_function`, or fake-data smoke checks, use `../training-core/` first.
If the user is asking about cloud launch or GCP job execution, use `../cli-cloud/`.

## What to read

- `references/overview.md` for the GPT catalog structure and major model families.
- `references/troubleshooting.md` for optional dependency and tokenizer-path failures.
- `scripts/inspect_gpt_configs.py` for a safe config-inspection helper.

## Families covered

- `c4_trainer` for C4-based training catalogs.
- `fuji`, `gala`, `honeycrisp`, `gspmd`, and `qwen` for model-family builders and trainer variants.
- `deterministic_trainer` and the Pajama configs for dataset-specific catalog variants.
- `vocabulary_fuji_v3` for tokenizer compatibility and Llama-3-style tokenizer files.
- `gala_sigmoid` for sigmoid-attention-related config manipulation.

## Typical workflows

### Inspect exported config names

Use the bundled helper to list the named trainer configs for a module and to inspect one resolved config:

```bash
python scripts/inspect_gpt_configs.py --module axlearn.experiments.text.gpt.gala --config 7B
```

### Understand tokenizer wiring

The GPT helpers read tokenizer files from the configured data directory. When `DATA_DIR=FAKE`, they fall back to the packaged repository data under `axlearn/data/tokenizers/`.

### Route around optional dependencies

Some GPT-family modules pull in extra MoE or flash-attention dependencies at import time. If the import fails, check `references/troubleshooting.md` before assuming the catalog is unavailable.

## Decision points

- Use this sub-skill when the user names a concrete GPT-family architecture or tokenizer file.
- Keep reusable trainer mechanics in `training-core`.
- Do not send vision or ASR questions here just because they also use trainer configs.
