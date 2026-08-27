# OpenAlphaTensor Configuration

## Purpose

Read this when you want to translate a JSON file or CLI flags into the public training API.

## Source defaults

The bundled `config.json` uses keys such as:

- `batch_size`
- `max_epochs`
- `action_memory`
- `optimizer`
- `weight_decay`
- `lr`
- `lr_decay_factor`
- `lr_decay_steps`
- `device`
- `len_data`
- `pct_synth`
- `n_synth_data`
- `limit_rank`
- `alpha`
- `beta`
- `matrix_size`
- `embed_dim`
- `actions_sampled`
- `n_actors`
- `mc_n_sim`
- `n_cob`
- `cob_prob`
- `cardinality_vector`
- `n_bar`

## CLI-to-API mapping

- `matrix_size` determines `input_size = matrix_size ** 2`.
- `action_memory` becomes `tensor_length = action_memory + 1`.
- `cardinality_vector` and `matrix_size` determine `n_steps` and `n_logits` in `main.py`.
- `alpha` and `beta` are bundled into `loss_params`.
- `checkpoint_dir`, `checkpoint_data_dir`, `save_dir`, `device`, and `extra_devices` pass through to the public API.

## Output layout

The training flow writes `final_model.pt` and `model_params.json` in the save directory. Checkpoints live under the configured checkpoint directory and are resumed automatically when present.
