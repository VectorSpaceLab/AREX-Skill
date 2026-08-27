# GeoSeg cross-cutting troubleshooting

Read this reference when a failure crosses workflow boundaries. Start by
identifying the route and the exact Python interpreter; then use the nearest
sub-skill's troubleshooting page for dataset, config, model, or output detail.

## Install and import

**Symptoms:** `ModuleNotFoundError` for `torch`, `timm`, `albumentations`,
`ttach`, `catalyst`, `skimage`, or `mamba_ssm`; ABI errors from OpenCV or
Torch; `lightning` fails while `pytorch_lightning` imports.

**Recovery:** run the bundled `scripts/check_env.py` with the intended Python.
Install the documented runtime dependencies into that same interpreter. Use a
CUDA-compatible PyTorch wheel for training/inference, not a CPU wheel. The
source imports `pytorch_lightning`; the root requirements file also names a
`lightning` meta-package whose resolved pydantic dependencies may be
incompatible with this older project. Keep the source-used package and record
any omitted redundant meta-package. Install `causal-conv1d` and `mamba-ssm`
only when selecting PyramidMamba and verify them separately.

**Stop:** do not hide a failed import by changing `PYTHONPATH`, use a different
Python, or call a CPU import a CUDA verification. Do not install all optional
backends merely to run the CPU preprocessing helpers.

## Checkout and path resolution

**Symptoms:** the wrapper cannot find an entry point, config, data directory,
or checkpoint; `FileNotFoundError` appears during config import; outputs are
written in an unexpected location.

**Recovery:** pass an explicit user checkout to
`scripts/run_geoseg_entrypoint.py --repo-root <checkout>`, and use absolute
paths for external data, weights, and outputs when diagnosing. The wrapper
supports only `train_supervision.py`, `vaihingen_test.py`, `potsdam_test.py`,
`loveda_test.py`, `inference_uavid.py`, and `inference_huge_image.py`. Run the
nearest static validator before importing a config. Configs use relative
`data/...`, `model_weights/...`, `pretrain_weights/...`, and
`lightning_logs/...` paths relative to the checkout/current process.

**Stop:** stop when the checkout does not contain the requested public
entry-point, when the config is not a `.py` file, or when the data/checkpoint
root is not the intended one. Do not create empty files to satisfy a config.

## Config and model mismatch

**Symptoms:** config import fails while constructing a dataset or model; a
checkpoint reports unexpected keys or output channels; loss receives the wrong
shape; a model downloads or opens a missing pretrained weight.

**Recovery:** use `model-and-config/scripts/inspect_config.py` or
`training/scripts/check_training_config.py` first. Match the model output
channels to the dataset class count: LoveDA 7, ISPRS Vaihingen/Potsdam 6,
UAVid 8. Keep `ignore_index` aligned with the loss and mask encoding. Check
whether `pretrained=True` uses a timm cache or an explicit `weight_path` before
importing. Ensure a checkpoint was produced by the same model/head and that
its `test_weights_name` matches the file suffix.

**Stop:** do not force-load a mismatched checkpoint, convert masks by modulo or
clipping, or claim that a static config parse proves runtime compatibility.
LoveDA creates a validation dataset at import and therefore needs its external
Urban/Rural validation directories. PyramidMamba remains blocked until its
optional extension is verified.

## CUDA and memory

**Symptoms:** `torch.cuda.is_available()` is false; `.cuda()` fails; the model
runs out of memory; UAVid inference rejects `config.gpus[0]`.

**Recovery:** run `check_env.py` and verify the device name, capability, and
tiny allocation. Install a wheel compatible with the host driver and Python.
Reduce inference `--batch-size`, patch height/width, TTA scale set, or training
batch/crop size; keep input and mask geometry paired. UAVid's script indexes
`config.gpus[0]`, while the training configs commonly use `gpus='auto'`; inspect
and adapt a copied config to an explicit device list only when that is the
intended runtime. Record actual device and settings in the experiment log.

**Stop:** do not substitute CPU for a required CUDA run, launch a large
training job after an unverified smoke, or change several CUDA/package
versions in a user-owned environment without authorization.

## Data, outputs, and masks

**Symptoms:** zero files, unequal counts, wrong colors, all-ignore masks,
shape mismatch during metric accumulation, or output files overwrite another
experiment.

**Recovery:** use `data-preparation` to validate exact stems, suffixes, image
and mask dimensions, label values, palette/channel order, tile/stride, and
output provenance. Keep indexed masks separate from `--gt`/RGB visualization
masks. Use `evaluation-inference/scripts/validate_inference_inputs.py` before
checkpoint execution; it never creates output directories or changes data.
Choose a new output root when changing model, dataset, TTA, tile geometry, or
label representation.

**Stop:** stop when a source/mask partner cannot be established, output format
is ambiguous, or a checkpoint is absent. Equal file counts and a successful
parser check are not evidence of semantic correctness.

## Metrics and claims

GeoSeg's `Evaluator` accumulates a confusion matrix and reports per-class
IoU/F1 plus OA. Vaihingen/Potsdam training/evaluation code excludes the final
class from aggregate mIoU/F1 in several paths; LoveDA/UAVid conventions differ.
Use `scripts/metric_smoke.py` only as a deterministic equation check. Do not
compare metrics from different class orders, ignore-index policies, or
aggregate slices without recording the convention.

## Verification boundary

This graph was generated from commit `9453fe48209c4626b29e35e61bab93b61212c4b1`.
The checkout had no data, weights, checkpoints, native tests, or notebooks.
Core package imports and CUDA preparation passed, but data-bound LoveDA import,
optional PyramidMamba, and full train/inference execution require explicit
external prerequisites. Preserve those limits in every handoff.
