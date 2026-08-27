# Installation and assets

Read this file when MatterGen import, package variants, checkpoints, Git LFS, Hugging Face, or released data are involved.

## Package baseline

The verified package metadata declares distribution `mattergen` version 1.0.3 and Python `>=3.10`. Its Linux dependency contract uses PyTorch 2.2.1 + CUDA 11.8 (`torch==2.2.1+cu118`, torchvision 0.17.1, torchaudio 2.2.1) plus PyTorch Geometric and matching compiled extensions. NumPy is constrained below 2.0. Install the repository's documented package variant rather than combining a newer torch build with old `torch_cluster`, `torch_scatter`, or `torch_sparse` wheels.

A minimal generic check after installation is:

```bash
python -c "import mattergen, torch, torch_geometric, pymatgen; print('mattergen import ok'); print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

The package exposes `mattergen-generate`, `mattergen-train`,
`mattergen-finetune`, `mattergen-evaluate`, and `csv-to-dataset`. Use each
sub-skill's preflight before invoking a workflow. Do not publish a temporary
inspection environment, editable checkout path, or local activation command as
part of a reusable setup recipe.

## Backend choices

- **CUDA (primary Linux path):** required for truthful full generation and
  MatterSim relaxation. Probe `torch.cuda.is_available()` and a small tensor
  operation on a device with free memory. A visible device can still be full;
  use `CUDA_VISIBLE_DEVICES` or a scheduler allocation.
- **CPU:** valid for imports, CLI help, config parsing, structure matching,
  CSV preflight, and many small diffusion/data utility tests. It is not a
  substitute for full generation or GPU MatterSim relaxation.
- **MPS:** documented as experimental on Apple Silicon. Set
  `PYTORCH_ENABLE_MPS_FALLBACK=1` and follow the training route's explicit MPS
  strategy override. This Linux-generated skill does not claim MPS verification.

## Checkpoints and data

The named pretrained catalog is hosted by `microsoft/mattergen` on Hugging
Face and includes `mattergen_base`, `mp_20_base`, `chemical_system`,
`space_group`, `dft_mag_density`, `dft_band_gap`, `ml_bulk_modulus`,
`dft_mag_density_hhi_score`, and `chemical_system_energy_above_hull`.
Generation can also use a local model directory, but it must contain a
`config.yaml` and hydrated checkpoint files. A small text file containing a
Git-LFS pointer is not a usable checkpoint.

The repository also documents Git LFS for checkpoints and released datasets.
Treat `git lfs pull`, Hub downloads, archive extraction, and potential-model
acquisition as explicit, user-approved network/storage actions. Check the
result with `file`, `unzip -t`, or a file-size/content inspection before passing
it to a workflow. Never bundle an automatic downloader or silently retry a
large download.

## Provenance boundary

Record the source release/commit, checkpoint name or path, dataset split and
version, reference/correction scheme, model/potential version, device, and
sampling/evaluation settings in the user's experiment record. The bundled
runtime helpers perform validation but do not replace scientific provenance.
