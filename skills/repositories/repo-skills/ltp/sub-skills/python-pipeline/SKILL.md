---
name: python-pipeline
description: "Guides high-level Python LTP pipeline workflows for model loading,
  sentence splitting, task outputs, custom words, and integration helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Python Pipeline

Use this sub-skill when the user wants to use `from ltp import LTP, StnSplit` for Chinese NLP inference, output conversion, or service integration.

## Choose this route when

- The task names `LTP(...)`, `pipeline`, `LTPOutput`, `StnSplit`, `LTP/tiny`, `LTP/small`, `LTP/base`, `LTP/legacy`, or local LTP model directories.
- The user asks for CWS, POS, NER, SRL, dependency parsing, SDP, SDPG, custom words, or GPU movement from Python.
- The user needs to interpret output structures or convert LTP output into a tabular/CoNLL-U-like format.
- The user wants to wrap LTP behind a Python service or batch-processing script.

Route low-level perceptron model/trainer APIs to [../legacy-extension/SKILL.md](../legacy-extension/SKILL.md), deep-training/config tasks to [../training-and-data/SKILL.md](../training-and-data/SKILL.md), and Rust/C bindings to [../rust-bindings/SKILL.md](../rust-bindings/SKILL.md).

## Minimal safe workflow

1. Confirm the package imports and optional CUDA state from the root skill:

   ```bash
   python ../../scripts/check_ltp_install.py --json
   ```

2. For no-network diagnostics, run the pipeline smoke script without loading a model:

   ```bash
   python scripts/ltp_pipeline_smoke.py --skip-model-load
   ```

3. If the user has a local or cached model, load it explicitly:

   ```bash
   python scripts/ltp_pipeline_smoke.py --model-path /path/to/ltp-model --local-files-only --tasks cws,pos,ner
   ```

4. For real application code, use a model id or local path and choose tasks deliberately:

   ```python
   from ltp import LTP

   ltp = LTP("LTP/small")
   output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
   print(output.cws, output.pos, output.ner)
   ```

## Read these references

- [references/api-reference.md](references/api-reference.md) for verified signatures, task dependencies, `LTPOutput`, and method behavior.
- [references/workflows.md](references/workflows.md) for common inference, custom-word, pretokenized-input, batch, and CUDA workflows.
- [references/model-loading-and-outputs.md](references/model-loading-and-outputs.md) for model ids, offline loading, output shapes, labels, and conversion decisions.
- [references/service-and-integration.md](references/service-and-integration.md) for CoNLL-U conversion, FastAPI-style wrappers, and production safety notes.
- [references/troubleshooting.md](references/troubleshooting.md) when model loading, task selection, CUDA, or optional service dependencies fail.

## Bundled helpers

- [scripts/ltp_pipeline_smoke.py](scripts/ltp_pipeline_smoke.py) checks imports/sentence splitting and optionally runs a tiny pipeline against a supplied model path or model id. Defaults avoid network downloads.
- [scripts/convert_ltp_output_to_conllu.py](scripts/convert_ltp_output_to_conllu.py) converts saved LTP JSON output into CoNLL-U-like rows without loading a model.

## Important boundaries

- Do not run remote model downloads unless the user has accepted network/model-cache side effects.
- Do not claim legacy `LTP("LTP/legacy")` supports SRL/DEP/SDP/SDPG. It supports CWS/POS/NER only.
- Do not pass raw strings when `cws` is omitted from `tasks`; pass pretokenized `List[List[str]]`.
- Do not hide private Hugging Face tokens, proxies, or model paths in scripts or committed configs.
