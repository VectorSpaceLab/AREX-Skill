# Repository Provenance

## Source Snapshot

- Repository name: `fastMRI`
- Generated skill id/name: `fastmri`
- VCS: git
- Commit: `91f2df4711adbb6d643df1810f234e4abcf5881b`
- Branch: `main`
- Exact tag: none detected
- Package/distribution name: `fastmri`
- Installed package version inspected: `0.1.dev1+g91f2df471`
- Python requirement from package metadata: `>=3.8`
- Working tree state at generation: dirty because generated `skills/` outputs were added; no source-code changes were detected before skill creation.
- Remote URL: https://github.com/facebookresearch/fastMRI

## Evidence Paths

- `README.md`
- `LIST_OF_PAPERS.md`
- `setup.cfg`
- `pyproject.toml`
- `setup.py`
- `fastmri/__init__.py`
- `fastmri/math.py`
- `fastmri/fftc.py`
- `fastmri/coil_combine.py`
- `fastmri/losses.py`
- `fastmri/evaluate.py`
- `fastmri/utils.py`
- `fastmri/data/README.md`
- `fastmri/data/mri_data.py`
- `fastmri/data/subsample.py`
- `fastmri/data/transforms.py`
- `fastmri/data/volume_sampler.py`
- `fastmri/models/__init__.py`
- `fastmri/models/unet.py`
- `fastmri/models/varnet.py`
- `fastmri/models/adaptive_varnet.py`
- `fastmri/models/policy.py`
- `fastmri/pl_modules/data_module.py`
- `fastmri/pl_modules/mri_module.py`
- `fastmri/pl_modules/unet_module.py`
- `fastmri/pl_modules/varnet_module.py`
- `fastmri_examples/README.md`
- `fastmri_examples/zero_filled/README.md`
- `fastmri_examples/zero_filled/run_zero_filled.py`
- `fastmri_examples/unet/README.md`
- `fastmri_examples/unet/train_unet_demo.py`
- `fastmri_examples/unet/run_pretrained_unet_inference.py`
- `fastmri_examples/varnet/README.md`
- `fastmri_examples/varnet/train_varnet_demo.py`
- `fastmri_examples/varnet/run_pretrained_varnet_inference.py`
- `fastmri_examples/adaptive_varnet/README.md`
- `fastmri_examples/feature_varnet/README.md`
- `fastmri_examples/cs/README.md`
- `tests/test_data.py`
- `tests/test_transforms.py`
- `tests/test_math.py`
- `tests/test_models.py`
- `tests/test_modules.py`
- `tests/test_integrations.py`
- `tests/create_temp_data.py`

## Excluded or Limited Evidence

- `banding_removal/`: related research code with its own package tree and requirements; excluded from `setup.cfg` package discovery.
- Example workflows requiring external downloads, external toolkits, real datasets, long training, or separate pinned environments were distilled as reference guidance rather than runtime dependencies.
- Public fastMRI datasets, pretrained weights, and leaderboard upload endpoints were not downloaded or contacted during generation.
