# Repo provenance

This runtime skill was distilled from MosaicML Composer source evidence.

## Source snapshot

- Public project name: MosaicML Composer
- Python distribution: `mosaicml`
- Import package: `composer`
- Package version from source metadata: `0.33.0.dev0`
- Remote URL: `https://github.com/mosaicml/composer.git`
- Source commit: `6405188805a0054b4551ec49e4919c54c971d0e8`
- Branch at distillation: `main`
- Exact tag: none detected
- Working tree state: clean

## Evidence paths used

- Package metadata: `setup.py`, `pyproject.toml`, `MANIFEST.in`, `README.md`
- Core package: `composer/`
- Trainer and core APIs: `composer/trainer/`, `composer/core/`, `composer/models/`
- Methods: `composer/algorithms/`, `composer/functional/`, `docs/source/method_cards/`
- Observability: `composer/callbacks/`, `composer/loggers/`, `composer/profiler/`, `composer/utils/collect_env.py`, `composer/utils/file_helpers.py`
- Distributed and devices: `composer/cli/launcher.py`, `composer/distributed/`, `composer/devices/`, `composer/utils/dist.py`, `composer/utils/parallelism.py`
- Export and integrations: `composer/utils/inference.py`, `composer/callbacks/export_for_inference.py`, `composer/models/huggingface.py`
- Public docs: `docs/source/getting_started/`, `docs/source/trainer/`, `docs/source/notes/`, `docs/source/functional_api.rst`
- Workflow examples as evidence only: `examples/`
- Behavior and verification candidates: `tests/`

## Excluded or de-prioritized evidence

- Build, CI, maintainer, and generated/support assets: `.github/`, `.devcontainer/`, `.pre-commit/`, `docker/`, `docs/source/_images/`, `docs/source/_static/`, `docs/source/_templates/`, `docs/source/tables/`
- Direct runtime reliance on original notebooks/examples was excluded. Useful ideas were distilled into bundled references and smoke scripts.
- Credentialed, networked, SLURM, TPU, long-training, and remote-upload examples were treated as evidence or troubleshooting notes rather than runnable skill dependencies.

## Refresh guidance

Refresh this skill when Composer changes its `Trainer` signature, distribution/extras metadata, algorithm exports, logger/callback APIs, launcher flags, FSDP/FSDP2/parallelism config, export API, HuggingFaceModel behavior, or checkpoint/resumption semantics.
