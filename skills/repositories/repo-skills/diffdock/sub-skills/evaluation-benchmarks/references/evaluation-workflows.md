# Evaluation Workflows

DiffDock benchmark evaluation uses `python -m evaluate`. It is script-style rather than an installed package entry point, so run it from a checkout or copied project context where the DiffDock modules and benchmark data are available. This reference is self-contained for planning and command construction; it does not require future agents to open the original repository files.

## Evaluation Entrypoint Shape

`evaluate.py` loads a score model, optionally loads a confidence model, builds a benchmark dataset, samples `samples_per_complex` poses per complex, computes RMSD and centroid metrics against ground truth ligand positions, and saves arrays under `--out_dir`.

Core flags:

| Concern | Main flags | Notes |
| --- | --- | --- |
| Config defaults | `--config default_inference_args.yaml` | The default config points at DiffDock-L score/confidence model dirs, checkpoint names, sampling temperatures, `inference_steps`, `actual_steps`, `samples_per_complex`, and noise settings. |
| Dataset selection | `--dataset pdbbind`, `--dataset moad`, `--dataset posebusters` | Any dataset other than `moad` is routed through the PDBBind loader with the dataset name passed through. |
| Data root | `--data_dir PATH` | Must match the dataset-specific layout described below. |
| Split | `--split_path PATH` or `--split test` | PDBBind/PoseBusters use `--split_path`; MOAD/DockGen uses `--split`. |
| ESM features | `--esm_embeddings_path PATH`, `--moad_esm_embeddings_sequences_path PATH` | Required when using cached language-model receptor features. MOAD additionally maps sequences through a FASTA-style sequence list. |
| Model checkpoints | `--model_dir DIR`, `--ckpt NAME`, `--confidence_model_dir DIR`, `--confidence_ckpt NAME` | Config supplies defaults; override when evaluating custom checkpoints. |
| Sampling | `--samples_per_complex N`, `--inference_steps N`, `--actual_steps N`, `--no_random`, `--no_final_step_noise`, temperature flags | Metrics such as top5/top10 only appear when enough samples are generated. |
| Compute | `--batch_size N`, `--num_workers N`, `--num_cpu N`, `--restrict_cpu`, `--tqdm` | `--restrict_cpu` disables CUDA via `CUDA_VISIBLE_DEVICES` and fixes several thread env vars to 16. |
| Outputs | `--out_dir DIR`, `--save_visualisation`, `--save_complexes`, `--complexes_save_path` | If `--out_dir` is omitted, evaluation writes below `inference_out_dir_not_specified/<run_name>`. `--save_visualisation` is default true in the parser. |
| GNINA | `--gnina_minimize`, `--gnina_path`, `--gnina_full_dock`, `--save_gnina_metrics`, `--gnina_poses_to_optimize`, `--gnina_autobox_add` | Requires an external GNINA executable and benchmark receptor paths compatible with DiffDock's naming assumptions. |

Use `scripts/build_evaluation_command.py` to generate commands safely without importing `evaluate.py` or launching a benchmark.

## PDBBind Benchmark

Dataset mode: `--dataset pdbbind`.

Expected layout:

- `--data_dir` points to a processed PDBBind root containing one folder per complex.
- Each complex folder is expected to contain a protein file named like `<complex>_<protein_file>.pdb`, defaulting to `<complex>_protein_processed.pdb`.
- Each complex folder is expected to contain a ligand file named like `<complex>_<ligand_file>.sdf` or `<complex>_<ligand_file>.mol2`, defaulting to `<complex>_ligand.sdf`.
- `--split_path` is a text file of complex identifiers.
- `--esm_embeddings_path` can be a `.pt` embedding map or an embedding directory recognized by the loader.

Canonical replicated-result pattern:

```bash
python -m evaluate --config default_inference_args.yaml --dataset pdbbind --data_dir data/PDBBind_processed/ --split_path data/splits/timesplit_test --esm_embeddings_path data/esm2_embeddings.pt --split test --chain_cutoff 10 --batch_size 10 --tqdm
```

Planning checks:

- Include `--split_path`; the historical README command repeats it, but one occurrence is sufficient.
- Keep `--chain_cutoff 10` when reproducing the published command pattern.
- Use `--limit_complexes` for smoke tests, but do not treat a limited run as benchmark evidence.
- Override `--protein_file` or `--ligand_file` only when the processed data uses non-default suffixes.

## DockGen / BindingMOAD Benchmark

Dataset mode: `--dataset moad`. The replicated-result command uses the BindingMOAD processed directory with the MOAD dataset loader; this is also the route for DiffDock-L DockGen-style evaluation from the provided processed MOAD data.

Expected layout:

- `--data_dir` points to the processed BindingMOAD root.
- The root needs MOAD metadata such as `new_cluster_to_ligands.pkl`.
- Receptors are loaded from `pdb_protein/<receptor>_protein.pdb`.
- Ligands are loaded from `pdb_ligand/<complex>.pdb` for non-train splits and `pdb_superligand/<complex>.pdb` for train-style handling.
- `--split test` selects the split key from the MOAD generalisation split metadata.
- `--moad_esm_embeddings_sequences_path` is required when `--esm_embeddings_path` is set; it maps receptor sequences to embedding entries.

Canonical replicated-result pattern:

```bash
python -m evaluate --config default_inference_args.yaml --dataset moad --data_dir data/BindingMOAD_2020_processed --split test --esm_embeddings_path data/moad_esm2_embeddings.pt --moad_esm_embeddings_sequences_path data/moad_sequences_to_id.fasta --unroll_clusters --min_ligand_size 2 --chain_cutoff 10 --batch_size 10 --tqdm
```

Planning checks:

- Do not pass `--split_path` for MOAD/DockGen unless a local wrapper expects it; the loader uses `--split` and internal split metadata.
- Keep `--unroll_clusters` for the replicated command shape.
- `--remove_pdbbind`, `--max_receptor_size`, and `--remove_promiscuous_targets` are filtering options; changing them changes the benchmark population.
- MOAD preprocessing creates receptor and ligand caches under `--cache_path`; stale cache names can preserve old preprocessing choices.

## PoseBusters Benchmark

Dataset mode: `--dataset posebusters`. The loader still uses the PDBBind class, but it activates PoseBusters-specific handling of alternative ground-truth ligand poses from `<complex>_ligands.sdf`.

Expected layout:

- `--data_dir` points to a processed PoseBusters benchmark root with one folder per complex id.
- `--split_path` points to a list of PoseBusters ids; the bundled source evidence includes `data/splits/posebusters_benchmark_set_ids.txt` with ids such as `5S8I_2LY`, `5SAK_ZRY`, and `5SB2_1K2`.
- Use `--protein_file protein` so the loader reads `<complex>_protein.pdb`.
- Use `--ligand_file ligands` so the loader reads `<complex>_ligands.sdf` or `.mol2` as the primary ligand file.
- `--esm_embeddings_path` should point to PoseBusters ESM embeddings.

Canonical replicated-result pattern:

```bash
python -m evaluate --config default_inference_args.yaml --dataset posebusters --data_dir data/posebusters_benchmark_set --split_path data/splits/posebusters_benchmark_set_ids.txt --esm_embeddings_path data/posebusters_ESM.pt --chain_cutoff 10 --batch_size 10 --protein_file protein --ligand_file ligands --tqdm
```

Planning checks:

- Missing `--protein_file protein` or `--ligand_file ligands` is a common cause of file-not-found failures for PoseBusters.
- PoseBusters uses multiple alternative ground-truth ligand poses when available and reports the minimum RMSD across them.
- Treat the split id file as benchmark membership evidence; changing it changes the evaluation set.

## Optional GNINA Post-Processing

GNINA is not a Python import inside DiffDock evaluation; DiffDock shells out to an external executable. Enabling `--gnina_minimize` writes predicted ligand SDF files, runs GNINA minimization or full docking, reads the minimized ligand, computes GNINA RMSDs, and records GNINA scores.

GNINA-related flags:

```bash
--gnina_minimize \
--gnina_path gnina \
--gnina_poses_to_optimize 1 \
--save_gnina_metrics
```

Add `--gnina_full_dock --gnina_autobox_add 4.0` only when intentionally running GNINA full docking instead of minimization.

Preflight checks:

- `--gnina_path` resolves to an executable in the run environment.
- The benchmark layout can produce receptor paths in the form `<folder>/<first-six-name-chars>_protein_chain_removed.pdb`; this naming is hard-coded in DiffDock's GNINA helper.
- `--out_dir` is writable and its `gnina_logs` subdirectory can be created before GNINA is invoked.
- GNINA failures fall back to the original DiffDock pose with GNINA score `0`, so zero GNINA scores may indicate tool failure rather than valid low affinity.

## Safe Command Builder Examples

PoseBusters command:

```bash
python sub-skills/evaluation-benchmarks/scripts/build_evaluation_command.py \
  --dataset posebusters \
  --data-dir data/posebusters_benchmark_set \
  --split-path data/splits/posebusters_benchmark_set_ids.txt \
  --esm-embeddings-path data/posebusters_ESM.pt \
  --protein-file protein \
  --ligand-file ligands \
  --batch-size 10 \
  --tqdm
```

MOAD/DockGen command with GNINA flags included but not executed:

```bash
python sub-skills/evaluation-benchmarks/scripts/build_evaluation_command.py \
  --dataset moad \
  --data-dir data/BindingMOAD_2020_processed \
  --split test \
  --esm-embeddings-path data/moad_esm2_embeddings.pt \
  --moad-esm-embeddings-sequences-path data/moad_sequences_to_id.fasta \
  --gnina-minimize \
  --gnina-path gnina \
  --save-gnina-metrics
```
