# Training Workflows

Boltz training is driven by a Hydra/OmegaConf YAML file and the official Boltz training launcher distributed with source releases. Keep this workflow conservative: validate config and data readiness first, run a debug-style launch in the user's own Boltz training environment, then scale only after a small launch succeeds. This skill bundles validation guidance and helper checks; it does not bundle the full training launcher because that script is tightly coupled to source-release training assets, GPUs, logging, and processed datasets.

## Preconditions

- Python package: `boltz`, Python `>=3.10,<3.13`.
- Training dependencies include PyTorch, PyTorch Lightning, Hydra, OmegaConf, PyYAML, and optionally wandb.
- Data must already be processed into Boltz training format: each dataset target directory has `manifest.json` and a `structures/` subtree, each MSA directory contains processed `.npz` files referenced by manifest records, and `data.symmetries` points to a ligand symmetry pickle.
- The public docs mention preprocessed RCSB targets/MSAs, OpenFold targets/MSAs, and `symmetry.pkl`; they also warn that the complete training data needs about 250 GB of storage.
- Raw-data processing is a separate data-preparation task, not a training launch task.

## Safe Launch Sequence

1. Copy one training template and replace all placeholders with local paths outside the skill.
2. From this skill's `sub-skills/training/` directory, run static validation with the bundled checker:

   ```bash
   python scripts/boltz_training_config_check.py train.yaml --profile debug
   ```

3. If imports are expected to work in the active environment, add:

   ```bash
   python scripts/boltz_training_config_check.py train.yaml --profile debug --check-imports
   ```

4. In the user's Boltz training environment or source-release workspace, run the official training launcher in debug mode using the validated config and a `debug=1` override.
5. Stop after the first successful data/model initialization or first batches if the goal is only smoke testing.
6. Scale gradually: increase `data.max_tokens`, `data.max_atoms`, `data.num_workers`, `trainer.devices`, and `trainer.accumulate_grad_batches` only after the debug path is clean.
7. Launch the full run only when storage, GPU memory, checkpoint strategy, and wandb/logging behavior are intentional.

## What Debug Mode Changes

The training launcher merges command-line dotlist overrides into the YAML and then instantiates the config with Hydra. When `debug=1` or `debug=true` is present:

- `trainer.devices` is forced to one device, or to the first entry if a list was supplied.
- `data.num_workers` is set to `0`, keeping data loading in the main process.
- wandb logging is disabled even if a `wandb:` block exists.

Use debug mode for path, Hydra target, dataset, split, featurizer, and first-batch failures. It is not a proof that full multi-GPU training will fit in memory.

## DDP And Devices

- The launcher keeps `strategy: auto` for single-device runs.
- If `trainer.devices` is an integer greater than one, or a list with more than one entry, it switches to `DDPStrategy(find_unused_parameters=cfg.find_unused_parameters)`.
- Set `find_unused_parameters: true` only when DDP reports unused-parameter errors; it can add overhead.
- For debugging data or Hydra issues, prefer `debug=1` rather than trying to diagnose them through DDP worker failures.

## Checkpoints, Resume, And Pretrained

The launcher has two distinct checkpoint paths:

- `resume`: passed as `ckpt_path` to `trainer.fit()` or `trainer.validate()`. Use it to continue an interrupted Lightning run with optimizer/scheduler/trainer state.
- `pretrained`: used only when `resume` is empty. The model class loads weights with `load_from_checkpoint(..., strict=False, **model_module.hparams)` before trainer construction.

Decision table:

| Goal | Set `resume` | Set `pretrained` | Notes |
| --- | --- | --- | --- |
| Continue an interrupted run | checkpoint path | usually `null` | Preserves Lightning training state. |
| Initialize from weights for a new run | `null` | checkpoint path | Does not resume optimizer/scheduler state. |
| Validate a checkpoint | checkpoint path | usually `null` | Also set `validation_only: true`. |
| Start confidence training from structure trunk | `null` | structure checkpoint path | For confidence config, `load_confidence_from_trunk: true` means broadcast trunk weights into the confidence module; use only when starting from scratch as the source comment states. |

Avoid setting both `resume` and `pretrained` unless intentionally relying on `resume` to win. The training script ignores `pretrained` when `resume` is set.

## Validation-Only Runs

Set:

```yaml
validation_only: true
resume: path/to/checkpoint.ckpt
```

The launcher calls `trainer.validate(..., ckpt_path=resume)`. Validation dataloading still requires processed target/MSA directories, `manifest.json`, split semantics, and `data.symmetries`.

## Wandb

The template leaves wandb commented out. If enabled, provide:

```yaml
wandb:
  name: run-name
  project: project-name
  entity: entity-name
```

The launcher creates a `WandbLogger`, writes `run.yaml` under the wandb experiment directory, and saves it to wandb. For offline or unauthenticated environments, either use debug mode, remove the `wandb:` block, or configure wandb offline/login before launching.

## Storage And Runtime Expectations

- Full public training data is dataset-scale; the docs state about 250 GB for all preprocessed data.
- Template crops use `max_tokens: 512`, `max_atoms: 4608`, `max_seqs: 2048`, padded to maxima, `batch_size: 1`, and large accumulation.
- The docs suggest reducing crop size to `max_tokens/max_atoms` pairs such as `256/2304` or `384/3456` for memory/speed trade-offs.
- Full model training and large validation sampling are GPU-heavy. Provide debug and validation checks, not guarantees of a cheap full run.