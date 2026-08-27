# Evaluation and Metrics Troubleshooting

## Purpose

Use this when a metric, statistic-precompute command, or translation-eval run fails.

## Common failures

### Distributed evaluation rejects the metric

**Symptoms**
- The multi-GPU helper refuses the selected metric.

**Likely causes**
- The distributed path supports only a subset of metrics.

**Recovery**
- Fall back to the single-process evaluation helper.
- Restrict the distributed claim to the metrics explicitly supported by the repo's docs and tests.

### FID needs real-image statistics

**Symptoms**
- FID evaluation cannot find an inception pickle file.
- The script tries to recompute stats and takes much longer than expected.

**Likely causes**
- The real-image statistics were never precomputed.
- The dataset path or subset does not match the evaluation config.

**Recovery**
- Run `tools/utils/inception_stat.py` first with the correct dataset or image directory.
- Reuse the cached pickle in the metric config.

### Inception-stat extraction fails on the stylegan branch

**Symptoms**
- The metric helper asks for a script module path or a GPU runtime.

**Likely causes**
- The StyleGAN-style Inception path is being used instead of the default PyTorch path.

**Recovery**
- Use the default PyTorch Inception path for a simpler inspection run.
- If you truly need the StyleGAN path, prepare the cached script module and the GPU runtime.

### Translation evaluation uses the wrong domain

**Symptoms**
- The output is scored against the wrong images or looks like the source domain.

**Likely causes**
- `--target-domain` was omitted or pointed at a domain that does not exist in the model.

**Recovery**
- Confirm the model's domain names before running the helper.
- Compare with the translation dataset layout in `references/data-formats.md`.

### `translation_eval.py --eval none` crashes

**Symptoms**
- The helper enters the no-metric path and then raises an attribute error.

**Likely causes**
- The script currently references `args.num_samples` even though the CLI does not define that argument.

**Recovery**
- Do not rely on that no-metric path without patching the helper.
- Use the main evaluation driver or a sampling helper when you only need saved images.

### Metric outputs are not what the caller expects

**Symptoms**
- The result is a scalar in one path and a dict in another.

**Likely causes**
- Different metrics return different shapes and summary structures.

**Recovery**
- Inspect the metric class signature and the helper path before asserting on the result.
- Use the tests under `tests/test_cores/test_metrics.py` as the source of truth.

## When to escalate

Stop and ask for a narrower scope or a different backend when the fix requires:

- A missing GPU.
- A cached external asset that cannot be downloaded.
- A metric path that is intentionally unsupported in distributed mode.
