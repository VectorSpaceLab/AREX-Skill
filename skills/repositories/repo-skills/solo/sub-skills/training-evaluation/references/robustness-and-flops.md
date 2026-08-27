# Robustness and FLOPs

## Corruption benchmark

`tools/test_robustness.py` evaluates a checkpoint by inserting a `Corrupt`
transform into the test pipeline after image loading. The documented benchmark
contains 15 corruptions:

- noise: `gaussian_noise`, `shot_noise`, `impulse_noise`
- blur: `defocus_blur`, `glass_blur`, `motion_blur`, `zoom_blur`
- weather: `snow`, `frost`, `fog`, `brightness`
- digital: `contrast`, `elastic_transform`, `pixelate`,
  `jpeg_compression`

The implementation also exposes `all`, `benchmark`, `holdout`, `None`, and
individual corruption names including `speckle_noise`, `gaussian_blur`,
`spatter`, and `saturate`. Severity 0 is clean data; severity increases from 1
to 5. The script avoids reevaluating severity 0 for every corruption by
reusing the first clean result.

Use a staged plan:

1. Run ordinary clean evaluation with the same config/checkpoint and save the
   clean metric.
2. Verify the optional `imagecorruptions` dependency and that the configured
   dataset pipeline can load local images of arbitrary expected size.
3. Run one corruption at one severity, then a small group, then the documented
   benchmark set only if the output and metric protocol are correct.
4. Record clean AP, corrupted AP, absolute drop, and relative retained
   performance for each corruption/severity. The documentation calls the
   aggregate corruption measures `P`, `mPC`, and `rPC`; preserve the exact
   final-print and aggregation settings.

The source documentation says the benchmark is single-GPU; the script contains
launcher plumbing but is not a safe promise of multi-GPU robustness support.
`--show` can require a display and is not necessary for metrics. The benchmark
is stochastic, so small variations are expected. Do not compare runs with
changed corruption implementation, severity set, image preprocessing, or
clean baseline.

Failure triage:

- `No module named imagecorruptions` or `robustness_eval`: install the exact
  optional dependency in the approved environment, or stop; do not silently
  substitute a different corruption library.
- Unknown corruption/severity: use the script's choices and integer severities
  0–5; start with documented names.
- Missing `Corrupt` transform or image shape errors: check package version,
  pipeline order, and image dimensions before retrying.
- Missing results sidecar: ensure `--out` is writable and inspect the first
  traceback; the script writes aggregate results beside the output.
- Metric is absent: specify `--eval` and use an evaluator supported by the
  dataset (COCO `bbox`/`segm`, or VOC `bbox` with its IoU protocol).
- A legacy source path for dictionary-shaped outputs contains a fragile
  filename concatenation expression; if it raises a unary-plus `TypeError`,
  preserve the clean result and stop the robustness run rather than mutating
  the source in place. Use a reviewed local patch or the non-dictionary output
  path only with explicit approval.

## Experimental FLOPs and parameter count

`tools/get_flops.py <CONFIG> [--shape ...]` accepts one dimension (square) or
two dimensions (height/width), with default input shape `(3, 1280, 800)`. It
builds the model, moves it to CUDA, switches `forward` to `forward_dummy` when
available, and calls the MMDetection FLOPs counter.

Interpret outputs as estimates, not ground truth:

- FLOPs depend on input shape; parameter count does not.
- Group normalization and custom operators may be omitted or incompletely
  counted depending on the counter/version.
- Two-stage detector FLOPs depend on proposal counts and post-processing.
- A model without `forward_dummy` is unsupported by this utility.
- Custom CUDA ops, DCN, and FP16 settings can change runtime behavior even if
  the displayed count is unchanged.

For a defensible comparison, hold config, input shape, model mode, counter
version, and operator coverage constant. Report units exactly as printed (for
example, `GMac` and `M`) and state missing operators. Do not use a CPU help or
config parse as FLOPs validation: the script requires CUDA model construction.

## Cost and stop policy

Robustness multiplies dataset inference by corruption and severity count.
FLOPs model construction can OOM at large shapes. Stop at the smallest result
that answers the question; bound image count, corruption set, severity set,
shape, and output size before starting. Never download the benchmark, model
weights, or datasets implicitly from a runtime skill.
