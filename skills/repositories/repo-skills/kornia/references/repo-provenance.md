# Repository Provenance

## Source snapshot

- Repository: Kornia (`kornia/kornia`).
- Remote URL: `https://github.com/kornia/kornia.git`.
- Branch: `main`.
- Commit: `3358ef16113456a5df1efe105e3ffb93a0e7d6ac`.
- Exact tag: none detected at this commit.
- Package version: `0.9.0rc1` from package metadata/runtime inspection.
- Working tree state during skill creation: dirty because production outputs under `skills/` were untracked. No source-code modifications were required for this skill.

## Evidence paths

Relative evidence paths used for this skill include:

- `pyproject.toml`, `pixi.toml`, `uv.lock`.
- `README.md`, `README_zh-CN.md`, `ROADMAP.md`, `TESTING.md`, `CONTRIBUTING.md`, `AI_POLICY.md`.
- `kornia/` public package source.
- `docs/source/get-started/`, `docs/source/*.rst`, `docs/source/applications/`, `docs/source/models/`.
- `tests/`, `testing/`, `conftest.py`, `tests/api_surface.json`.
- `benchmarks/README.md`, `benchmarks/augmentation/`, `benchmarks/filters/`, `benchmarks/geometry/`, `benchmarks/feature/`.
- `.claude/skills/kornia-developer/SKILL.md` as maintainer workflow evidence.

## Environment inspection summary

A private inspection environment verified:

- Import of `kornia` and representative public submodules.
- Distribution version `0.9.0rc1`.
- Representative CPU and CUDA tensor smokes for filters, geometry, augmentation, and descriptor matching.
- Public signatures for key APIs such as `AugmentationSequential`, `RandomAffine`, `gaussian_blur2d`, `warp_perspective`, `match_nn`, `load_image`, `write_image`, and `ONNXSequential`.

Private environment paths and command logs are intentionally omitted from this public provenance file.

## Refresh guidance

Refresh this skill when any of the following change:

- Package version or public module import layout.
- Tensor layout/range conventions, dtype/backend support, or test fixture semantics.
- Augmentation container data-key semantics or transform-matrix behavior.
- Geometry matrix direction, `align_corners` defaults, camera conventions, or epipolar/calibration APIs.
- Feature/model pretrained-weight loading behavior or optional dependency requirements.
- ONNX/transpiler APIs, benchmark methodology, or maintainer contribution policy.
