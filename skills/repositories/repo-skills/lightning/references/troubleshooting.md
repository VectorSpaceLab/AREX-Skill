# Cross-Cutting Lightning Troubleshooting

## Import or Install Fails

Symptoms:
- `ModuleNotFoundError: No module named 'lightning'`
- `ModuleNotFoundError: No module named 'pytorch_lightning'`
- `pip check` reports dependency conflicts
- CLI or serving modules fail only after import

Actions:
1. Confirm the target package and namespace: `python -c "import lightning as L; print(L.__version__)"`.
2. Prefer `pip install lightning` for new code and `pip install pytorch-lightning` only for legacy namespace compatibility.
3. Install focused extras only for the failing surface, such as `jsonargparse[signatures]` for `LightningCLI` or server packages for serving validation.
4. Run `python scripts/lightning_env_report.py --json` from the root skill directory to collect import and version facts.

## Wrong Namespace or Version

Symptoms:
- Code mixes `lightning.pytorch` and `pytorch_lightning` objects.
- Checkpoints or callbacks come from one namespace while the model imports the other.
- A newer source feature is missing in an older installed compatibility package.

Actions:
- Keep a project consistent unless performing a migration.
- For new code, use `lightning` / `lightning.pytorch` imports.
- For existing legacy code, inspect the installed `pytorch_lightning.__version__` and migrate deliberately.

## Optional Dependency Missing

Symptoms:
- `LightningCLI` import asks for `jsonargparse`.
- Logger import fails for WandB, MLflow, Comet, TensorBoard, or Neptune.
- `DeepSpeedStrategy`, XLA, FP8, or serving validator fails after selecting an optional backend.

Actions:
- Identify the owning sub-skill: CLI, distributed accelerators, or deployment serving.
- Install only the dependency for that surface.
- Re-run an import/help check before running training, launching workers, or starting servers.

## Device or Backend Mismatch

Symptoms:
- `accelerator='gpu'` but no GPU is visible.
- `devices=2` on a single-device host.
- Precision mode unsupported by CPU/MPS/TPU/GPU.
- Distributed worker launch hangs or fails.

Actions:
- Route to `sub-skills/distributed-accelerators/SKILL.md`.
- Start with CPU or `accelerator='auto', devices=1` to isolate model/data bugs.
- Validate syntax with `sub-skills/distributed-accelerators/scripts/strategy_config_check.py` before launching distributed workers.
- Only claim GPU/distributed runtime success after running a real backend smoke in the target environment.

## Training or Data Misuse

Symptoms:
- Manual `.cuda()` or `.to(device)` in code that Lightning should manage.
- Manual `DistributedSampler` conflicts with Trainer defaults.
- Callback monitors a metric that is never logged.
- `training_step` returns an invalid value.

Actions:
- Route to `sub-skills/training-core/SKILL.md`.
- Use `fast_dev_run=True` or a tiny batch limit to reproduce quickly.
- Ensure metrics used by checkpointing/early stopping are logged with matching names.
