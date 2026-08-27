# Repository Provenance

Generated skill id: `timm`

## Source Snapshot

- Project: PyTorch Image Models (`timm`)
- Source commit: `87fc38a5569e9ce153378373851469562536dec4`
- Branch: `main`
- Exact tag: none detected
- Remote URL: `https://github.com/huggingface/pytorch-image-models.git`
- Working tree state at generation: dirty because generated skill artifacts were present
- Package version from source/installed metadata: `1.0.28.dev0`

## Evidence Paths

- Package metadata: `pyproject.toml`, `setup.cfg`, `requirements.txt`, `requirements-dev.txt`, `MANIFEST.in`
- Public package source: `timm/`
- Public docs: `README.md`, `UPGRADING.md`, `hfdocs/source/`
- Repository workflow scripts: `train.py`, `validate.py`, `inference.py`, `benchmark.py`, `onnx_export.py`, `onnx_validate.py`, `clean_checkpoint.py`, `avg_checkpoints.py`, `bulk_runner.py`, `distributed_train.sh`, `legacy_train.py`, `convert/`
- Behavior evidence: `tests/`
- Result/model metadata: `results/README.md`, `results/model_metadata-in1k.csv`, `results/results-*.csv`, `results/benchmark-*.csv`
- Interoperability evidence: `hubconf.py`, `hfdocs/source/hf_hub.mdx`

## Refresh Triggers

Refresh this skill when any of these change materially:

- `timm` public APIs such as `create_model`, `list_models`, `create_dataset`, `create_loader`, `create_optimizer_v2`, or `create_scheduler_v2`.
- Root scripts add, remove, or rename important CLI flags.
- Pretrained model naming, Hugging Face Hub/local-dir behavior, checkpoint loading, or ONNX export behavior changes.
- NaFlex, distillation tasks, optimizer/scheduler factories, or benchmark/result CSV formats change.
- The package version or source commit differs from the snapshot above and the user needs current behavior.
