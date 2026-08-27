---
name: evaluation
description: "Select, prepare, and interpret ECCV2022-RIFE benchmark and
  evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ECCV2022-RIFE evaluation sub-skill

Use this sub-skill when the task is about RIFE benchmarks, reported evaluation metrics, benchmark dataset layout, throughput smoke checks, or deciding which evaluation case is safe to run.

Natural triggers include: "run RIFE benchmarks", "UCF101 evaluation", "Vimeo90K evaluation", "MiddleBury IE", "ATD12K", "HD benchmark", "HD 4X", "PSNR/SSIM/IE", "testtime smoke", "which benchmark is safe", and "dataset layout".

## Route away

- Image-pair, video, PNG-sequence, `--ratio`, `--exp`, `--fps`, `--scale`, `--fp16`, `--montage`, or output generation questions belong to the interpolation sub-skill.
- Vimeo triplet training, distributed launch, TensorBoard logs, checkpoint production, or reproduction training belongs to the training sub-skill.
- Do not download benchmark datasets or checkpoints automatically. Official metrics require user-provided external assets.

## Core workflow

1. **Classify the request.** Decide whether the user needs benchmark selection, layout validation, command construction, metric interpretation, or verification skip classification.
2. **Gate assets before commands.** Full UCF101, Vimeo90K, MiddleBury, ATD12K, HD, and HD 4X evaluations require external datasets plus checkpoints. The benchmark scripts expect checkpoint directories containing `flownet.pkl`.
3. **Gate backend criticality.**
   - `benchmark/testtime.py` is the only no-dataset/no-checkpoint source benchmark candidate. It times random 480x640 tensor inference and is not an official quality metric.
   - UCF101, Vimeo90K, MiddleBury, and ATD12K use `torch.device("cuda" if available else "cpu")`; CPU is functionally possible but may be slow.
   - `benchmark/HD.py` and `benchmark/HD_multi_4X.py` contain explicit `.cuda()` calls and have **no CPU substitute**. Treat them as required-CUDA cases.
4. **Validate layout safely.** Use the bundled validator before running any source benchmark:

   ```bash
   python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark <name>
   ```

   The validator checks expected source scripts, dataset files, checkpoint files, and HD YUV sizes. It performs no downloads and does not execute benchmarks.
5. **Use benchmark commands only after gates pass.** The command, metric, dataset, checkpoint, dependency, backend, and skip rationale matrix is in [references/benchmarks.md](references/benchmarks.md).
6. **Interpret signals carefully.** PSNR and SSIM are higher-is-better image fidelity metrics; MiddleBury IE is lower-is-better interpolation error; `testtime.py` prints seconds per inference and says nothing about checkpoint quality.
7. **Troubleshoot by symptom.** Use [references/troubleshooting.md](references/troubleshooting.md) for missing files, checkpoint load errors, CUDA-only HD failures, `scikit-image`/YUV issues, slow CPU runs, shape/padding failures, and metric interpretation traps.

## Verification skip decisions

Use these labels consistently when planning final verification:

- **safe smoke candidate:** `benchmark/testtime.py` when repo dependencies are installed and the runtime budget can tolerate 200 random 480x640 inferences. Prefer CUDA for speed; on CPU, mark `SKIP_EXPENSIVE` if the budget is tight.
- **SKIP_DATA:** any full benchmark whose dataset directory or checkpoint file is absent, or whose setup would require network downloads.
- **SKIP_EXPENSIVE:** full dataset benchmarks when assets exist but running all samples is outside the approved time/GPU budget; also use for CPU-only throughput timing if too slow.
- **required-CUDA:** HD and HD 4X benchmarks if CUDA is unavailable, even if CPU imports work.
- **not verified:** never claim README-reported official metrics were reproduced unless the matching dataset, checkpoint, backend, and command were actually run later.
