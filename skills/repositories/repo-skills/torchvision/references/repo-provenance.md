# Repo Provenance

- Schema: `disco.repo-provenance.v1`
- Skill id: `torchvision`
- Source project: TorchVision / PyTorch Vision
- VCS: git
- Commit: `65eb7b9e26750ae59e2748d340d8b0ff58b28bec`
- Branch: `main`
- Exact tag: none detected
- Package version from checkout metadata: `0.29.0a0`
- Live inspection package version used for stable API signatures: `torchvision 0.27.1+cpu`
- Dirty state at generation: dirty because the generated `skills/` directory was added during DisCo creation
- Dirty paths summary: `skills/` untracked/generated
- Remote URL: https://github.com/pytorch/vision

## Evidence Paths

- `README.md`
- `setup.py`
- `pyproject.toml`
- `setup.cfg`
- `version.txt`
- `torchvision/`
- `docs/source/index.rst`
- `docs/source/models.rst`
- `docs/source/feature_extraction.rst`
- `docs/source/transforms.rst`
- `docs/source/tv_tensors.rst`
- `docs/source/datasets.rst`
- `docs/source/io.rst`
- `docs/source/utils.rst`
- `docs/source/ops.rst`
- `docs/source/training_references.rst`
- `docs/source/models/`
- `gallery/transforms/`
- `gallery/others/`
- `references/`
- `test/test_models.py`
- `test/test_extended_models.py`
- `test/test_backbone_utils.py`
- `test/test_transforms.py`
- `test/test_transforms_v2.py`
- `test/test_tv_tensors.py`
- `test/test_datasets.py`
- `test/test_datasets_utils.py`
- `test/test_io.py`
- `test/test_image.py`
- `test/test_ops.py`
- `test/test_models_detection_utils.py`
- `test/test_models_detection_negative_samples.py`
- `test/smoke_test.py`

## Refresh Triggers

Refresh this skill when TorchVision changes its model/weight APIs, transform v2 semantics, TVTensor types, dataset catalog, image IO behavior, custom ops/extension loading, reference training scripts, PyTorch/TorchVision compatibility matrix, or major docs guidance.
