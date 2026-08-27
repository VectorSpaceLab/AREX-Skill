---
name: evaluation-and-projects
description: "Plan InternLM-XComposer benchmark workflows and related project
  package usage without executing downloads, judge calls, services, or long
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation And Projects

Use this sub-skill when the task is to plan, audit, or troubleshoot benchmark and related-project workflows for the InternLM-XComposer repository family without reopening the source checkout. It is intentionally non-executing: it preserves benchmark data layouts, command shapes, result files, submission expectations, and project-package routing, but it does not download benchmark data, launch models, call GPT/OpenAI judges, start services, or run long inference.

## Route First

- Use this sub-skill for benchmark plans, dataset-layout checklists, result/submission file expectations, ShareGPT4V or DualFocus evaluation/converter planning, and benchmark troubleshooting.
- Route actual model loading, image/video chat, caption generation, quantized inference, or Gradio/LMDeploy usage to sibling `model-inference` unless the request only asks for a non-executing ShareGPT4V/ShareCaptioner plan.
- Route OmniLive audio/base/memory inference, online demo services, model layout checks, and live audio/video interaction to sibling `omnilive`. Keep only OmniLive benchmark planning here.
- Route supervised fine-tuning or adapter merging to sibling `finetuning`. This sub-skill may mention ShareGPT4V installation and data layout, but not operate a training run.
- Route IXC-2.5-Reward scoring, ranking, reward training, and reward benchmarks to sibling `reward-model`.
- If the user asks to execute a benchmark, first convert the request into a plan and explicitly ask for the needed external data, credentials, GPU/Slurm budget, and execution approval before any separate execution-oriented skill acts.

## Required Inputs To Collect

Before producing a plan, identify:

1. Model family or project package: current XComposer/VLMEvalKit, legacy 1.0/2.0 scripts, OmniLive, ShareGPT4V, or DualFocus.
2. Benchmark or utility target: for example MME, MMBench, SEED, QBench, MMMU, MM-Vet, POPE, ChartQA, AI2D, MLVU, Video-MME, StreamingBench, MVBench, ShareGPT4V converter, or DualFocus converter.
3. Intended action: plan only, layout audit, result conversion, submission packaging, or troubleshooting.
4. Local resources: CUDA GPU count, Slurm availability, model/checkpoint path, dataset root, output root, and whether external judge/server submission is allowed.
5. Blocking constraints: benchmark license/data access, GPT/OpenAI judge key, leaderboard account, large download budget, flash-attn/decord/Swift/ffmpeg dependencies, or model-weight license.

## Operating Procedure

1. Open `references/benchmark-workflows.md` for benchmark routing and data/result expectations.
2. Open `references/related-projects.md` for ShareGPT4V and DualFocus installation, package routing, evaluation families, Captioner usage, and Slurm/local distinctions.
3. Open `references/data-conversion.md` when the task involves JSONL, TSV, XLSX, answer-upload, or result-converter formats.
4. Open `references/troubleshooting.md` when a plan is blocked by missing data, CUDA/Slurm, GPT judges, submission servers, output shape errors, or hardcoded source-era paths.
5. Optionally run the bundled safe planner to render a checklist without executing any benchmark:

```bash
python scripts/render_benchmark_plan.py --list
python scripts/render_benchmark_plan.py --workflow xcomposer2-mme --model-path <model> --data-root <data> --output-root <outputs> --gpus 1
python scripts/render_benchmark_plan.py --workflow sharegpt4v-eval --checkpoint share4v-7b --gpus 8 --format markdown
python scripts/render_benchmark_plan.py --workflow omnilive-video-mme --data-root <video-root> --gpus 8 --check-paths
```

The helper uses only Python's standard library, prints commands/checklists as text, and performs optional path-existence probes only when `--check-paths` is supplied.

## Non-Execution Boundaries

- Do not download benchmark datasets, model weights, playground archives, or official eval tools from this sub-skill.
- Do not call OpenAI/GPT judges for LLaVA-Bench, MM-Vet, MathVista answer extraction, or any other judged workflow.
- Do not submit to OpenCompass, EvalAI, QBench, SEED, or other external servers.
- Do not launch ShareGPT4V Gradio demos, OmniLive SRS/FastAPI/Gradio services, or long CUDA inference.
- Do not assume source checkout scripts are present. When a workflow came from source-era scripts or notebooks, use the distilled layout, command shape, result shape, and blockers recorded in the bundled references.

## Output Expectations

A good response from this sub-skill names the chosen workflow, required data layout, GPU/Slurm and package requirements, non-executing command pattern, expected local result files, external submission/judge requirements, known blockers, and the sibling sub-skill to use if the user actually wants inference, service deployment, fine-tuning, or reward modeling.
