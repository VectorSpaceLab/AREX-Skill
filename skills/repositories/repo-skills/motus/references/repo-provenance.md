# Repository provenance

schema: disco.repo-provenance.v1

- Source project: Motus, public repository associated with `thu-ml/Motus`.
- Source commit: `f771216802b8a1601599422f12088bee3c068c14`.
- Source branch: `main`.
- Exact tag: none observed at the source commit.
- Working tree at extraction: dirty only from generated skill and review artifacts; the source baseline was otherwise clean when inspected.
- Package version: no `pyproject.toml`, `setup.py`, or distribution metadata was present; the repository is consumed as a source-layout project.
- Public evidence paths: `README.md`, `INFERENCE.md`, `TRAINING.md`, `DATA_FORMAT.md`, `configs/`, `models/`, `data/`, `utils/`, `train/`, `scripts/`, `inference/real_world/Motus/`, and `inference/robotwin/Motus/`.
- Implementation evidence: `bak/wan/` was inspected for attention fallback and scheduler behavior but is not a runtime dependency of this skill.
- Refresh signal: regenerate or refresh this skill when model config fields, dataset factory values, checkpoint layout, inference flags, training parser flags, or external integration paths change.
