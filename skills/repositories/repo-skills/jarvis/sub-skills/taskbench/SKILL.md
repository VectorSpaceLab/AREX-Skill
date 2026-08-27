---
name: taskbench
description: "Operate TaskBench benchmark workflows for task automation
  datasets, inference, evaluation, graph tools, and Back-Instruct construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TaskBench sub-skill

Use this sub-skill when a future agent must run, validate, or troubleshoot TaskBench task-automation benchmark workflows in a JARVIS checkout or a compatible TaskBench data directory.

Route elsewhere when the request is about EasyTool benchmark conversion or execution (`easytool`) or HuggingGPT chat/server operation (`hugginggpt-chat`). This sub-skill does not verify local FastChat, vLLM, or other model serving backends; it only describes the OpenAI-compatible endpoint contract that TaskBench clients expect.

## Operating map

- For native command options, safe command shapes, dependency-type routing, and batch evaluation, read [CLI reference](references/cli-reference.md).
- For domain directories, tool graph schemas, data JSONL, user request JSONL, and prediction JSONL shape, read [data formats](references/data-formats.md).
- For metrics, split/tool grouping, prediction and metrics directory naming, and malformed-output recovery, read [evaluation reference](references/evaluation-reference.md).
- For graph generation, graph sampling, visualization, Back-Instruct data generation, and formatting, read [dataset construction](references/dataset-construction.md).
- For endpoint failures, rate limits, resource/temporal asserts, metrics dependencies, visualization paths, and accidental writes, read [troubleshooting](references/troubleshooting.md).

## Skill-owned helpers

Prefer these bundled helpers before running native scripts that write implicitly:

- [scripts/taskbench_graph_tools.py](scripts/taskbench_graph_tools.py) generates, samples, and visualizes graph fixtures using explicit input and output paths.
- [scripts/validate_taskbench_fixture.py](scripts/validate_taskbench_fixture.py) validates TaskBench tool, graph, data, user-request, and prediction fixtures and emits a JSON summary.
- [scripts/batch_evaluate.sh](scripts/batch_evaluate.sh) safely wraps native batch evaluation when the user provides an explicit repository root and existing prediction files.

## Hard routing rules

1. Select `--dependency_type temporal` for Daily Life APIs and any tool library whose tools use request `parameters` instead of `input-type`/`output-type` resources. Selecting `resource` for Daily Life APIs triggers a native assertion.
2. Select `--dependency_type resource` for HuggingFace Tools, Multimedia Tools, and custom tool libraries whose tools declare resource `input-type` and `output-type` lists.
3. Treat inference and Back-Instruct generation as credentialed network workflows. Do not run them by default; require an explicit OpenAI-compatible endpoint, API key or compatible token, model name, and bounded worker/sample counts.
4. Treat native graph and visualization scripts as evidence of behavior, not as safe wrappers. Use the bundled graph helper when an explicit output path is required.
5. Validate predictions before evaluation when model output may be malformed. Use inference reformatting (`--reformat true --reformat_by self` or a formatter model) or regenerate only failed prediction lines.

Source evidence names used while drafting: taskbench/README.md, taskbench/requirements.txt, taskbench/inference.py, taskbench/evaluate.py, taskbench/generate_graph.py, taskbench/graph_sampler.py, taskbench/data_engine.py, taskbench/format_data.py, taskbench/visualize_graph.py, taskbench/batch_evaluate.sh, and the three bundled TaskBench data-domain schema directories.
