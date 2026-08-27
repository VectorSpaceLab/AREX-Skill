# Cross-cutting troubleshooting

Use this page to classify a failure before changing a config or rerunning a
large operation.

## Import and environment

- If `config`, `dataset`, or a trainer import fails, print the active Python
  executable/version and compare it with the selected requirements. The root is
  not packaged; run from the checkout root or set an explicit import path.
- If `mamba_ssm`, `causal_conv1d`, or `timm` is absent, PhysMamba is blocked.
  Do not change its device to CPU and claim equivalent coverage. Compare the
  PyTorch/CUDA/driver/extension/compiler tuple and rerun a tiny backend smoke.
- If OpenCV cannot open media or a Haar cascade, verify the resource is readable
  and resolved explicitly; do not trust a source-relative path when running
  outside the repository root.

## YAML and dispatch

- Unknown YAML keys, wrong nesting, and case mismatches are YACS errors. Start
  from a nearby config and use the setup route's read-only validator.
- Use exact mode, dataset, model, and method tokens. The source has explicit
  dispatch branches and raises rather than falling back.
- `only_test` needs a readable `INFERENCE.MODEL_PATH`. A training model output
  directory is not a checkpoint.

## Cache and labels

- A missing cache with `DO_PREPROCESS: false` is a data-preparation decision,
  not a reason to create an empty directory. Either point to a matching cache
  or explicitly preprocess raw data.
- A missing CSV may be reconstructed only when raw identifiers and cached input
  names remain discoverable. Relocated caches should use a deliberate custom
  `input_files` CSV and a read-only pair validator.
- Check the input/label temporal length, `DATA_FORMAT`, label type, frame rate,
  and preprocessing identity together. Do not interpret metrics from invalid,
  constant, empty, or too-short signals.

## Outputs and permissions

- Relative cache, checkpoint, plot, and log paths resolve from the process
  working directory. Inspect the printed frozen config and derived output path.
- Do not overwrite raw data, checkpoints, or known-good caches by default. Use
  an explicit new output path or obtain permission before replacement.
- Pickle output inspection is local-only and requires trusted files because
  Python pickle deserialization can execute code.

## Escalation record

For a reproducible handoff, retain the command, mode, exact token, config
identity, dataset/split, cache/file-list identity, frame rate, label type,
device/backend, checkpoint basename, first error, and whether the action was
read-only, cache-writing, training, or externally dependent. Omit credentials,
private environment names, and absolute machine paths from public reports.
