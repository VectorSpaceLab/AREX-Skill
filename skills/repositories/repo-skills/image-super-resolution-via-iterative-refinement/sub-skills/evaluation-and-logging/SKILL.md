---
name: evaluation-and-logging
description: "Guide PSNR/SSIM result-pair evaluation and TensorBoard/W&B logging
  for the SR3/DDPM super-resolution repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and logging

Use this sub-skill when a task is about evaluating generated super-resolution outputs, interpreting PSNR/SSIM numbers, or enabling/diagnosing TensorBoard and Weights & Biases logging for this repository.

## Route by intent

- **Evaluate completed SR outputs:** read [metrics-and-logging.md](references/metrics-and-logging.md#result-pair-evaluation) and use [evaluate_result_pairs.py](scripts/evaluate_result_pairs.py) on a directory containing final `*_hr.png` and `*_sr.png` images.
- **Explain metric semantics:** read [metrics-and-logging.md](references/metrics-and-logging.md#metric-semantics) before comparing scores across runs.
- **Find the right output files:** read [metrics-and-logging.md](references/metrics-and-logging.md#output-file-contracts) for how `sr.py`, `infer.py`, and `sample.py` name images.
- **Set up experiment logging:** read [metrics-and-logging.md](references/metrics-and-logging.md#tensorboard-and-wb-logging) for TensorBoard, W&B flags, tables, checkpoint artifacts, and supported scripts.
- **Debug missing pairs, shape errors, or W&B failures:** read [troubleshooting.md](references/troubleshooting.md).

## Operating boundaries

- Result-pair PSNR/SSIM requires ground-truth HR images; unconditional samples without matching HR files are not valid for this evaluator.
- The bundled evaluator is self-contained and does not import repository modules, so it can be used on copied result folders.
- Training, inference, checkpoint acquisition, and dataset preparation are owned by other sub-skills; this sub-skill only interprets and checks the outputs and logging behavior they produce.
