# Repository Provenance

schema: `disco.repo-provenance.v1`

This skill was generated from repository evidence for `scvi-tools`.

## Source Snapshot

- VCS: git
- Commit: `4bada9744d4274f4f82c4015b1c73b4698d830e7`
- Branch: `main`
- Exact tag: none detected
- Working tree state: dirty at generation time
- Dirty summary: untracked `skills/` tree containing generated DisCo runtime and review/test artifacts
- Package version: `1.4.3`
- Remote URL: https://github.com/scverse/scvi-tools

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `src/scvi/`
- `docs/api/`
- `docs/installation.md`
- `docs/faq.md`
- `docs/user_guide/models/`
- `docs/user_guide/use_case/`
- `docs/tutorials/`
- `tests/data/`
- `tests/dataloaders/`
- `tests/train/`
- `tests/model/`
- `tests/external/`
- `tests/hub/`
- `tests/autotune/`
- `tests/criticism/`

## Live Inspection Baseline

- Verified distribution: `scvi-tools==1.4.3`
- Verified imports: `scvi`, `scvi.data`, `scvi.model`, `scvi.external`, `scvi.train`, `scvi.dataloaders`, `scvi.criticism`, `torch`, `anndata`
- Verified backend: CPU PyTorch import and public API inspection; CUDA was not required for skill generation
- Optional extras: not installed for baseline inspection; documented as workflow-specific requirements

## Refresh Triggers

Refresh this skill if any of these change:

- Public `setup_anndata`, constructor, `train`, save/load, hub, or downstream accessor signatures.
- Supported Python version, base dependencies, optional extras, or backend recommendations.
- Model family availability under `scvi.model` or `scvi.external`.
- Data registry semantics, AnnData/MuData field requirements, or dataloader APIs.
- Repository docs or tests for primary workflows diverge from this skill's routing.
