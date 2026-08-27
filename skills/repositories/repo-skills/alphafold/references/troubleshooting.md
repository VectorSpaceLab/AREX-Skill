# Cross-Cutting Troubleshooting

Use this reference when an AlphaFold task fails before it is clearly owned by a single sub-skill.

## Install and Import

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: alphafold` | Package is not installed in the active environment | Install the package, then run `python scripts/check_install.py --check run_alphafold`. |
| `jaxlib version ... incompatible with jax version ...` | JAX and JAXLIB pins drifted during dependency resolution | Align JAXLIB with the installed JAX version; for AlphaFold 2.3.2 evidence, `jax==0.4.26` pairs with `jaxlib==0.4.26`. Preserve AlphaFold's NumPy and TensorFlow pins. |
| TensorFlow complains about NumPy or `ml-dtypes` | A backend repair upgraded shared dependencies past TensorFlow/AlphaFold constraints | Re-pin to the package constraints before testing model imports. |
| `run_alphafold` command not found | Console script entry point is not on `PATH` | Run with the environment's Python scripts directory on `PATH`, or reinstall the package in the intended environment. |
| OpenMM/PDBFixer import errors | Relaxation dependencies are missing or incompatible | Route to `sub-skills/relaxation/` and decide whether relaxation is required. |

## Data and External Tools

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Missing `jackhmmer`, `hhblits`, `hhsearch`, `hmmsearch`, `hmmbuild`, or `kalign` | Direct local pipeline cannot find external alignment/template binaries | Provide explicit binary path flags or use the documented container path. |
| Missing database path errors | `db_preset` or `model_preset` requires paths that were omitted or not downloaded | Run the prediction validator in `sub-skills/prediction-cli/scripts/check_prediction_inputs.py` or Docker/data planner. |
| Full database run points at `small_bfd` | `db_preset` mismatch | Use `reduced_dbs` with small BFD, or use `full_dbs` with BFD plus UniRef30. |
| Multimer run uses `pdb70` but lacks UniProt/PDB SeqRes | `model_preset=multimer` uses multimer database paths | Switch database flags or model preset to match the task. |
| Cached MSAs reused after sequence or data changes | `--use_precomputed_msas=true` trusts files under the output target's `msas/` directory | Disable MSA reuse or clear stale `msas/` when sequence, database, preset, or template cutoff changes. |

## Docker and Hardware

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Docker build is unexpectedly huge or slow | Data directory is inside the project/build context | Move data outside the project root and rerun the Docker/data setup planner. |
| Docker cannot see GPUs | NVIDIA Container Toolkit, driver, or Docker `--gpus` configuration is missing | Run a user-supervised `nvidia-smi` container smoke check and route to `docker-and-data-setup`. |
| JAX OOM or long-protein memory failure | Sequence length, MSA depth, model preset, or GPU memory is too large | Consider reduced databases, fewer sequences, CPU/GPU memory flags, or more capable hardware; do not promise deterministic success. |
| Relaxation fails on GPU but prediction succeeded | OpenMM CUDA platform instability or dependency mismatch | Switch `use_gpu_relax=false` or `models_to_relax=none` and route to `relaxation`. |

## Outputs and Confidence

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Target folder lacks ranked PDB/mmCIF files | Prediction stopped before model output or write stage | Inspect logs/timings and route to `prediction-cli` before interpreting confidence. |
| PAE JSON is absent | Model output did not include predicted aligned error | Use pTM/multimer-capable presets when PAE is needed; route to `outputs-and-confidence`. |
| pLDDT categories look low for a region | Local disorder or uncertain domain placement | Use the confidence JSON helper and PAE reference before drawing biological conclusions. |

## Safety Boundary

Do not use routine verification to run full prediction, database downloads, Docker builds, Docker runs, BigQuery/GCS bulk access, or OpenMM minimization. Use dry-run helpers and request explicit user approval for expensive or external operations.
