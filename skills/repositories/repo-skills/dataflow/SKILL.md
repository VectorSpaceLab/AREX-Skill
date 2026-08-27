---
name: dataflow
description: "Route DataFlow workflows for pipelines, text and document
  processing, serving, evaluation, and Ray acceleration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DataFlow

Use this repo skill for `open-dataflow` / `dataflow` tasks that prepare data, build pipelines, launch serving backends, run evaluations, or wrap operators with RayOrch.

## First reads

- `references/repo-provenance.md` — source commit, package version, evidence paths, and refresh baseline.
- `references/installation-and-backends.md` — install commands, verified import checks, and backend selection.
- `references/api-overview.md` — verified public surface for the most important classes, CLIs, and serving helpers.
- `references/troubleshooting.md` — cross-cutting install/import, key-mismatch, TTY, and backend failure guidance.
- `references/repo-routing-metadata.json` — routing metadata used by the managed repo-skill router.

## Fast start

1. Install the package for local inspection or use the published distribution:
   - `python -m pip install -e .`
   - or `python -m pip install open-dataflow`
2. Run a safe environment smoke check:
   - `python scripts/check_dataflow_env.py`
3. Inspect the public API surface when you need signatures or command names:
   - `python scripts/inspect_dataflow_surface.py`
4. Read the focused sub-skill that matches the task family below.

## Route map

### [pipeline-foundations](sub-skills/pipeline-foundations/SKILL.md)
Use for operator, pipeline, storage, prompt, wrapper, and compile-time key-validation work.

Typical requests:
- create or debug a `PipelineABC`, `BatchedPipelineABC`, or `StreamBatchedPipelineABC`
- choose between `FileStorage`, `LazyFileStorage`, `DummyStorage`, batch storage, or MyScale storage
- fix `input_*` / `output_*` mismatches or `Key Matching Error`
- validate `prompt_restrict`, `PromptABC`, `DIYPromptABC`, or `draw_graph`

### [serving-cli](sub-skills/serving-cli/SKILL.md)
Use for CLI routing, `dataflow init`, `chat`, `eval`, `pdf2model`, `text2model`, `webui`, and serving class setup.

Typical requests:
- inspect command groups and help output
- choose an API, local, or hosted serving backend
- understand credential, timeout, or WebUI side effects
- diagnose missing optional serving dependencies

### [text-workflows](sub-skills/text-workflows/SKILL.md)
Use for text cleaning, filtering, reasoning, code, conversation, Text2SQL, prompt-driven generation, translation, and text2model prep.

Typical requests:
- adapt CPU-safe text filters or prompt-driven generators
- map columns such as `raw_content`, `instruction`, `problem`, `generated_code`, or `golden_answer`
- prepare offline text fixtures or text2model inputs
- separate API-backed stages from pure local filtering

### [document-vision-rag](sub-skills/document-vision-rag/SKILL.md)
Use for PDF/OCR, visual QA, knowledge-base cleaning, LightRAG, Agentic RAG, speech, chemistry, and `pdf2model` planning.

Typical requests:
- validate document inputs before OCR or retrieval
- choose between KBC, PDF VQA, or document-prep flows
- reason about MinerU, FlashMinerU, DataFlex, LlamaFactory, and audio extras
- diagnose missing documents, suffixes, or hardware/credential limits

### [rayorch-acceleration](sub-skills/rayorch-acceleration/SKILL.md)
Use for RayOrch wrapping, actor cleanup, and pipeline acceleration without changing the surrounding pipeline contract.

Typical requests:
- wrap an existing operator with `RayAcceleratedOperator`
- preserve order and storage behavior through CPU or GPU execution
- decide when to use `replicas`, `num_gpus_per_replica`, or `env`
- debug shutdown or optional Ray dependency issues

## How to choose

- If the task is mainly about **how DataFlow operators and pipeline storage work**, start with `pipeline-foundations`.
- If the task is mainly about **CLI commands, serving, or launch-time dependencies**, start with `serving-cli`.
- If the task is mainly about **text or tabular dataset transformation**, start with `text-workflows`.
- If the task is mainly about **documents, PDFs, OCR, RAG, or pdf2model**, start with `document-vision-rag`.
- If the task is mainly about **distributed acceleration of an existing operator**, start with `rayorch-acceleration`.
- If the request spans multiple families, use the root references first, then hand off to the narrowest sub-skill that owns the final action.

## What this root skill does not do

- It does not execute training, downloads, or backend-heavy workflows by default.
- It does not rely on the original checkout after generation; bundled references and scripts carry the reusable guidance.
- It does not replace the focused sub-skills when the request is already narrow.

## When to revisit provenance

Read `references/repo-provenance.md` before deciding whether this skill is stale for a checkout of DataFlow or before running a refresh workflow.
