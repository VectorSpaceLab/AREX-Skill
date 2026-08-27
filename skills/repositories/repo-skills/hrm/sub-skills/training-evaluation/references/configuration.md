# HRM Training Configuration

## Hydra entry point

`pretrain.py` uses Hydra with `config_path="config"` and
`config_name="cfg_pretrain"`. CLI overrides use standard Hydra dot syntax:

```bash
python pretrain.py data_path=data/sudoku-extreme-1k-aug-1000 epochs=20000 arch.L_cycles=8
```

Verified default config from `config/cfg_pretrain.yaml`:

```yaml
defaults:
  - arch: hrm_v1
  - _self_
hydra:
  output_subdir: null
data_path: data/arc-aug-1000
global_batch_size: 768
epochs: 100000
eval_interval: 10000
checkpoint_every_eval: true
lr: 1e-4
lr_min_ratio: 1.0
lr_warmup_steps: 2000
beta1: 0.9
beta2: 0.95
weight_decay: 0.1
puzzle_emb_weight_decay: 0.1
puzzle_emb_lr: 1e-2
```

The default architecture is documented in the `model-architecture` sub-skill.

## `PretrainConfig` fields

Verified live fields:

- `arch`: nested architecture/loss config.
- `data_path`: converted HRM dataset root.
- `global_batch_size`: total batch across all distributed ranks. Must be
  divisible by world size.
- `epochs`: total epochs.
- `eval_interval`: epochs per train/eval cycle; must divide `epochs`.
- `checkpoint_every_eval`: save at every eval cycle instead of only final.
- Optimizer schedule: `lr`, `lr_min_ratio`, `lr_warmup_steps`, `beta1`, `beta2`,
  `weight_decay`.
- Puzzle embedding optimizer: `puzzle_emb_lr`, `puzzle_emb_weight_decay`.
- Names and outputs: `project_name`, `run_name`, `checkpoint_path`.
- Extras: `seed`, `eval_save_outputs`.

## Runtime defaults filled by code

On rank 0, `load_synced_config` fills:

- `project_name = f"{basename(data_path).capitalize()} ACT-torch"` when unset.
- `run_name = f"{arch.name.split('@')[-1]} {coolname.generate_slug(2)}"` when
  unset.
- `checkpoint_path = checkpoints/<project_name>/<run_name>` when unset.

The filled config is broadcast to all ranks in distributed mode.

## Evaluation config

`evaluate.py` parses command-line key/value pairs with OmegaConf, not Hydra.
Required field:

```bash
checkpoint=<CHECKPOINT_PATH>
```

Optional field:

```bash
save_outputs=[inputs,labels,puzzle_identifiers,logits,q_halt_logits,q_continue_logits]
```

The evaluator opens `all_config.yaml` from the checkpoint directory, sets
`eval_save_outputs`, loads the checkpoint file, and saves selected outputs to
`<checkpoint>_all_preds.<rank>` when `config.checkpoint_path` is set.

## Important invariants

- `epochs % eval_interval == 0` when `eval_interval` is set.
- `global_batch_size % WORLD_SIZE == 0`.
- `config.arch.name` and `config.arch.loss.name` must resolve through
  `utils.functions.load_model_class` under the `models.` prefix.
- Dataset metadata drives `vocab_size`, `seq_len`, and
  `num_puzzle_identifiers`; do not hard-code those values in training commands.
- `DISABLE_COMPILE=true` disables `torch.compile` in `create_model`, useful for
  debugging and bounded smoke checks.
- `WANDB_MODE=offline` avoids hosted W&B login during smoke/debug runs while
  preserving logging behavior.
