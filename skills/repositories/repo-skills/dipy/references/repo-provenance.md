# Dipy Repo Provenance

Schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: Dipy / Diffusion Imaging in Python
- VCS: git
- Commit: `ac9380dd22a66b3868e497d1be1ad238a1528ccb`
- Branch: `master`
- Exact tag: none detected
- Remote URL: `https://github.com/dipy/dipy`
- Working tree state at generation: dirty because DisCo generated new `skills/` content in the checkout
- Relative changed paths summary: `skills/` untracked

## Package Snapshot

- Project metadata name: `dipy`
- Project metadata version: `1.13.0.dev0`
- Installed runtime version observed during inspection: `1.13.0.dev0+git20260617.ac9380d`
- Python requirement from metadata: `>=3.12`
- Base dependencies from metadata: NumPy, SciPy, nibabel, h5py, packaging, tqdm, trx-python
- Optional surfaces intentionally not assumed: visualization (`fury`, `matplotlib`), ML/neural workflows (`torch`, `tensorflow`, scikit-learn-dependent paths), broad `optional`, `all`, `doc`, `dev`, and `benchmark` groups

## Evidence Paths

- `pyproject.toml`
- `README.rst`
- `requirements.txt`
- `requirements/`
- `dipy/`
- `dipy/workflows/`
- `dipy/io/`
- `dipy/core/gradients.py`
- `dipy/denoise/`
- `dipy/reconst/`
- `dipy/direction/`
- `dipy/tracking/`
- `dipy/segment/`
- `dipy/align/`
- `dipy/stats/`
- `dipy/viz/`
- `dipy/*/tests/`
- `dipy/workflows/tests/`
- `dipy/tests/test_scripts.py`
- `doc/user_guide/`
- `doc/interfaces/`
- `doc/theory/`
- `doc/examples/`
- `doc/reconstruction_models_list.rst`
- `doc/tractography_methods_list.rst`
- `tools/`

## Generation Scope

The generated skill covers public Dipy package APIs, command-line workflows, docs examples, and safe synthetic probes for IO/data, denoising/preprocessing, reconstruction, tracking/segmentation, registration/alignment, and CLI workflow mechanics.

Excluded or de-prioritized sources include benchmark-scale workflows, generated docs output, maintainer-only CI/release tooling, and optional GUI/neural paths except as optional dependency guidance.

## Refresh Signals

Refresh this skill when any of these change materially:

- Dipy CLI entry points or `dipy.workflows.cli.cli_flows` mapping.
- Public signatures for IO, gradient, reconstruction, denoise, tracking, segment, align, or workflow APIs mentioned by the sub-skills.
- Optional dependency behavior for visualization, neural workflows, or Patch2Self estimator support.
- Data-format semantics for tractograms, PAM5, bvals/bvecs, or NIfTI IO.
- Docs examples or workflow interface guides that change command names, output names, or recommended validation steps.
