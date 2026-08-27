# Dexbotic provenance

Schema: `disco.repo-provenance.v1`

- Package: `dexbotic==0.2.0`
- Source repository: public Dexmal/dexbotic repository
- Source commit: `6356c98e6b75d3f4fbc8765913d64ddfd9fe0823`
- Branch: `main`
- Source dirty state at inspection: clean before generated `skills/` artifacts were added
- Python requirement: `>=3.10`
- Extraction decision: `extractionScope: agent-decide` from the user's `auto decide`; broad public workflow scope was confirmed without a routine approval question.
- Import decision: `importAfterVerification: do-not-import`; no managed skill copy or router update is authorized in this run.

## Evidence snapshot

Relative source evidence used for this graph includes:

- `pyproject.toml`, `README.md`
- `dexbotic/client.py`
- `dexbotic/data/data_source/register.py`
- `dexbotic/data/dataset/dex_dataset.py`
- `dexbotic/data/utils/normalize.py`
- `dexbotic/policy/base_policy.py`, `dexbotic/policy/types.py`
- `dexbotic/exp/base_exp.py`, `dexbotic/exp/backend_resolver.py`, `dexbotic/exp/trainer.py`
- `docs/Data.md`, `docs/Tutorial.md`, `docs/InferenceAPI.md`, `docs/DM0RealtimeInference.md`
- `docs/ModelZoo.md`, `docs/DM0.md`, `docs/FSDP2.md`, `docs/LiberoLora.md`
- `docs/RL.md`, `docs/RLinf.md`, `docs/RLinfAsRLBackend.md`, `docs/Uni-NaVid.md`
- `hardware/docs/so101_inference_example.md`, `hardware/docs/xlerobot_inference_example.md`, `hardware/docs/dosw1_inference_example.md`
- `script/convert_data/`, `hardware/*/convert*_to_dexdata.py`, `script/deepspeed/`, `dexbotic/config/rl/`

Binary assets, source checkout paths, generated artifacts, physical bridge execution, external simulator/RL stacks, model downloads, and long-running training/evaluation were excluded from runtime content or retained only as explicit limitations.

## Inspection evidence

A private backend-aware inspection environment imported major package APIs, passed dependency checks, and passed a CUDA smoke on an available A100-class device. The private environment identity and filesystem path are intentionally excluded from this public skill.
