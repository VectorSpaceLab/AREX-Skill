# Installation and Backend Notes

## Purpose

Read this before installing DataFlow or choosing a backend for a workflow. It summarizes the verified package surface, public install commands, optional extras, and the backend stance used while constructing this skill.

## Verified package facts

- Distribution name: `open-dataflow`
- Import package: `dataflow`
- Console script: `dataflow`
- Verified version: `1.0.10`
- Supported Python range in package metadata: `>=3.7, <4`
- CLI entry point: `dataflow.cli:app`

## Public install options

Use one of these depending on your context:

```bash
python -m pip install -e .
```

or

```bash
python -m pip install open-dataflow
```

After installing, run:

```bash
python -m pip check
python -m dataflow.cli --help
python scripts/check_dataflow_env.py
```

## Optional extras by workflow family

Install only the extras that match the workflow you are using.

| Extra | Typical use |
| --- | --- |
| `ray` | RayOrch acceleration and distributed operator execution |
| `audio` | speech-related operators and pipelines |
| `rag` | LightRAG / retrieval-oriented workflows |
| `litellm` | LiteLLM-backed serving |
| `sglang` | SGLang local serving |
| `eval` | vLLM-based evaluation workflows |
| `vllm`, `vllm07`, `vllm08` | local LLM serving and model-backed training/eval paths |
| `mineru`, `pdf2vqa`, `pdf2model`, `pdf2model-dataflex`, `flash-mineru` | PDF / OCR / VQA / document-prep workflows |
| `test` | repo test extras, not needed for normal runtime use |

## Backend stance for this skill

- The generated skill is organized so that **CPU** is the required final verification backend for the selected scope.
- A **CUDA-capable** environment is useful as an optional smoke path because the host supports NVIDIA GPUs and the package exposes CUDA-aware serving paths.
- Do not treat a CPU import as proof of GPU-only behavior. Keep optional GPU, OCR, local model serving, and Ray workflows clearly separated in the sub-skills that own them.

## What to install for each major route

- `pipeline-foundations`: base install only; optional `pyvis` if you want graph rendering.
- `serving-cli`: base install for help and import checks; add backend-specific extras only for the serving class you actually use.
- `text-workflows`: base install for CPU filters and offline fixture work; add model-serving extras only for API/model-backed stages.
- `document-vision-rag`: base install plus OCR / retrieval / VQA extras only when the selected workflow truly needs them.
- `rayorch-acceleration`: base install plus `ray` / `rayorch` when you want a real acceleration smoke.

## Safe smoke checks

- `python scripts/check_dataflow_env.py`
- `python scripts/inspect_dataflow_surface.py`
- `python -m dataflow.cli --help`
- `python -m dataflow.cli init --help`

## Common installation signals

- `ModuleNotFoundError: dataflow` — install the package or activate the correct environment.
- `ImportError` for serving backends — the selected workflow probably needs an optional extra or a local runtime binary.
- `dataflow env` failure in pipes or CI — use the bundled diagnostic script instead of the built-in command.
