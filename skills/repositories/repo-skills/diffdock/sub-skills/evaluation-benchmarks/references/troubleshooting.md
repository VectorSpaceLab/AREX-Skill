# Troubleshooting Evaluation Benchmarks

Use this checklist before running an expensive DiffDock evaluation and when interpreting failed or suspicious benchmark outputs.

## Dependency And Import Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: torch`, `torch_geometric`, `rdkit`, `wandb`, or model modules | `evaluate.py` imports the heavy ML/chemistry stack at module import time. | Prepare an environment with Torch, PyG, RDKit, W&B, and DiffDock dependencies before running evaluation. Use the command builder for planning when the stack is unavailable. |
| `python -m spyrmsd --help` fails before help text | The vendored CLI imports package dependencies before parsing. | Install/check NumPy and then RDKit or OpenBabel for molecule loading; use `inspect_spyrmsd_cli.py` to report the exact failure safely. |
| `app.main` import fails with `mol_viewer` from outside `app/` | The Gradio app uses sibling imports and is unrelated to evaluation. | Do not use app imports to validate benchmark evaluation; validate `utils.parsing`, `spyrmsd`, and command construction separately. |
| CUDA libraries or PyG extensions fail to load | Torch/PyG build does not match CUDA/driver/runtime. | Rebuild or reinstall matching Torch/PyG wheels; for CPU-only planning add `--restrict_cpu`, but expect full benchmarks to be slower. |

## Dataset Layout Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Folder not found <complex>` for PDBBind/PoseBusters | `--data_dir` does not contain folders named by `--split_path`. | Check that `--data_dir` points to the processed benchmark root and the split file ids match folder names. |
| Protein file not found | Wrong `--protein_file` suffix or dataset layout mismatch. | PDBBind defaults to `protein_processed`; PoseBusters uses `--protein_file protein`. |
| Ligand file not found or cannot be sanitized | Wrong `--ligand_file` suffix or invalid ligand file. | PDBBind defaults to `ligand`; PoseBusters uses `--ligand_file ligands`; confirm `.sdf` or `.mol2` exists. |
| `new_cluster_to_ligands.pkl` missing for MOAD/DockGen | `--dataset moad` expects processed BindingMOAD metadata. | Point `--data_dir` at a processed BindingMOAD root, not a PDBBind- or PoseBusters-style folder tree. |
| `MOAD_generalisation_splits.pkl` missing | MOAD loader expects split metadata under `data/splits` relative to the run context. | Ensure the benchmark context includes the split metadata; do not substitute an arbitrary text split path for MOAD. |
| PoseBusters alternative poses missing | `<complex>_ligands.sdf` is absent or unreadable. | Use `--ligand_file ligands` and a processed PoseBusters root that includes all ligand poses. |

## Split And Benchmark Mode Mistakes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| PDBBind command has no complexes | Missing or wrong `--split_path`. | Use a text split file such as `data/splits/timesplit_test`; avoid duplicated split flags but keep one valid path. |
| MOAD/DockGen command ignores `--split_path` | MOAD loader uses `--split`, not `--split_path`. | Use `--split test` for the replicated DockGen/MOAD command pattern. |
| Results cannot be compared to published benchmark | Filters changed the population. | Record and justify any use of `--limit_complexes`, `--remove_pdbbind`, `--min_ligand_size`, `--max_receptor_size`, `--remove_promiscuous_targets`, or custom split files. |
| Top5/top10 metrics absent | `--samples_per_complex` is below 5 or 10. | Use at least 10 samples per complex for the default DiffDock-L replicated-result pattern. |

## ESM Embedding Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| ESM embeddings path does not exist | `--esm_embeddings_path` points to a missing `.pt` file or directory. | Generate/cache embeddings before evaluation or remove the flag only if evaluating a model/config that does not require them. |
| MOAD sequence lookup fails | `--moad_esm_embeddings_sequences_path` missing or mismatched. | Provide the sequence list used to build the MOAD embedding `.pt` map. |
| Unexpected cache reuse after changing embeddings | Dataset cache key may not distinguish enough input details for the change. | Use a fresh `--cache_path` when changing benchmark layout, ESM paths, graph settings, or file suffixes. |

## Model And Checkpoint Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `model_parameters.yml` missing | `--model_dir` or `--confidence_model_dir` points to the wrong directory. | Point each model dir at a directory containing `model_parameters.yml` and the chosen checkpoint. |
| Checkpoint file missing | `--ckpt` or `--confidence_ckpt` does not exist inside the model dir. | Use the checkpoint names from the config or list the model directory before running. |
| State dict mismatch | Checkpoint and model parameters do not match. | Keep score/confidence checkpoints paired with the corresponding `model_parameters.yml`; do not mix incompatible training runs. |
| Confidence complex skipped | Confidence dataset did not contain that complex and could not reuse the original model cache. | Check confidence-model cache settings and dataset preprocessing; compare skip counts before trusting filtered metrics. |

## GNINA Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| GNINA command not found | `--gnina_path` does not resolve to an executable. | Install GNINA or pass an explicit executable path; verify separately before enabling `--gnina_minimize`. |
| GNINA logs directory error | DiffDock opens a file below `out_dir/gnina_logs` but does not robustly create all directories in every path. | Create `--out_dir` and `--out_dir/gnina_logs` before the run when enabling GNINA. |
| GNINA receptor path missing | The helper expects `<folder>/<name[:6]>_protein_chain_removed.pdb`. | Confirm the benchmark folder and receptor naming match this convention before using GNINA. |
| GNINA scores are all `0` | GNINA failed or `CNNscore` could not be parsed. | Inspect GNINA logs and output SDF properties; do not interpret zero scores as valid affinity without confirming successful GNINA output. |
| `gnina_metrics.pkl` missing | `--save_gnina_metrics` was not enabled or the run failed before saving. | Add `--save_gnina_metrics` only when GNINA output is needed and the binary/layout are verified. |

## Cache And Preprocessing Problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Old file suffixes or graph settings seem to persist | Dataset preprocessing cache reused earlier choices. | Change or delete `--cache_path` for a fresh preprocessing pass. |
| Multiprocessing stalls or file descriptor errors | Dataset preprocessing opens many files and workers. | Reduce `--num_workers`; DiffDock raises the open-file soft limit but system limits can still bite. |
| RDKit conformer/matching failures | Ligand sanitization, torsion matching, or geometry generation failed. | Try `--skip_matching` only when the benchmark protocol permits it; otherwise fix ligand inputs. |

## GPU, CPU, And OOM Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| CUDA out of memory | Batch size, model size, receptor size, or sample count too high. | Lower `--batch_size`, use `--limit_complexes` for debugging, or filter receptor size only if changing the benchmark population is acceptable. |
| Run becomes extremely slow | CPU-only path, large receptor graphs, or GNINA full docking. | Confirm GPU availability for full benchmarks; reserve `--restrict_cpu` for debugging or environments without CUDA. |
| Failures recover after batch size reduction | Evaluation halves batch size on exceptions while retrying a complex. | Treat repeated failures as a data/model issue even if some complexes recover. |

## Result Interpretation Problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `10000` RMSD values | Complex failed after retry attempts. | Count failures and inspect per-complex error logs before reporting aggregate metrics. |
| `min_rmsds_below_2` is high but `filtered_rmsds_below_2` is low | Good poses were sampled but confidence did not rank them first. | Report both sampling success and confidence-ranking success; do not conflate them. |
| `rmsds_below_2` is much lower than `min_rmsds_below_2` | Only a minority of samples per complex are accurate. | Use top5/top10 and confidence-filtered metrics to explain practical pose selection. |
| GNINA improves score but worsens RMSD | GNINA score optimizes its own scoring function, not RMSD to crystal pose. | Compare `gnina_score.npy` and `gnina_rmsds.npy`; do not assume higher GNINA score means lower RMSD. |
| Visualized files absent or too many | `--save_visualisation` behavior and sample count. | The parser default is true; disable or redirect outputs in large benchmark runs if storage is a concern. |

## Safe Native Candidate Classification

- `evaluate.py` parser/source inspection is safe and useful for command planning, but importing it requires heavy optional dependencies.
- `python -m spyrmsd --help` is a safe native check only when the current Python has the needed package imports; otherwise record the import failure as environment evidence.
- The PoseBusters id split file is safe to inspect and useful for command validation.
- README replicated-result commands are benchmark candidates but should be skipped as expensive until data, checkpoints, ESM embeddings, and compute budget are confirmed.
