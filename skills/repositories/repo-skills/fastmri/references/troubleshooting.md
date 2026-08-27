# fastMRI Troubleshooting

## Install or import fails

- `ModuleNotFoundError: fastmri`: install the package into the active Python environment before using the skill.
- `ModuleNotFoundError: requests`: install `requests`; this checkout imports it from `fastmri.data.mri_data` even though package metadata does not list it.
- `ModuleNotFoundError` for `torch`, `torchvision`, `pytorch_lightning`, `torchmetrics`, `h5py`, `runstats`, `skimage`, `pandas`, or `yaml`: install the core package dependencies for the workflow you are running.
- Large HDF5 memory growth while reading data can be related to the README's `h5py`/HDF5 leak note; prefer a conda `h5py` build with a compatible HDF5 version when this appears.

## Data or HDF5 layout fails

Use [data-loading](../sub-skills/data-loading/SKILL.md) when the error names `SliceDataset`, `CombinedSliceDataset`, `challenge`, `sample_rate`, `volume_sample_rate`, `dataset_cache.pkl`, `ismrmrd_header`, `kspace`, `mask`, `reconstruction_rss`, or `reconstruction_esc`.

Common fixes:

- Pass split directories such as `multicoil_train` to `SliceDataset`, but pass the parent data root to `FastMriDataModule`.
- Use `challenge="singlecoil"` only for single-coil data and `challenge="multicoil"` for multicoil data.
- Set either `sample_rate` or `volume_sample_rate`, not both.
- Treat test/challenge files as targetless unless they include the expected reconstruction key.

## Tensor or operator errors

Use [mri-operators](../sub-skills/mri-operators/SKILL.md) when errors mention FFT dimensions, final complex dimension size 2, crop shapes, RSS dimensions, SSIM tensors, dtype/device mismatch, or metric array shapes.

Common fixes:

- Convert native complex tensors with `torch.view_as_real` before calling fastMRI FFT helpers.
- Keep complex tensor shape as `... x height x width x 2` for centered FFT/IFFT and complex crops.
- Choose the coil dimension explicitly for `rss`/`rss_complex`.
- Crop predictions and targets to compatible real 3D image stacks before SSIM/PSNR.

## Model or checkpoint errors

Use [model-architectures](../sub-skills/model-architectures/SKILL.md) for U-Net/VarNet constructor choices, tiny shape checks, mask dtype/shape issues, checkpoint key mismatches, CUDA defaults, and offline pretrained inference.

Common fixes:

- Use U-Net for image-domain baselines and VarNet for multicoil k-space reconstruction.
- For VarNet, pass masks aligned to k-space width and use boolean/byte masks deliberately.
- Load pretrained state dicts from local files unless the user explicitly authorizes a network download.
- Map CUDA checkpoints to CPU with `map_location="cpu"` when GPU is unavailable.

## Training or Lightning workflow fails

Use [lightning-training](../sub-skills/lightning-training/SKILL.md) for `FastMriDataModule`, `UnetModule`, `VarNetModule`, trainer settings, CPU fast-dev, DDP, checkpointing, and `combine_train_val`.

Common fixes:

- Prefer explicit `data_path` and `default_root_dir` instead of relying on `fastmri_dirs.yaml`.
- Convert old Lightning demo options (`gpus`, `Trainer.add_argparse_args`, `resume_from_checkpoint`) to the installed Lightning version when needed.
- Use CPU fast-dev settings before GPU/DDP: `num_workers=0`, `batch_size=1`, tiny model parameters, and `fast_dev_run` or one-batch limits.
- Preserve `distributed_sampler=True` for DDP so validation/test volume dispatch remains coherent.

## Evaluation or submission output fails

Use [evaluation-submission](../sub-skills/evaluation-submission/SKILL.md) when prediction files miss `reconstruction`, filenames do not match targets, target keys mismatch challenge, filters skip all files, v2 filenames are needed, or the user asks about leaderboard upload.

Common fixes:

- Save predictions with dataset key `reconstruction`, not `reconstruction_rss` or `reconstruction_esc`.
- Match prediction filenames to target filenames for local evaluation.
- Use `--challenge multicoil` for target key `reconstruction_rss` and `--challenge singlecoil` for target key `reconstruction_esc`.
- Treat public leaderboard availability as uncertain; the repository README states the historical fastmri.org leaderboards are unavailable.
