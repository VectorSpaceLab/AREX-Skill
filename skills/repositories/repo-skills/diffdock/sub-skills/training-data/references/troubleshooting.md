# Training And Data Troubleshooting

Use this guide before starting heavy DiffDock training jobs. Prefer the bundled validators and command builder to isolate path/config mistakes without importing the full training stack.

## Dependency And Import Failures

Symptoms:

- Import errors for `torch`, `torch_geometric`, `e3nn`, `wandb`, `rdkit`, `prody`, `esm`, `Bio`, or `sklearn`.
- Training import succeeds on one machine but fails on another.
- Direct source imports work for `utils.parsing` but full training imports fail.

Likely cause:

- DiffDock is script-style and has no installable package metadata; full training imports require the optional-heavy ML/chemistry stack and a working source checkout.

Actions:

- Use this sub-skill's helper scripts first; they are pure stdlib by default.
- Verify the training environment separately before running `python -m train`.
- Keep commands rooted at the DiffDock checkout so script-style imports like `utils.*`, `datasets.*`, and `confidence.*` resolve.
- Do not treat a successful parser import as proof that Torch/PyG/RDKit/ProDy training is ready.

## Backend And CUDA Failures

Symptoms:

- CUDA unavailable, CPU-only training is extremely slow, or data parallel/batch behavior differs.
- PyTorch/PyG/e3nn wheels import but fail at runtime.
- `torch.cuda.OutOfMemoryError` or repeated OOM warnings.

Actions:

- Start with `--limit_complexes`, `--n_epochs 1`, and small `--batch_size`.
- Reduce `--num_dataloader_workers` to `0` while debugging.
- Disable or postpone expensive validation inference by avoiding frequent `--val_inference_freq`.
- Lower graph size by reviewing `--all_atoms`, receptor radius, atom radius/neighbors, max receptor size, ligand-size filters, and chain cutoff.
- Expect full-size training to need substantial GPU memory; ask the user before launching.

## Data Path Failures

Symptoms:

- `Folder not found <complex>`.
- Missing protein or ligand files.
- Dataset root exists but split validation reports many missing complexes.
- PoseBusters data uses non-default protein/ligand stems.

Actions:

- Run [../scripts/validate_dataset_layout.py](../scripts/validate_dataset_layout.py) with the intended dataset type and split path.
- For PDBBind-style data, confirm each split id has `<id>/<id>_protein_processed.pdb` or the intended alternate protein stem.
- For ligand files, confirm `<id>_ligand.sdf`, `<id>_ligand.mol2`, or another planned ligand stem exists.
- For PoseBusters-style data, pass matching `--protein-file` and `--ligand-file` values to the validator and training/evaluation command.
- Do not use inference CSV files as score-training split files.

## Split And Schema Failures

Symptoms:

- Empty train or validation dataset.
- MOAD training ignores a plain split expectation.
- Sidechain training fails on missing cluster metadata.

Actions:

- Confirm PDBBind/PoseBusters split files are plain one-id-per-line files.
- Confirm MOAD metadata files exist, especially `new_cluster_to_ligands.pkl` under the MOAD root and `data/splits/MOAD_generalisation_splits.pkl` under the working tree.
- Confirm sidechain roots include `list.csv`, `valid_clusters.txt`, `test_clusters.txt`, and nested chain `.pt` files.
- Use `--limit_complexes` for early path debugging, but remember `0` often means no limit in dataset code.

## Cache Failures

Symptoms:

- Stale graph cache appears to be reused after changing geometry flags.
- Confidence training cannot find generated ligand positions for a cache id.
- `heterographs.pkl` or chunked `heterographs<N>.pkl` files are missing.

Actions:

- Use a fresh `--cache_path` when changing architecture/data geometry, all-atom mode, ESM embeddings, split files, protein stem, or ligand filtering.
- For confidence training, decide whether `--use_original_model_cache` is intended; otherwise confidence graph caches can differ from score-model caches.
- If combining confidence cache ids, confirm every `ligand_positions_id<N>.pkl` and matching `complex_names_in_same_order_id<N>.pkl` exists.
- Avoid deleting shared caches during another active run.

## ESM Embedding Failures

Symptoms:

- `ESM embeddings path does not exist`.
- Key mismatch between split ids and aggregate `.pt` keys.
- Missing MOAD sequence mapping file.
- Torch is unavailable when checking aggregate `.pt` files.

Actions:

- Run [../scripts/validate_esm_embedding_index.py](../scripts/validate_esm_embedding_index.py) on the embedding directory or aggregate `.pt`.
- For `.pt` aggregate content inspection, pass `--load-pt`; without that flag the checker reports metadata only.
- For PDBBind aggregate `.pt`, expect keys like `<complex>_chain_<index>`.
- For MOAD, keep the ESM sequence mapping path paired with the aggregate embeddings.
- Regenerate embeddings from prepared FASTA/sequence mapping if keys or chains are missing; do not start training to discover this late.

## W&B Failures

Symptoms:

- Training hangs or fails during W&B initialization.
- Offline environment cannot log.
- Wrong project/entity receives logs.

Actions:

- Omit `--wandb` for local smoke tests.
- Enable W&B only after the user confirms account, network, project, and logging expectations.
- Keep W&B settings out of portable public configs unless they are intentionally generic.

## Checkpoint And Config Failures

Symptoms:

- Missing `model_parameters.yml` next to checkpoint.
- State-dict shape mismatch.
- Missing/unexpected keys during restart or confidence transfer.
- Confidence training fails to find score-model checkpoint.

Actions:

- Confirm the run directory contains both `model_parameters.yml` and the selected `.pt` checkpoint.
- For score restart, check whether `--restart_ckpt` expects a name without `.pt`.
- For confidence training, check `--original_model_dir` and `--ckpt` together.
- Compare architecture-affecting flags: `all_atoms`, ESM mode, hidden dimensions, convolution layers, representation flags, sidechain/atom-confidence flags, and old-model options.
- Do not mix all-atom confidence defaults with coarse-grained score checkpoints unless the run is explicitly planned for that.

## OOM During Confidence Dataset Generation

Symptoms:

- Confidence training fails before epochs begin.
- Generation of ligand positions/RMSDs consumes too much memory or time.

Actions:

- Reduce `--limit_complexes`, `--samples_per_complex`, and `--inference_steps`.
- Use a small score checkpoint trial before generating full confidence caches.
- Ensure the score model and confidence graph settings agree before paying the generation cost.
- Reuse known-good generated cache ids only when their dataset, score checkpoint, and graph settings match.

## When To Route Elsewhere

- If the user wants to run inference with trained checkpoints, route to `../docking-inference/SKILL.md`.
- If the user wants benchmark metrics after training, route to `../evaluation-benchmarks/SKILL.md`.
- If the user wants Gradio launch/debug help, route to `../web-ui/SKILL.md`.
