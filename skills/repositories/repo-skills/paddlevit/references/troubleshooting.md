# Cross-cutting troubleshooting

Use this page after the owning sub-skill identifies the task family. Preserve the
first error and classify it before retrying.

## Import and dependency failures

- **`ModuleNotFoundError: paddle`, `yacs`, or `yaml`:** install the matching
  PaddlePaddle build and the small configuration dependencies. For segmentation
  add OpenCV/SciPy/Cityscapes tooling; for COCO add `pycocotools`; for LSUN add
  `lmdb`. Do not install PyTorch/timm unless an explicitly approved porting task
  needs them.
- **Wrong `config`/`utils` module:** a different model folder is earlier on
  `PYTHONPATH` or cached in the process. Start a new process and expose only
  the selected source root.
- **Historical API error on current Paddle:** record Paddle/Python versions and
  run a tiny builder/forward. Apply only a minimal, reviewed compatibility
  patch; do not claim the original training path is current merely because the
  package imports.

## Backend and launch failures

- **CUDA unavailable or cuDNN cannot load:** distinguish a CPU-only Paddle
  wheel, missing driver/runtime, and missing cuDNN shared libraries. Run a tiny
  tensor/layer operation on the requested GPU. Do not replace a required GPU
  result with a CPU import; report the capability as blocked until the backend
  passes.
- **AMP failure:** use AMP only in a training path with a supported NVIDIA
  backend and a healthy CUDA smoke. Re-run without AMP only as a diagnostic, not
  as proof of AMP support.
- **Multi-GPU hang, rank mismatch, or NCCL error:** stop the bounded job, check
  visible-device count, requested `ngpus`, rank/world size, rendezvous and
  per-GPU batch size. Do not retry indefinitely or call single-GPU execution a
  distributed pass.

## Data and config failures

- **Missing file/empty dataset:** validate the exact root, split, list/JSON
  names, image/annotation pairing, and permissions. The skill does not download
  datasets or fabricate labels.
- **Shape/class/checkpoint mismatch:** compare image/crop/patch/window sizes,
  class count, head dimensions, query count, decoder type, and checkpoint keys.
  Start a new output path; do not reshape or partially load weights silently.
- **YAML override appears ignored:** inspect recursive `BASE` resolution and
  parser option names. The selected script may expose only a subset of config
  fields; print the effective config after CLI overrides.

## Operational and artifact failures

- **Export graph error:** check dynamic model eval mode, tensor indexing/shape
  operations, `InputSpec` NCHW shape, and preprocessing parity. Export to a new
  prefix and verify `.pdmodel`, `.pdiparams`, and `.pdiparams.info` before
  creating a predictor.
- **Inference output is numerically wrong:** API success is not accuracy.
  Match RGB/BGR order, resize/crop interpolation, normalization, batch shape,
  and the model's expected image size; compare with a known-good reference.
- **Results/checkpoint were overwritten:** stop and recover from the original
  path if possible. Future runs must use a new output directory and explicit
  overwrite approval; segmentation's historical demo may delete an existing
  results directory.
- **FID/benchmark claim without data:** report the missing real samples,
  reference dataset, metric implementation and checkpoint. A synthetic shape
  smoke cannot establish a paper or model-zoo metric.

## Evidence and stop rules

Keep a distinction between static/parser checks, import/model construction,
GPU smoke, native test, real-data evaluation, and benchmark reproduction. If a
required backend, dataset, checkpoint, credential, or safe output location is
missing, stop at the last proven tier and state the next required input.
