---
name: inference
description: "Routes OpenNMT-py translation, decoding, inference-engine, server,
  and benchmark/evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this sub-skill when an OpenNMT-py task is about producing translations, scoring outputs, running the REST server, or choosing between PyTorch and CTranslate2 inference paths.

## Use this route when

- The request mentions `onmt_translate`, decoding options, alignments, score output, beam traces, or batch inference.
- The task is about `onmt_server`, a server `model_config` file, REST endpoints, tokenizer setup, preprocess/postprocess hooks, or model cloning/unloading.
- The user wants to run OpenNMT-py inference engines, CTranslate2 releases, or LLM-style benchmark/evaluation wrappers that consume released checkpoints.

## Do not use this route when

- The main task is building vocabularies or preparing corpora; use `../data-preparation/`.
- The main task is architecture choice, training schedules, or checkpoint continuation; use `../training/`.
- The main task is averaging, releasing, or converting checkpoints; use `../conversion/`.

## Start here

1. Read `references/translation-and-serving.md` for the command, config, endpoint, engine, and evaluation contracts.
2. Run the bundled server-config validator before starting a server:

   ```bash
   python scripts/validate_server_config.py --config MODEL_CONFIG.json --root MODEL_ASSET_ROOT
   ```

   Add `--no-check-files` when reviewing a template that intentionally omits model/tokenizer files.
3. For a normal decode run, prefer the packaged CLI:

   ```bash
   onmt_translate --model MODEL.pt --src src.txt --output pred.txt
   ```

4. If the job uses a REST server, keep the `model_config` file self-contained and make model/tokenizer paths resolvable from the working directory used to launch `onmt_server`.

## What this sub-skill owns

- Decoding options such as beam search, sampling, `n_best`, `replace_unk`, alignment output, debugging flags, and batch sizing.
- Inference-engine selection and runtime behavior for PyTorch and CTranslate2 releases.
- REST server startup, model cloning, unloading, CPU/GPU migration, and model configuration files.
- Translation debugging, tokenizer setup, preprocess/postprocess hooks, and score/alignment troubleshooting.
- Benchmark-style prompt generation or perplexity scoring that evaluates released models rather than training them.

## Bundled helper

`scripts/validate_server_config.py` is a self-contained JSON validator. It checks the top-level server shape, model entries, model roots, tokenizer shape, optional CT2 fields, timeout fields, and path existence without importing the source checkout.

## Troubleshooting entry point

If the request fails before any actual translation output is produced, read `references/troubleshooting.md` first. Most failures are server-config shape issues, missing model paths, tokenizer model paths, incompatible release formats, alignment option conflicts, or attempts to use a GPU-only path without the required backend.
