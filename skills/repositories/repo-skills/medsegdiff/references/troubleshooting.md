# Cross-cutting troubleshooting

## Import or dependency failure

The repository has no formal package metadata; a successful install of
`requirement.txt` alone does not make `guided_diffusion` importable. Run the
bundled environment checker from the checkout or add the repository root to
the process's import path. Check `torch`, `torchvision`, `numpy`, `scipy`,
`nibabel`, `opencv-python`, `scikit-image`, `blobfile`, `visdom`, and
`torchsummary` as applicable. Do not repair a user-owned environment blindly;
use an isolated environment and record versions.

If an error names `torchvision::nms`, an undefined symbol, or a CUDA shared
library, treat it as a torch/torchvision/backend mismatch. Install a matched
pair for the chosen Python and CUDA wheel family, then rerun the checker. A
CPU import does not prove a CUDA run.

## CUDA and memory

The source's full train/sample paths are CUDA-dependent. Probe
`torch.cuda.is_available()`, device count, device name, and a tiny allocation
before launching. If a visible GPU is already full, select an explicitly
approved free device with `CUDA_VISIBLE_DEVICES` or stop and obtain capacity;
do not terminate unrelated jobs. `nvidia-smi` driver support and the installed
PyTorch CUDA runtime must be compatible. `nvcc` is not needed for ordinary pip
wheels unless compiling an extension.

Reduce `image_size`, `num_channels`, `num_res_blocks`, `batch_size`, or use
`microbatch` only when the resulting architecture remains compatible with the
checkpoint and experiment. Never report an out-of-memory workaround as a
paper-equivalent configuration without recording the change.

## Data and path failures

Dataset loaders use strict source-specific names and positional CSV columns.
Use `data-preparation`'s validator before changing model flags. Confirm the
working directory because the documented defaults are relative paths. Verify
that image/mask pairs, NIfTI modalities, slice counts, and output directories
are readable. A path that exists but has the wrong branch layout can produce an
empty dataset or an assertion later in iteration.

## CLI and boolean failures

Every boolean option is parsed from an explicit value. Use `True`/`False` or
one of the accepted aliases rather than a bare flag. Exact branch values are
case-sensitive: `ISIC` and `BRATS` select dedicated loaders; anything else
selects the custom branch. Inspect effective defaults with the bundled
training or sampling inspector before launching a costly process.

## Checkpoint and version failures

`version`, image size, input channels, model width/depth, attention settings,
diffusion schedule, and checkpoint state must agree. A `module.` prefix may be
removed for DataParallel checkpoints, but that does not fix an architecture
mismatch. Inspect missing/unexpected keys and tensor shapes without mutating the
checkpoint. Resume filename handling for optimizer and EMA files is not fully
consistent with the saved names in the inspected source; verify optimizer/EMA
restoration independently instead of assuming it occurred.

## Sampling-only failures

The source sampler creates CUDA timing events and calls synchronization even
when the surrounding task looks like a CPU smoke test. Use the bundled parser
inspector and evaluators for CPU checks; use a CUDA runtime, real checkpoint,
and user-provided data for source sampling. Keep `batch_size=1` unless output
ID handling has been patched. Record `--num_ensemble`, `--use_ddim`,
`--dpm_solver`, `--diffusion_steps`, and `version` with every result.

## Evaluation failures

The original ISIC evaluator matches files containing `ens` to
`ISIC_<first-token>_Segmentation.png` and can divide by zero when no pairs are
found. The bundled evaluator sorts inputs, reports missing pairs, and fails
explicitly for zero valid pairs. Use it for deterministic fixture checks, but
inspect any naming adaptation before interpreting a score. Per-class output
also depends on two-class labels and the optional `prettytable` package.

Stop and ask for user data, credentials, hardware, or approval when those are
required; do not download medical datasets or fabricate checkpoint results.
