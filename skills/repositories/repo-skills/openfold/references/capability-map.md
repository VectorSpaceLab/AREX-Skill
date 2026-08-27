# OpenFold Capability Map

Use this map to choose the smallest useful route for a user request. Each route is self-contained inside this generated skill tree.

## Primary Workflows

| Capability | Owner | Key references | Bundled helpers |
| --- | --- | --- | --- |
| Environment validation, install/build troubleshooting, parameter/database planning | `sub-skills/installation-assets/` | `sub-skills/installation-assets/references/environment-and-assets.md`, `sub-skills/installation-assets/references/troubleshooting.md` | `sub-skills/installation-assets/scripts/check_openfold_environment.py`, `sub-skills/installation-assets/scripts/plan_asset_downloads.py`, `scripts/check_openfold_imports.py` |
| Monomer inference with generated or precomputed alignments | `sub-skills/inference/` | `sub-skills/inference/references/cli-reference.md`, `sub-skills/inference/references/inference-workflows.md` | `sub-skills/inference/scripts/build_inference_command.py`, `sub-skills/inference/scripts/validate_inference_inputs.py` |
| Multimer inference | `sub-skills/inference/` with asset/data checks from siblings | `sub-skills/inference/references/inference-workflows.md`, `sub-skills/installation-assets/references/environment-and-assets.md` | `sub-skills/inference/scripts/build_inference_command.py`, `sub-skills/installation-assets/scripts/plan_asset_downloads.py` |
| SoloSeq / ESM single-sequence inference | `sub-skills/inference/` | `sub-skills/inference/references/inference-workflows.md`, `sub-skills/inference/references/troubleshooting.md` | `sub-skills/inference/scripts/validate_inference_inputs.py` |
| Template threading | `sub-skills/inference/` | `sub-skills/inference/references/cli-reference.md` | `sub-skills/inference/scripts/build_inference_command.py`, `sub-skills/inference/scripts/validate_inference_inputs.py` |
| FASTA, MSA, mmCIF, alignment directory, alignment DB, cache, duplicate-chain, and cluster-file preparation | `sub-skills/data-preparation/` | `sub-skills/data-preparation/references/data-formats.md`, `sub-skills/data-preparation/references/cache-and-db-workflows.md` | `sub-skills/data-preparation/scripts/validate_alignment_layout.py`, `sub-skills/data-preparation/scripts/inspect_mmcif_cache.py`, `sub-skills/data-preparation/scripts/plan_alignment_db.py` |
| Initial training and fine-tuning | `sub-skills/training/` | `sub-skills/training/references/training-cli-reference.md`, `sub-skills/training/references/training-workflows.md` | `sub-skills/training/scripts/build_training_command.py` |
| Distributed training and DeepSpeed config | `sub-skills/training/` | `sub-skills/training/references/distributed-and-deepspeed.md` | `sub-skills/training/scripts/build_deepspeed_config.py` |
| Python API, config presets, weight import, protein outputs, validation metrics | `sub-skills/model-apis/` | `sub-skills/model-apis/references/api-reference.md`, `sub-skills/model-apis/references/config-presets.md`, `sub-skills/model-apis/references/weights-and-checkpoints.md` | `sub-skills/model-apis/scripts/inspect_openfold_api.py`, `sub-skills/model-apis/scripts/validate_config_preset.py` |
| Acceleration internals: DeepSpeed, cuEquivariance, FlashAttention, TensorRT, long-sequence mode | `sub-skills/model-apis/` plus installation checks | `sub-skills/model-apis/references/acceleration.md`, `sub-skills/installation-assets/references/troubleshooting.md` | `sub-skills/model-apis/scripts/validate_config_preset.py`, `sub-skills/installation-assets/scripts/check_openfold_environment.py` |

## Support Workflow Ownership

- `installation-assets` owns optional dependency, compiled extension, external binary, parameter, and database diagnosis. It does not build production environments automatically or run downloads.
- `data-preparation` owns precomputed alignment and cache layout validation. `inference` may check whether inputs are present before command construction, but data layout depth belongs to `data-preparation`.
- `training` owns command construction and DeepSpeed config emission. It links to `data-preparation` for alignment DBs, mmCIF caches, chain caches, duplicate-chain handling, and cluster files.
- `model-apis` owns config/API/weight internals. It links to `inference` or `training` when users should prefer public CLIs.

## Native Evidence Anchors

- CLI scripts: `run_pretrained_openfold.py`, `thread_sequence.py`, and `train_openfold.py` informed command builders and CLI references.
- Example layout: monomer FASTA, precomputed alignment files, and sample prediction outputs informed inference/data validation recipes.
- Test fixtures: tiny FASTA, mmCIF files, alignment files, feature pickles, and cache JSON informed validators and usability cases.
- Tests: parser/data pipeline/model/import-weight/kernel/DeepSpeed/cuEquivariance tests informed capability boundaries and skip reasons.

Full model inference, database downloads, parameter downloads, cache generation over full corpora, and training are intentionally treated as unsafe/expensive native checks unless the user explicitly approves them.
