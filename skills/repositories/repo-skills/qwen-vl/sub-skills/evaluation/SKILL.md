---
name: evaluation
description: "Operate Qwen-VL official benchmark evaluation, scoring, and data utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Qwen-VL Evaluation Sub-skill

Use this sub-skill when the task is to prepare or run the official Qwen-VL benchmark evaluations, convert benchmark data, score generated answers, or format benchmark submissions.

## Route here for

- Captioning benchmarks: Flickr30K and Nocaps.
- VQA and document/chart/text QA: VQAv2, OKVQA, TextVQA, VizWiz, DocVQA, ChartQA, GQA, OCRVQA, and AI2D.
- Referring-expression grounding: RefCOCO, RefCOCO+, and RefCOCOg.
- Multiple-choice benchmarks: ScienceQA, MMBench, and SEED-Bench.
- Reference-only benchmark workflows: MME and TouchStone.
- CPU-only data conversion or scoring utilities bundled under [scripts/](scripts/).

## Route elsewhere

- For direct ad-hoc multimodal chat, image grounding prompts, model loading, checkpoint choice, or quantization behavior, use [../inference/SKILL.md](../inference/SKILL.md).
- For evaluating a newly trained adapter after a finetuning run, use this sub-skill for benchmark execution but use [../finetuning/SKILL.md](../finetuning/SKILL.md) for training and adapter preparation.
- For web demos or OpenAI-compatible service deployment, use [../serving/SKILL.md](../serving/SKILL.md).

## First actions

1. Identify the benchmark name and split, then open [references/benchmark-reference.md](references/benchmark-reference.md) for the owner script, dataset key, metric, output file, and submission route.
2. Validate the local `data/` layout against [references/data-layouts.md](references/data-layouts.md). Do not assume external datasets, annotations, or model checkpoints are already present.
3. If the workflow runs model inference, confirm CUDA/NCCL availability and launch with the distributed arguments in [references/benchmark-reference.md](references/benchmark-reference.md). These official inference scripts use `device_map='cuda'`, `.cuda()`, `torch.distributed`, and NCCL.
4. If the task is only conversion or scoring, prefer the CPU-capable bundled utilities in [scripts/mmbench/](scripts/mmbench/) or [scripts/infographicsvqa_eval.py](scripts/infographicsvqa_eval.py) when their input files are already available.
5. When model downloads, benchmark downloads, API-judged scoring, or full multi-GPU runs are not approved, report the exact skipped prerequisite and prepare commands/files without executing the expensive step.

## Bundled entry points

- Core Qwen-VL evaluation scripts: [scripts/evaluate_caption.py](scripts/evaluate_caption.py), [scripts/evaluate_vqa.py](scripts/evaluate_vqa.py), [scripts/evaluate_grounding.py](scripts/evaluate_grounding.py), and [scripts/evaluate_multiple_choice.py](scripts/evaluate_multiple_choice.py).
- VQA and ANLS scoring helpers: [scripts/vqa.py](scripts/vqa.py), [scripts/vqa_eval.py](scripts/vqa_eval.py), and [scripts/infographicsvqa_eval.py](scripts/infographicsvqa_eval.py).
- MMBench conversion, scoring, and submission helpers: [scripts/mmbench/](scripts/mmbench/).
- SEED-Bench prompt conversion and multiple-choice inference: [scripts/seed_bench/trans.py](scripts/seed_bench/trans.py) and [scripts/seed_bench/eval.py](scripts/seed_bench/eval.py).

## Safety and limitations

- Do not run a full benchmark unless the user has provided a checkpoint, datasets, model-download approval or cached weights, enough GPU memory, and output destination expectations.
- Do not use MME `get_images.py` from the source repository as-is; this sub-skill documents MME as reference-only because the original helper mutates directories and assumes external hard-coded dataset paths.
- SEED-Bench image conversion is CPU-friendly; video conversion additionally needs video decoding packages and local video assets. See [references/troubleshooting.md](references/troubleshooting.md).
- TouchStone requires an external judge workflow and is documented as methodology/reference-only here.
