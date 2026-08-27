# Model And Checkpoint Reference

DiffDock model construction is driven by saved parser/config values. Keep checkpoint files and `model_parameters.yml` together, and treat architecture-affecting flags as compatibility contracts.

## Parameter Categories

General/run parameters:

- `--config`: YAML overlay for parser defaults.
- `--log_dir`, `--run_name`: output directory is `<log_dir>/<run_name>`.
- `--restart_dir`, `--restart_ckpt`, `--restart_lr`: optimizer-aware restart path for score training.
- `--pretrain_dir`, `--pretrain_ckpt`: model-weight initialization without optimizer state.
- `--wandb`, `--project`: optional W&B logging.

Dataset/cache parameters:

- `--dataset`: score-training family; important values are `pdbbind`, `moad`, `generalisation`, `distillation`, and `pdbsidechain`.
- `--pdbbind_dir`, `--moad_dir`, `--pdbsidechain_dir`: dataset roots.
- `--split_train`, `--split_val`, `--split_test`: split-file paths for PDBBind-style workflows.
- `--cache_path`: graph cache base path.
- `--limit_complexes`: cap for train/validation complexes.
- `--combined_training`, `--triple_training`: combine PDBBind, MOAD, and sidechain datasets.

Training/scheduler parameters:

- `--n_epochs`, `--batch_size`, `--lr`, `--w_decay`.
- `--scheduler`, `--scheduler_patience`, `--lr_start_factor`, `--warmup_dur`.
- `--use_ema`, `--ema_rate`.
- `--val_inference_freq`, `--train_inference_freq`, `--inference_steps`, `--num_inference_complexes`: expensive inference-in-training controls.

Diffusion/loss parameters:

- `--tr_weight`, `--rot_weight`, `--tor_weight`, `--confidence_weight`.
- `--rot_sigma_min/max`, `--tr_sigma_min/max`, `--tor_sigma_min/max`.
- `--no_torsion`, `--sampling_alpha`, `--sampling_beta`, `--bootstrap_*`.
- `--sidechain_loss_weight`, `--backbone_loss_weight`.

Graph/data geometry parameters:

- `--all_atoms`, `--chain_cutoff`, `--receptor_radius`, `--c_alpha_max_neighbors`.
- `--atom_radius`, `--atom_max_neighbors`.
- `--max_lig_size`, `--remove_hs`, `--num_conformers`.
- `--matching_popsize`, `--matching_maxiter`, `--matching_tries`.
- `--protein_file`, `--include_miscellaneous_atoms`.
- `--not_fixed_knn_radius_graph`, `--not_knn_only_graph`.

Model architecture parameters:

- `--num_conv_layers`, `--max_radius`, `--ns`, `--nv`.
- `--distance_embed_dim`, `--cross_distance_embed_dim`.
- `--no_batch_norm`, `--dropout`, `--use_second_order_repr`.
- `--cross_max_distance`, `--dynamic_max_cross`.
- `--embedding_type`, `--sigma_embed_dim`, `--embedding_scale`.
- `--smooth_edges`, `--odd_parity`, `--sh_lmax`, `--tp_weights_layers`.
- `--num_prot_emb_layers`, `--reduce_pseudoscalars`, `--embed_also_ligand`, `--depthwise_convolution`.

ESM/language-model parameters:

- `--pdbbind_esm_embeddings_path`.
- `--moad_esm_embeddings_path` and `--moad_esm_embeddings_sequences_path`.
- `--pdbsidechain_esm_embeddings_path` and `--pdbsidechain_esm_embeddings_sequences_path`.
- `--esm_embeddings_model`: requests model-side LM embeddings instead of precomputed embeddings.

## Score Model Compatibility

The model factory chooses architecture by flags:

- `all_atoms: false` uses the coarse-grained model.
- `all_atoms: true` uses the all-atom model.
- ESM paths set a precomputed language-model embedding mode.
- `esm_embeddings_model` selects an in-model LM embedding type.
- Sidechain or backbone loss weights enable sidechain prediction behavior.
- Confidence mode is disabled for score training and enabled for confidence training.

Architecture-affecting values in `model_parameters.yml` must match the checkpoint. Incompatible changes commonly cause missing/unexpected state-dict keys or tensor shape mismatches. Treat these as fixed unless deliberately training a new model:

- `all_atoms`.
- ESM/language embedding mode and dimensions.
- `num_conv_layers`, `ns`, `nv`, representation/order settings, and embedding dimensions.
- Confidence-head options for confidence checkpoints.
- Sidechain/backbone and atom-confidence options.
- Old-model compatibility flags.

## Confidence Model Compatibility

Confidence training reads the score run's `model_parameters.yml` from `--original_model_dir` to construct score-model graph/cache expectations and, when `--transfer_weights` is set, to build the confidence model before copying compatible score weights.

Confidence-specific flags include:

- `--original_model_dir`: score run directory containing `model_parameters.yml` and the selected score checkpoint.
- `--ckpt`: score checkpoint inside `--original_model_dir`, default `best_model.pt`.
- `--use_original_model_cache`: reuse graph cache path derived from the original score-model args.
- `--cache_creation_id` and `--cache_ids_to_combine`: manage repeated ligand-position/RMSD generation runs.
- `--samples_per_complex` and `--inference_steps`: control generation of confidence training examples.
- `--rmsd_prediction`: use regression instead of classification.
- `--rmsd_classification_cutoff`: binary cutoff or list of cutoffs for multiclass output.
- `--confidence_no_batchnorm`, `--confidence_dropout`: confidence readout options.

Changing `--all_atoms`, ESM embeddings, graph geometry, or cache reuse policy between score and confidence workflows can force cache regeneration or make generated ligand positions incompatible with complex graphs.

## Old Model And All-Atom Notes

The model factory still supports old model classes when an explicit old-model path uses that option. Current score/confidence training paths use the current coarse-grained or all-atom classes based on `all_atoms`.

Use `--all_atoms` only when the dataset and environment can support atom-level receptor graphs. The PDBBind class asserts that all-atom mode is not combined with the wrong KNN-only setting, and all-atom caches include atom radius/neighbors in their path. Confidence training defaults `--all_atoms` to true, so verify whether that matches the score model and intended confidence dataset.

## Checkpoint File Meanings

| File | Producer | Contents | Use |
| --- | --- | --- | --- |
| `model_parameters.yml` | Score and confidence training | Serialized parser/config state | Reconstruct model, dataset, cache, and inference settings. |
| `best_model.pt` | Score and confidence training | Model state dict | Best checkpoint by validation loss for score, by main confidence metric for confidence. |
| `last_model.pt` | Score and confidence training | Restart dict with epoch/model/optimizer and score EMA when available | Resume training. |
| `best_ema_model.pt` | Score training | EMA model state dict | Inference/evaluation when EMA was enabled and validation improved. |
| `best_inference_epoch_model.pt` | Score training | Model state dict | Best checkpoint by validation inference metric. |
| `epoch<N>_best_model.pt` | Score training | Copy of best score checkpoint | Periodic archive when save frequency is enabled. |
| `model_epoch<N>.pt` | Confidence training | Confidence model state dict | Periodic archive when save frequency is enabled. |
| `best_model_epoch<N>.pt` | Confidence training | Copy of best confidence checkpoint | Periodic best archive when save frequency is enabled. |

## Config Portability

A YAML `--config` can override parser defaults. Before reusing a config:

1. Confirm all relative paths are valid from the intended DiffDock working directory.
2. Check dataset and split choices against the available roots.
3. Check `all_atoms`, ESM paths, model-size flags, and sidechain/confidence flags against the checkpoint family.
4. Remove or change machine-specific paths, run names, W&B settings, and old cache paths when moving between machines.
5. Keep a copy of the final emitted `model_parameters.yml` as the canonical run configuration.

Do not hand-edit a checkpoint to fix mismatches. Build a compatible command/config or train a new compatible model.
