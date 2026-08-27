# Metrics and Benchmarks

This sub-skill plans Sana evaluation commands without running benchmarks.
Use the bundled planner to render the exact launcher command for the chosen
metric family.

## Metric selection

| Metric family | Planner input | Separate env? | Required data or model cache | Typical output |
| --- | --- | --- | --- | --- |
| FID + CLIP | `fid`, `clip`, or both | No extra metric env, but wandb logging is optional only | MJHQ-30K images and the reference embeddings cache | Local image cache plus FID/CLIP summaries |
| GenEval | `geneval` | Yes: a dedicated GenEval env | GenEval prompt set plus the detector cache | JSONL scores and a text summary |
| DPG-Bench | `dpg` | Yes: a dedicated DPG env | DPG benchmark CSV/metadata and model cache | Per-run text summary and local score file |
| ImageReward | `image-reward` | No extra metric env, but wandb logging is optional only | Benchmark prompt dictionary plus generated images | Per-run text score file |

## Planning checklist

Before planning a metric command, confirm:

1. The checkpoint or checkpoint list exists, or the path is a valid remote model reference.
2. The paired Sana config matches the model family and image resolution.
3. The benchmark data are present locally.
4. The required metric environment is available when the metric needs one.
5. WandB logging is either authenticated or explicitly disabled.

## Benchmark-specific notes

### FID + CLIP
- Uses the same launcher for both metrics.
- MJHQ-30K is the expected image benchmark.
- Reference embeddings are cached locally so repeated runs do not rebuild them.
- Local outputs usually live under the job metrics tree together with cached image-path manifests.
- Turn off `log_fid` or `log_clip_score` when wandb is unavailable.
- Example planner call:
  ```bash
  python scripts/plan_metrics_command.py \
    --metric fid \
    --config configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
    --model-paths output/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
    --sample-nums 30000 --img-size 512 --tracker-project-name sana-baseline
  ```
- Example launcher shape:
  ```bash
  bash scripts/bash_run_inference_metric.sh <config> <checkpoint-or-txt> --sample_nums=30000 --img_size=512
  ```

### GenEval
- Requires a dedicated GenEval environment.
- The wrapper expects the detector cache to be available and can populate it when network access is allowed.
- The benchmark split is prompt-driven; the image directory layout must match the evaluator expectation.
- Keep `sample_nums` aligned with the launcher parallelism. If the requested sample count does not divide evenly, some prompts may be dropped from a naive split.
- Example planner call:
  ```bash
  python scripts/plan_metrics_command.py \
    --metric geneval \
    --config configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
    --model-paths output/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
    --sample-nums 553 --cfg-scale 4.5 --tracker-project-name sana-baseline
  ```
- Example launcher shape:
  ```bash
  bash scripts/bash_run_inference_metric_geneval.sh <config> <checkpoint-or-txt> --sample_nums=553
  ```

### DPG-Bench
- Requires a dedicated DPG environment.
- The launcher is GPU-heavy and assumes a multi-process accelerator run.
- The benchmark uses a CSV/metadata pair and writes a local summary file.
- `bs=1` is the safe choice for DPG planning.
- Example planner call:
  ```bash
  python scripts/plan_metrics_command.py \
    --metric dpg \
    --config configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
    --model-paths output/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
    --sample-nums 1065 --bs 1 --img-size 512
  ```
- Example launcher shape:
  ```bash
  bash scripts/bash_run_inference_metric_dpg.sh <config> <checkpoint-or-txt> --sample_nums=1065 --bs=1
  ```

### ImageReward
- Uses a benchmark prompt dictionary plus generated images.
- `bs=1` is the safe choice.
- The evaluator writes a per-run text score file and can optionally log to wandb.
- Example planner call:
  ```bash
  python scripts/plan_metrics_command.py \
    --metric image-reward \
    --config configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
    --model-paths output/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
    --sample-nums 100 --bs 1
  ```
- Example launcher shape:
  ```bash
  bash scripts/bash_run_inference_metric_imagereward.sh <config> <checkpoint-or-txt> --sample_nums=100 --bs=1
  ```

## WandB caveat

The metric utilities only implement wandb-style online logging. If wandb is not
available or should not be used:

- disable the relevant `log_*` flag, or
- use offline mode only if the environment already supports it and the run does
  not depend on online sync.

Do not assume a different tracker backend is supported by these benchmark wrappers.

## Expected output tree

A typical evaluation run produces a tree like this:

```text
output/<job>/
  checkpoints/
  vis/
  metrics/
    cached_img_paths_<dataset>.txt
    tmp_<dataset>*.txt
    <metric-specific summaries>
```

Metric-specific summaries commonly include:
- `*_geneval_result.txt`
- `*_geneval.jsonl`
- `*_sample*_dpg_results_simple.txt`
- `*_sample*_image_reward.txt`
- FID/CLIP local summary files and cached embeddings

## Safe planner usage

Use the bundled metric planner to select the launcher and render the command.
It never executes the benchmark.

When the planner warns about missing data, envs, or auth, stop at command
planning and fix the preflight issue before any run.

## Provenance labels

- `docs/metrics_toolkit.md`
- `scripts/bash_run_inference_metric*.sh`
- `scripts/inference_*metric*.py`
- `tools/metrics/*`
- `.github/workflows/ci.yaml`
