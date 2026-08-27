---
name: training
description: "Train, resume, smoke-test, or troubleshoot BigGAN-PyTorch GAN
  runs, including BigGAN and BigGANdeep architectures, CUDA parallelism,
  gradient accumulation, EMA, spectral normalization, orthogonal regularization,
  precision modes, checkpoints, datasets, and the checked-in launch recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BigGAN-PyTorch training

Use this sub-skill as the training router for the BigGAN-PyTorch repository. It
covers the executable training path (`train.py` and `train_fns.py`), the model
and numerical building blocks (`BigGAN.py`, `BigGANdeep.py`, `layers.py`,
`losses.py`, and `sync_batchnorm/`), and the bookkeeping/data helpers in
`utils.py`.

## Route by intent

- **Start a run or choose a recipe:** read `references/workflows.md`.
- **Choose flags, understand tensor/optimizer contracts, or modify a model:**
  read `references/api-reference.md`.
- **Diagnose a failed help command, data path, OOM, resume, precision, or
  multi-GPU run:** read `references/troubleshooting.md`.

Do not launch a production-scale run until the CUDA, dataset, output-root, and
experiment-name gates in `workflows.md` pass. The code is designed for CUDA;
`train.py` assigns `device = 'cuda'`, and the sampling/standing-stat utilities
also create tensors on CUDA. A CPU-only run is not a supported fallback.

## Non-negotiable facts

1. The historical README targets PyTorch 1.0.1 plus `tqdm`, `numpy`, `scipy`,
   and `h5py`; this is an old research codebase, so validate the installed
   PyTorch/torchvision pair before a long run.
2. Supported dataset keys are `I32`, `I64`, `I128`, `I256`, their `_hdf5`
   ImageNet forms, `C10`, and `C100`. The key determines resolution, class
   count, and the child name appended below `data_root`; do not substitute an
   arbitrary directory name without updating the metadata dictionaries.
3. `--parallel` uses `torch.nn.DataParallel` around the combined `G_D` module,
   not distributed training. Select visible GPUs with `CUDA_VISIBLE_DEVICES`.
4. The default loss is hinge loss. The training closure averages each
   accumulation loss before `backward()`, then takes one optimizer step for the
   corresponding network.
5. `--ema` creates a non-optimizing generator copy. `--use_ema` affects
   sampling/metrics only when EMA is enabled; it does not change which weights
   are optimized. Standing-stat accumulation is a separate option.
6. `--G_fp16`/`--D_fp16` cast the corresponding modules (and the relevant data)
   to half. The `*_mixed_precision` switches select the repository's naive
   `Adam16`; they are not a modern AMP/Tensor-Core implementation. The README
   reports early collapse risk and no Tensor-Core activation for this path.
7. Checkpoints are a family of files under
   `<weights_root>/<experiment_name>/`: G, D, both optimizer states,
   `state_dict`, and optionally `G_ema`. Resume with the same configuration-derived
   or explicitly supplied experiment name; use `--load_weights` for suffixes
   such as `best0` or `copy0`.
8. On Python 3.11, `python train.py --help` can crash before showing help with
   `ValueError: unsupported format character '#'`. The literal `%#.#f/%#.#e`
   text in the `--logstyle` help string is interpreted by argparse's `%`
   formatter. Escape the literal percent signs in that *help string* as
   `%%#.#f/%%#.#e` (or replace the text with words); keep the runtime
   `--logstyle` value such as `%3.3e` unchanged. The same failure is observable
   on newer Python versions. This is a parser-help bug, not a CUDA diagnosis.

For a short, bounded verification run, use the temporary ImageFolder smoke
harness in `workflows.md`; it bypasses the repository's unconditional Inception
startup, avoids metric evaluation and checkpoint sample sheets, uses one tiny
batch, and keeps all artifacts outside the repository.
