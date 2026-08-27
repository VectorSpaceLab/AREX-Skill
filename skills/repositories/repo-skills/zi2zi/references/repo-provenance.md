# zi2zi repo provenance

- Schema: `disco.repo-provenance.v1`

This generated operating skill was distilled from the public zi2zi repository
state below. Paths are relative evidence paths from the source tree; no local
checkout or environment paths are required to use the skill.

## Source state

- Repository name: `zi2zi`
- Public project URL: `https://github.com/kaonashi-tyc/zi2zi`
- VCS: git
- Commit: `546025f59690b7c7c85de0146aba6f24f26f6b9d`
- Branch: `master`
- Exact tag: none detected
- Working tree state at distillation: dirty only because generated `skills/`
  production artifacts were present; source evidence files were otherwise from
  the commit above.
- Package version: not declared. The repository has no `setup.py`,
  `pyproject.toml`, or importable `__version__`.
- Public license: Apache 2.0

## Evidence paths used

- `README.md`
- `font2img.py`
- `package.py`
- `train.py`
- `infer.py`
- `export.py`
- `model/__init__.py`
- `model/dataset.py`
- `model/ops.py`
- `model/unet.py`
- `model/utils.py`
- `charset/cjk.json` (keys and usage only; the large charset data is not copied)
- `assets/` (visual intent only; images are not needed at runtime)

## Verification baseline

Private construction checks prepared a legacy Python 2.7/TensorFlow 1.15
inspection environment and verified:

- dependency imports for TensorFlow, NumPy, SciPy, Pillow, and imageio;
- `font2img.py --help`, `package.py --help`, `train.py --help`,
  `infer.py --help`, and `export.py --help`;
- source package import for `model` during inspection;
- TensorFlow graph construction for `UNet` with CUDA devices hidden.

Full GAN training, checkpoint-backed inference/export, pretrained model
downloads, and CUDA device execution were not part of the default verification
baseline. They require user-provided data/checkpoints and explicit runtime
approval.

## Refresh signals

Refresh this skill when any of these change in a target zi2zi checkout:

- command-line flags in `font2img.py`, `package.py`, `train.py`, `infer.py`, or
  `export.py`;
- model checkpoint naming, TensorFlow variable naming, loss terms, or data
  provider behavior in `model/`;
- supported Python/TensorFlow/Pillow/SciPy versions;
- charset keys or data layout assumptions;
- documented experiment layout or pretrained checkpoint guidance.
