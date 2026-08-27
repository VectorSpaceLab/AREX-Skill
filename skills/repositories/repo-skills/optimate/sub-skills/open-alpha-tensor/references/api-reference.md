# OpenAlphaTensor API Reference

## Public entry point

- `train_alpha_tensor(tensor_length, input_size, scalars_size, emb_dim, n_steps, n_logits, n_samples, optimizer_name, lr, lr_decay_factor, lr_decay_steps, weight_decay, loss_params, checkpoint_dir, checkpoint_data_dir, epochs, batch_size, len_data, n_synth_data, pct_synth, limit_rank, n_actors, mc_n_sim, N_bar, device, save_dir, random_seed, n_cob, cob_prob, data_augmentation, extra_devices)`

## Parameter groups

- **Model shape**: `tensor_length`, `input_size`, `scalars_size`, `emb_dim`, `n_steps`, `n_logits`, `n_samples`
- **Optimization**: `optimizer_name`, `lr`, `lr_decay_factor`, `lr_decay_steps`, `weight_decay`, `loss_params`
- **Training scale**: `epochs`, `batch_size`, `len_data`, `n_synth_data`, `pct_synth`, `limit_rank`, `n_actors`, `mc_n_sim`, `N_bar`, `n_cob`, `cob_prob`, `data_augmentation`, `extra_devices`
- **Checkpoint/output**: `checkpoint_dir`, `checkpoint_data_dir`, `save_dir`, `random_seed`
- **Device**: `device`

## Return value

The function returns `root_op.get_result()`, which is the trained `AlphaTensorModel` produced by the configured training run.

## Notes

- `optimizer_name` must be one of `adam`, `adamw`, or `sgd`.
- `main.py` derives several values from `matrix_size`, `action_memory`, and `cardinality_vector` before calling this function.
