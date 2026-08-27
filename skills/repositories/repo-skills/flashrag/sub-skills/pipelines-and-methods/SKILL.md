---
name: pipelines-and-methods
description: "Plan and implement FlashRAG end-to-end RAG pipelines, quick-start
  demos, method reproductions, active/reasoning/branching/multimodal pipelines,
  multi-turn prompts, and experiment-runner dry-runs without executing large
  models by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlashRAG Pipelines and Methods

Use this sub-skill when the task is about choosing or wiring FlashRAG pipelines, adapting quick-start demos, reproducing supported methods, planning multi-turn or multimodal workflows, or dry-checking an experiment configuration before any large model/index execution.

## Route first

- For standard text RAG, start with `SequentialPipeline` or `naive_run`; see [pipeline API](references/pipeline-api.md) and [quick-start/multi-turn](references/quick-start-and-multiturn.md).
- For method reproduction, map the requested method name to the experiment-runner recipe and prerequisites; see [method recipes](references/method-recipes.md).
- For active, branching, adaptive, or reasoning RAG, select the pipeline by required control flow and model support; see [pipeline API](references/pipeline-api.md) and [multimodal/reasoning](references/multimodal-and-reasoning.md).
- For multimodal RAG, check dataset modality, prompt template, multimodal retriever settings, generator capability, and hardware before running; see [multimodal/reasoning](references/multimodal-and-reasoning.md).
- Before execution, run the bundled safe checker: `python skills/flashrag/sub-skills/pipelines-and-methods/scripts/validate_pipeline_config.py --config CONFIG.yaml --method METHOD --dry-run-plan`.
- If a run fails or looks wrong, triage with [troubleshooting](references/troubleshooting.md).

## Safety defaults

- Do not execute model downloads, index building, vLLM server/model loading, or full benchmark runs unless explicitly requested.
- Prefer `test_sample_num`, small `retrieval_topk`, short `generation_params`, and `do_eval=False` for smoke tests.
- Treat model paths, corpus paths, index paths, cache paths, and output paths as user-provided runtime values; do not hard-code machine-specific paths in public instructions.
- Keep low-level config schema details, index construction, generator/refiner internals, and metric/UI work in their dedicated FlashRAG skill areas.
