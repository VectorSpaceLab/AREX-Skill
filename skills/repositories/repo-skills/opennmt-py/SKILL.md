---
name: opennmt-py
description: "Routes OpenNMT-py workflows for data preparation, training,
  inference, server deployment, and checkpoint/model conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenNMT-py

Use this skill for OpenNMT-py tasks that involve corpus preparation, vocabulary building, training, translation, REST serving, checkpoint maintenance, or model conversion.

## Install

For a local checkout, prefer an editable install:

```bash
python -m pip install -e .
```

For a published install:

```bash
python -m pip install "OpenNMT-py==3.5.1"
```

Core runtime facts:
- Python 3.9+
- PyTorch 2.1 to <2.3
- The package expects `torch`, `ctranslate2`, `pyonmttok`, and `pyyaml` to be present.
- Optional workflows add `sentencepiece`, `safetensors`, `pandas`, `gradio`, and `bitsandbytes`.

Minimal smoke check:

```bash
python -c "import onmt, torch; print('onmt_import=ok'); print(torch.__version__, torch.cuda.is_available())"
```

If you need CUDA paths, read `references/compatibility.md` and run `scripts/check_cuda.py`.

## Route map

- `sub-skills/data-preparation/` — build vocabularies, validate corpus YAML, apply transforms, handle source features, and debug data layout issues.
- `sub-skills/training/` — train seq2seq or language models, inspect model configs, handle multi-GPU, embeddings, alignment, LoRA, and checkpointing.
- `sub-skills/inference/` — translate, score, align, run the REST server, and use CTranslate2 or LLM-style inference configs.
- `sub-skills/conversion/` — convert external checkpoints, upgrade old checkpoints, extract or merge weights, and release models.

## Start here

1. Read `references/repo-provenance.md` to check whether this skill still matches the current checkout.
2. Read `references/cli-reference.md` for the main console commands.
3. Read the owning sub-skill for the workflow you want to run.

## Common entry points

- Build vocabulary: `onmt_build_vocab`
- Train: `onmt_train`
- Translate: `onmt_translate`
- Serve: `onmt_server`
- Average models: `onmt_average_models`
- Release models: `onmt_release_model`

## When to read the bundled references

- `references/workflows.md` for a quick route overview and the standard quickstart sequence.
- `references/compatibility.md` for backend, Python, and optional-dependency notes.
- `references/troubleshooting.md` for install, import, CUDA, config, and runtime failures.
