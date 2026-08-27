# Repo provenance

- Source repository: Helios
- Remote URL: https://github.com/PKU-YuanGroup/Helios.git
- Source commit: `47219a07860f158ce56a3b1d1ee2e012aab5c39b`
- Source branch: `main`
- Exact tag: none detected
- Working tree state at source analysis: clean before generated skill files were written
- Current checkout state after generation: dirty, with generated skill and artifact files added during this run
- Package version: not declared in repository metadata

## Evidence paths

Primary evidence used for this generated skill:

- `README.md`
- `requirements.txt`
- `requirements_npu.txt`
- `install.sh`
- `app.py`
- `infer_helios.py`
- `train_helios.py`
- `helios/`
- `scripts/inference/`
- `scripts/training/`
- `scripts/accelerate_configs/`
- `tools/offload_data/`
- `tools/merge_lora_for_helios.py`
- `example/`
- `eval/` was inspected and intentionally not selected as a primary runtime route

## Refresh trigger

Refresh this skill when Helios changes its public model IDs, diffusers API
surface, training YAML schema, data-preparation file formats, or required
backend package set.
