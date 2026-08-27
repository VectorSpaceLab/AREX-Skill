# Troubleshooting and recovery

## Missing Python packages or import mismatch

**Symptoms:** `ModuleNotFoundError` for `torch`, `torchvision`, `addict`,
`yapf`, `timm`, `scipy`, `submitit`, `pycocotools`, or `panopticapi`, or an
operator symbol/import error after a PyTorch upgrade.

**Checks and recovery:**

1. Activate the intended environment and run the bundled checker with the
   relevant `--require-*` flags.
2. Run `python -m pip check` and inspect `python -m pip show torch torchvision`.
3. Install a compatible torch/torchvision pair, then install the requirements
   in that same interpreter. Do not mix a CPU-only torch with a CUDA extension
   build.
4. For panoptic-only imports, install `panopticapi` and re-run the check; an
   ordinary box run does not need to import it.
5. If PyTorch, torchvision, CUDA, or the compiler changed, rebuild and
   reinstall `MultiScaleDeformableAttention`; an old binary may import but
   fail at call time.

The checker is diagnostic and read-only. It does not repair the environment.

## `pycocotools` build failures

**Symptoms:** pip fails while building the Git requirement, `_mask.c` or a C
compiler is missing, or `from pycocotools import mask` fails.

The repository requirement points to the COCO API Git subdirectory. Some
checkouts or source distributions do not contain generated C artifacts needed
by that build. Confirm the failure is packaging/toolchain-related rather than
an invalid annotation. As an approved alternative, install a compatible
published `pycocotools` wheel, run `python -c "from pycocotools import mask;
print(mask.__file__)"`, and record the version substitution. Do not edit the
COCO annotations to fix a package build.

## CUDA_HOME, headers, compiler, and linker failures

**Symptoms:** `CUDA_HOME is not set`, `nvcc not found`, `cuda_runtime.h`,
`cuda/std`, `cuda/cccl`, `THC/THCAtomics.cuh`, `ATen`, unresolved symbols, or
unsupported GNU compiler errors while building.

Use this order:

1. Compare `torch.version.cuda`, `nvcc --version`, the active driver, and
   `CUDA_HOME`. Set `CUDA_HOME` to the compatible toolkit root for the current
   shell; do not assume the system default is the one PyTorch uses.
2. Confirm CUDA development headers, not only runtime libraries, are installed.
   CUDA 12.x may need an explicit CCCL include directory, for example the
   active toolkit's `targets/<arch>/include/cccl`. Add it through `CPATH` or
   build include flags only after checking that it exists.
3. Select a supported host GCC/G++ pair. The verified build required GCC <=12;
   a newer host compiler can trigger CUDA's unsupported-compiler guard or
   template failures. Do not suppress the guard as a first response.
4. Set `TORCH_CUDA_ARCH_LIST` to the target compute capability if autodetection
   chooses the wrong architecture. Verify the target GPU is visible and free.
5. Re-run the build from the repository root/ops directory and then run the
   operator test. If PyTorch or any toolchain input changed, rebuild rather
   than trusting an old `.so`.

The operator sources include ATen, CUDA runtime, and legacy THC headers, so a
runtime-only CUDA installation is insufficient. Linker failures can also mean
that the compiler and CUDA libraries come from different installations.

## Extension imports but operator call fails

Check that Python imports the extension from the intended environment, that
`torch.version.cuda` has not changed since compilation, and that the binary
contains the target architecture. Run the repository operator test with a free
GPU. A successful `import MultiScaleDeformableAttention` is only an import
check; it is not numerical validation.

A CPU-only fallback through `ms_deform_attn_core_pytorch` can help isolate
shape logic, but it is a debug/reference implementation and does not satisfy
the standard DINO CUDA backend gate.

## GPU OOM, occupied device, or low occupancy

**Symptoms:** CUDA initialization fails, allocation fails before the model
starts, out-of-memory during a small smoke, or an unexpectedly slow operator.

- Check `CUDA_VISIBLE_DEVICES`, current free memory, and that another process
  is not occupying the selected device. The verified smoke had to select a
  specifically free GPU; do not infer a software incompatibility from a fully
  occupied default device.
- For model setup, reduce the smoke batch/image size and disable expensive
  optional branches only for diagnosis. For the real run, route batch-size,
  accumulation, AMP, and memory policy decisions to training.
- Multi-scale attention memory grows with flattened feature tokens, query
  count, batch size, and feature levels. A 5-scale configuration and large
  images can need materially more memory than 4-scale.
- A warning about non-power-of-two channels per attention head is an efficiency
  warning, not automatically a correctness failure. Keep `hidden_dim / nheads`
  divisible and prefer a power of two for the CUDA kernel.
- If occupancy is poor, verify architecture flags and per-head dimension
  before changing model semantics. Do not claim a throughput result from this
  setup route.

## Config parsing and compatibility

**Symptoms:** syntax/NameError while loading a config, missing key after a
base override, wrong shape at model construction, or a model/checkpoint load
with many missing/unexpected keys.

`SLConfig.fromfile` executes Python config files, resolves `_base_` relative
to the config, rejects syntax errors and duplicate base keys, and supports
`KEY=VALUE` command-line overrides. Parse only trusted config code. Check the
resolved values, not just the child file text, especially:

- `backbone` and `return_interm_indices`;
- `num_feature_levels` and `hidden_dim`/`nheads`;
- `num_classes`, `dn_labelbook_size`, and the dataset's maximum category ID;
- `query_dim`, `num_queries`, `enc_layers`, `dec_layers`, `enc_n_points`, and
  `dec_n_points`;
- `two_stage_type`, `masks`, and `decoder_module_seq`.

A custom dataset with one category ID 1 generally needs the repository's
`num_classes=2` convention, not `num_classes=1`; a sparse category scheme
needs a deliberate remap or a width covering its maximum ID. The README's
custom-data rule also requires `dn_labelbook_size >= num_classes + 1`.

## Optional panoptic path

**Symptoms:** missing `panopticapi`, missing `panoptic_*` JSON/PNG files,
image/annotation filename mismatch, RGB-ID decode errors, or a missing
`coco_panoptic_path`.

Only enable this path when `dataset_file='coco_panoptic'` and masks/panoptic
outputs are required. Validate both the image root and the panoptic root,
including `panoptic_train2017/` or `panoptic_val2017/`, the corresponding
`annotations/panoptic_*.json`, and each referenced PNG. The implementation
replaces `.png` with `.jpg` for the corresponding image and expects aligned
image/annotation records. A normal instance box run should not be blocked by
missing panoptic artifacts.

## Boundary reminders

Do not download COCO, pretrained weights, or checkpoints from this route. Do
not use `datasets.data_util.preparing_dataset`, `remove`, or copy helpers: they
can delete/recreate paths. After setup is accepted, hand off to training for
launch/checkpoint/optimizer work or inference-evaluation for prediction,
post-processing, and metric workflows.
