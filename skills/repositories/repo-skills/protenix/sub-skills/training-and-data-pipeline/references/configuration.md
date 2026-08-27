# Protenix Training Configuration Guide

## Config Parser APIs

The installed package exposes these config helpers:

- `parse_configs(configs, arg_str=None, fill_required_with_null=False)`
- `load_config(path)`
- `save_config(config, path)`

Training uses `parse_sys_args()` internally and expects command-line arguments as `--key value` pairs. Booleans still need explicit values such as `true` or `false`.

## Merge Flow

`runner.train` builds the final training config in two passes:

1. Start from base configs plus data configs under `data`.
2. Parse CLI arguments once with required fields temporarily fillable with `None`, so `--model_name` can be discovered.
3. Merge model-specific defaults for the selected `model_name` into the base/data config.
4. Parse CLI arguments again so command-line overrides have final priority.

This means one-off overrides should be passed on the command line instead of editing source configs.

## Override Syntax

Nested config keys use dot notation:

```bash
--use_wandb false \
--data.train_sets weightedPDB_before2109_wopb_nometalc_0925 \
--data.test_sets recentPDB_1536_sample384_0925,posebusters_0925 \
--data.weightedPDB_before2109_wopb_nometalc_0925.base_info.pdb_list subset.txt \
--model.N_cycle 4 \
--sample_diffusion.N_step 20
```

Rules:

- Every override is `--key value`; do not use valueless booleans.
- List values are comma-separated strings with no spaces inside the value.
- Nullable values can use strings such as `None`, `none`, or `null` where the config type allows null.
- Unknown keys fail during argument parsing because the parser registers known config keys from the config tree.
- Config keys themselves cannot contain periods except as hierarchy separators.

## Required Base Fields

Base fields without safe defaults include:

- `project`
- `run_name`
- `base_dir`
- `eval_interval`
- `log_interval`
- `max_steps`

The first parse can temporarily fill these as null for model-name discovery. The final parse should receive real values or training config parsing will fail.

## Core Training Defaults

Important defaults and demo overrides include:

- `model_name`: default `protenix_base_default_v1.0.0`.
- `seed`: default `42`.
- `dtype`: default `bf16`.
- `train_crop_size`: base default `256`; demo training uses `384`.
- `diffusion_batch_size`: default `48`.
- `model.N_cycle`: base default `4`, while model-specific configs may override it; demo training passes `4` explicitly.
- `sample_diffusion.N_step`: default `200`; demo training uses `20` for cheaper evaluation.
- `triangle_attention`: default `cuequivariance`, with environment override support through `TRIANGLE_ATTENTION` before launch.
- `triangle_multiplicative`: default `cuequivariance`, with environment override support through `TRIANGLE_MULTIPLICATIVE` before launch.
- `use_wandb`: default `true`; safe generated commands pass `false`.
- `checkpoint_interval`: default `-1`, so periodic checkpointing is disabled unless overridden.
- `ema_decay`: default `-1.0`, so EMA is disabled unless set between 0 and 1.
- `eval_first` and `eval_only`: default `false`; use deliberately because evaluation can be expensive.

## Dataset Defaults

Dataset configs resolve paths under `PROTENIX_ROOT_DIR`:

- `data.train_sets`: default `weightedPDB_before2109_wopb_nometalc_0925`.
- `data.test_sets`: default `recentPDB_1536_sample384_0925`.
- Weighted PDB datasets use `mmcif/`, `mmcif_bioassembly/`, and dataset-specific index CSV.GZ files.
- RecentPDB and posebusters evaluation datasets use their own bioassembly/mmCIF directories and index/list files.
- MSA config uses `common/seq_to_pdb_index.json`, `mmcif_msa_template/`, `rna_msa/rna_sequence_to_pdb_chains.json`, and `rna_msa/msas/`.
- Template config uses `mmcif/`, `mmcif_msa_template/`, `common/seq_to_pdb_index.json`, release-date metadata, obsolete-PDB metadata, and `kalign` when needed.
- CCD and cluster config uses `common/components.cif`, `common/components.cif.rdkit_mol.pkl`, `common/obsolete_release_date.csv`, and `common/clusters-by-entity-40.txt`.

When using custom bioassembly/index data, prefer explicit dataset path overrides only when the existing sampler/cropping assumptions still fit. Otherwise, request a project-specific dataset config.

## Fine-Tune and Resume Controls

Common fine-tune fields:

- `load_checkpoint_path`: standard model checkpoint path.
- `load_ema_checkpoint_path`: EMA checkpoint path loaded into model parameters first when present.
- `load_strict`: strict state-dict loading; consider `false` only when model-specific changes justify it.
- `load_params_only`: default `true`, suitable for starting a new fine-tune from weights without optimizer/scheduler state.
- `skip_load_optimizer`, `skip_load_scheduler`, `skip_load_step`, `load_step_for_scheduler`: resume controls for deliberate resume semantics.
- `data.<dataset>.base_info.pdb_list`: text file that restricts released-data fine-tuning to selected PDB IDs.

`FinetuneLRScheduler` is used when `finetune_params_with_substring` has a non-empty first substring. Treat such parameter-group behavior as model-specific.

## Optimizer and Scheduler

Base optimizer/scheduler defaults include:

- `lr`: `0.0018`; demo commands use `0.001`.
- `lr_scheduler`: `af3`.
- `warmup_steps`: `10`; demo commands use `2000`.
- `decay_every_n_steps`: `50000`.
- `min_lr_ratio`: `0.1`.
- `grad_clip_norm`: `10`.
- Adam beta1/beta2: `0.9` and `0.95`.
- Adam weight decay: `1e-8`.

Scheduler names visible from source include `af3`, `cosine_annealing`, and `constant`. Use smaller max steps and less frequent evaluation for planning experiments, but do not launch training without resource approval.

## Data Loader Surfaces

Training calls `get_dataloaders(configs, world_size, seed, error_dir)`. Dataset reading loads the configured index CSV, optionally filters by `pdb_list`, token limits, exclusions, group-by-PDB, and sort-by-token settings, then reads `[pdb_id].pkl.gz` from `bioassembly_dict_dir`.

Index semantics matter because sampler weights and grouping use `type`, `cluster_id`, `entity_1_id`, `entity_2_id`, `mol_1_type`, and `mol_2_type`. Use the bundled checker for shallow schema validation before launching training.

## Safe Validation Order

Prefer checks in this order:

1. `python scripts/check_training_data_layout.py DATA_ROOT --index-csv INDEX.csv`.
2. `python scripts/build_prepare_training_data_command.py ...` for CIF preprocessing planning.
3. `python scripts/build_training_command.py --mode train --data-root DATA_ROOT --base-dir OUTPUT_DIR` for launch-command inspection.
4. `python -m scripts.prepare_training_data --help` only inside an environment with Protenix and its heavy dependencies installed; treat this as help-only.
5. Selected source tests only when the user is explicitly working in a source checkout.

Do not use full downloads, CCD refreshes, custom preprocessing, MSA/template generation, or `runner.train` as validation unless the user explicitly approves the resources and side effects.
