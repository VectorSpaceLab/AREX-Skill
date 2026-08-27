# Training and Data Pipeline Troubleshooting

## `PROTENIX_ROOT_DIR` Is Missing or Wrong

Symptoms:

- Training looks for data under an unexpected home-directory default.
- Index, mmCIF, bioassembly, CCD, MSA/template, or RNA MSA files are missing.
- The data downloader exits because `PROTENIX_ROOT_DIR` is unset.

Actions:

1. Set `PROTENIX_ROOT_DIR` explicitly before training, preprocessing, or search workflows.
2. Run `python scripts/check_training_data_layout.py DATA_ROOT`.
3. Confirm dataset overrides still point to the intended root, especially `indices_fpath`, `bioassembly_dict_dir`, `mmcif_dir`, `pdb_list`, and MSA/template paths.

## Partial Data Root

Symptoms:

- Dataloader fails on missing weighted PDB index, `mmcif_bioassembly`, `mmcif_msa_template`, `common/components.cif`, or `seq_to_pdb_index.json`.
- Template/RNA features are missing for datasets that expect released features.
- A read-only root check finds inference/search components but reports missing training directories or index files.

Actions:

- For inference/search roots, expect `common` and `search_database`, but not training bioassemblies or training indices.
- For training/fine-tuning, require `common`, `indices`, `mmcif`, `mmcif_bioassembly`, `mmcif_msa_template`, `rna_msa`, and `search_database`.
- If only inference data was downloaded, explain that training/fine-tuning needs full data mode and large disk/network approval.
- If custom CIF preprocessing was used, validate the generated CSV and ensure the selected dataset config points at the custom bioassembly directory.

## Huge Disk or Download Requirements

Symptoms:

- Downloads run out of disk.
- Archive extraction partially completes.
- The user asks for full training data on a small filesystem.

Actions:

- Warn that full released training data can require terabyte-scale free space.
- Ask before retrying a failed data download because partial archives and extracted directories can duplicate storage.
- Treat the upstream full-data downloader as side-effect-heavy: it downloads, extracts, and removes archives under the data root.
- Use inference-only data only for inference/search workflows, not training.

## Missing Cluster File

Symptoms:

- Custom preprocessing is planned without `clusters-by-entity-40.txt`.
- Sampling metadata or cluster diversity is unclear.

Actions:

- Explain that the cluster file is optional for the preprocessing command, but it improves sampling metadata for protein clusters.
- If the user needs released-like behavior, obtain or generate a compatible 40 percent identity cluster file before preprocessing.
- If the user is doing a tiny custom fine-tune, proceed only after documenting the cluster-file trade-off and validating the generated index CSV.

## Missing or Stale CCD Cache

Symptoms:

- Custom/new structures include CCD codes absent from `components.cif` or `components.cif.rdkit_mol.pkl`.
- Data preprocessing or training fails while resolving ligands or chemical components.

Actions:

1. Confirm `common/components.cif` and `common/components.cif.rdkit_mol.pkl` exist in the intended data root.
2. If structures are newer than the cache or contain custom ligands, plan a CCD cache refresh with the user because it can download and process CCD data.
3. If an updated `components.cif` already exists, plan a no-download cache rebuild instead of a network download.
4. Copy or move refreshed files into the data root's `common/` only when the user confirms that root should be updated.

## Malformed CIF or Empty Preprocessing Output

Symptoms:

- Preprocessing logs parser failures.
- Output CSV exists but has no rows.
- No `.pkl.gz` files appear in the bioassembly output directory.
- Structures are filtered out unexpectedly.

Actions:

- Confirm the input is a directory with top-level `*.cif`/`*.cif.gz` files or a `.txt` list of paths.
- Use `--distillation` for model-generated/custom CIFs where WeightedPDB filters and Assembly 1 expansion should not apply.
- Check whether failures are actually missing CCD-code problems.
- Reduce worker count when debugging to make logs easier to follow.
- Validate generated CSV schema before using it in training.

## Index CSV Schema Errors

Symptoms:

- Dataset sampling fails with missing columns.
- Chain rows have malformed chain-2 fields.
- Sampler weighting or mol-group behavior looks unexpected.

Actions:

1. Run `python scripts/check_training_data_layout.py DATA_ROOT --index-csv INDEX.csv`.
2. Ensure required columns exist: `type`, `pdb_id`, `cluster_id`, `entity_1_id`, `chain_1_id`, `mol_1_type`, `cluster_1_id`, `entity_2_id`, `chain_2_id`, `mol_2_type`, and `cluster_2_id`.
3. For `type=chain`, keep chain-2 columns present but empty.
4. Use molecular type values consistent with the data pipeline, such as `protein`, `nuc`, `ligand`, and `ions`.
5. Include `num_tokens` when using max/min token filters.

## W&B Login or Network Side Effects

Symptoms:

- Training prompts for W&B login, writes remote logs, or hangs in a non-interactive session.
- The user did not ask for remote experiment tracking.

Actions:

- Add `--use_wandb false` by default.
- If W&B is desired, confirm project name, credentials, network policy, and non-interactive behavior.
- Remember only rank 0 initializes W&B in DDP, but rank 0 can still block on authentication.

## CUDA Out of Memory

Symptoms:

- Training crashes during forward/backward or evaluation.
- OOM appears after increasing crop size, token limits, diffusion batch size, samples, or model depth.

Actions:

- Lower `--diffusion_batch_size` first for training memory pressure.
- Lower `--train_crop_size` or dataset `base_info.max_n_token` for large structures.
- Reduce evaluation frequency or evaluation dataset size while debugging.
- Use `--dtype bf16` on compatible GPUs rather than `fp32`.
- Switch kernels to portable `torch` only for debugging when optimized kernels fail; this may be slower and not always lower memory.
- Reduce model depth only when the user accepts changing model behavior.

## DDP and NCCL Issues

Symptoms:

- Multi-GPU training hangs at startup.
- Ranks disagree about visible devices.
- NCCL timeouts occur during dataloader startup or evaluation.

Actions:

- Launch with `torchrun --nproc_per_node N -m runner.train ...`, where `N` matches intended local GPUs.
- Check `CUDA_VISIBLE_DEVICES`, `LOCAL_RANK`, `MASTER_ADDR`, and `MASTER_PORT`.
- Increase `NCCL_TIMEOUT_SECOND` for slow initialization or slow data loading.
- Ensure shared data paths are visible to all ranks.
- Avoid multiple independent jobs writing the same output base and run-name prefix.

## Checkpoint Path or Load Failures

Symptoms:

- `FileNotFoundError` for `load_checkpoint_path` or `load_ema_checkpoint_path`.
- Strict loading fails after changing model family or architecture.
- Fine-tuning resumes with unexpected optimizer, scheduler, or step state.
- EMA checkpoint is requested while EMA is disabled or inconsistent.

Actions:

- Confirm checkpoint paths exist before launching training.
- Use both `--load_checkpoint_path` and `--load_ema_checkpoint_path` only when the source checkpoint policy expects EMA weights.
- For changed model architecture, consider `--load_strict false` only when model-specific config or task requirements justify it.
- Use `--load_params_only true` when starting a new fine-tune from weights without optimizer/scheduler state.
- Use skip-load flags only when intentionally controlling resume semantics.

## Config Override Typos

Symptoms:

- Assertions that an argument key does not start with `--`.
- A required config is `None`.
- List overrides are parsed as one wrong value.
- Boolean flags are ignored or parsed unexpectedly.

Actions:

- Pass every override as `--key value`; do not use valueless booleans.
- Use dot notation for nested keys.
- Use comma-separated list values with no spaces inside the value.
- Include all required base fields in direct `runner.train` commands.
- Use `scripts/build_training_command.py` to generate a syntactically safe no-run command, then adapt deliberately.

## Deepspeed, CUTLASS, and Pydantic Compatibility

Symptoms:

- Training exits with an assertion that `CUTLASS_PATH` is not set.
- Importing DeepSpeed fails with a Pydantic error containing `json_schema_input_schema`.
- The user selected `--triangle_attention deepspeed`.

Actions:

- Require `CUTLASS_PATH` to point at a compatible CUTLASS checkout before launch.
- Confirm CUDA toolkit, GPU, DeepSpeed, and Pydantic compatibility.
- For the `json_schema_input_schema` failure, repository tests document pinning Pydantic below 2.0 or updating DeepSpeed as likely fixes.
- If CUTLASS or dependency compatibility is uncertain, switch `--triangle_attention` to `cuequivariance` or `torch` depending on installed kernels and debugging needs.
- For fast layer norm failures, try `LAYERNORM_TYPE=torch`.

## Tiny Check vs Training-Scale Confusion

Symptoms:

- The user asks for a quick check but a proposed command would download data, preprocess CIFs, refresh CCD, or start training.
- Validation is blocked by missing GPU even though the task only needs data-root inspection.

Actions:

- Use bundled no-run scripts first.
- Treat Protenix custom preprocessing, CCD cache refresh, full-data download mode, MSA/template generation, and `runner.train` as heavy operations.
- Ask for explicit approval and prerequisites before moving from planning/checking to mutation, network, or GPU work.
