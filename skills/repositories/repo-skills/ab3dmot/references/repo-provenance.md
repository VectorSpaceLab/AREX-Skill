# AB3DMOT repo provenance

schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: AB3DMOT
- Public remote: `https://github.com/xinshuoweng/AB3DMOT.git`
- Commit: `61f3bd72574093e367916c757b4747ca445f978c`
- Branch: `master`
- Exact tag: none found for this commit
- Working tree state at generation: clean
- Package/distribution version: not declared; repository has no `pyproject.toml`, `setup.py`, or importable distribution metadata

## Skill generation scope

Included evidence paths:

- `README.md`
- `docs/INSTALL.md`
- `docs/KITTI.md`
- `docs/nuScenes.md`
- `requirements.txt`
- `configs/KITTI.yml`
- `configs/nuScenes.yml`
- `main.py`
- `AB3DMOT_libs/`
- `scripts/pre_processing/convert_det2input.py`
- `scripts/post_processing/`
- `scripts/KITTI/evaluate.py`
- `scripts/KITTI/evaluate_tracking.seqmap.val`
- `scripts/KITTI/label/`
- `scripts/nuScenes/`
- Representative detection schemas under `data/KITTI/detection/` and `data/nuScenes/detection/`
- KITTI mini image/calibration layout under `data/KITTI/mini/`

Excluded or de-prioritized evidence:

- `.git/`
- `__pycache__/`
- Generated review/test artifact directories
- Production logs under the repo-local `skills/` area
- `main1.gif`, `main2.gif` large demo binaries
- `external/` duplicate legacy copies of helpers also present in `AB3DMOT_libs/`
- Large dataset payloads beyond sampled schemas and layout evidence

## Verification baseline

Live CPU inspection checks verified imports, CLI help, config loading, and a synthetic one-frame `AB3DMOT.track` smoke for this source snapshot. Full KITTI and nuScenes benchmark runs require external datasets/results and were not run during generation.

## Refresh guidance

Refresh this skill when any of these change:

- `main.py` flags, config loading, or output naming.
- `configs/*.yml` detector/category/default fields.
- `AB3DMOT_libs/model.py`, `box.py`, `matching.py`, `io.py`, or dataset helper APIs.
- `scripts/pre_processing/`, `scripts/post_processing/`, `scripts/KITTI/`, or `scripts/nuScenes/` commands.
- Dependency or Python-version guidance in `docs/INSTALL.md` or `requirements.txt`.
