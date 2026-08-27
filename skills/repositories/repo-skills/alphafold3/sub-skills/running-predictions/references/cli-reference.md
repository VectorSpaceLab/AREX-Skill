# AlphaFold 3 CLI Reference

`run_alphafold.py` is the primary execution entry point. It uses Abseil flags; booleans accept forms such as `--run_inference=false`. Exactly one input selector is required, and `--output_dir` is required.

## Input and Output Selection

| Flag | Purpose | Notes |
| --- | --- | --- |
| `--json_path` | Path to one AlphaFold 3 input JSON file. | Mutually exclusive with `--input_dir`. Route JSON schema questions to `../input-preparation/`. |
| `--input_dir` | Directory containing input JSON files. | Mutually exclusive with `--json_path`; useful for batch runs. |
| `--output_dir` | Parent directory where job subdirectories/results are written. | Required even for help validation; make it writable before starting long runs. |
| `--force_output_dir` | Allow use of an existing non-empty output directory. | Useful for split data-pipeline/inference workflows that reuse a directory. |
| `--compress_large_output_files` | Compress large mmCIF and confidence JSON outputs with zstandard. | Embeddings/distograms are already stored compressed when requested. |

## Stage Control

| Flag | Purpose | Typical use |
| --- | --- | --- |
| `--run_data_pipeline` | Run genetic/template search and produce MSA/template-enriched inputs. | Default `true`; set `false` for inference-only on already enriched JSON. |
| `--run_inference` | Run featurisation and model inference on a GPU. | Default `true`; set `false` for CPU-only data-pipeline runs. |

At least one of `--run_data_pipeline` or `--run_inference` must be `true`.

## Model and Database Paths

| Flag | Purpose | Default behavior |
| --- | --- | --- |
| `--model_dir` | Directory containing model parameters. | Defaults to a user home model directory in the runner; pass explicitly in reproducible commands. |
| `--db_dir` | Directory containing public databases; can be repeated. | Database path flags using `${DB_DIR}` are resolved by searching each `--db_dir` in order. |
| `--small_bfd_database_path` | Protein MSA search database. | Default `${DB_DIR}/bfd-first_non_consensus_sequences.fasta`. |
| `--mgnify_database_path` | Protein MSA search database. | Default `${DB_DIR}/mgy_clusters_2022_05.fa`. |
| `--uniprot_cluster_annot_database_path` | Protein paired-MSA database. | Default `${DB_DIR}/uniprot_all_2021_04.fa`. |
| `--uniref90_database_path` | MSA/profile database used for template search. | Default `${DB_DIR}/uniref90_2022_05.fa`. |
| `--ntrna_database_path` | RNA MSA search database. | Default `${DB_DIR}/nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta`. |
| `--rfam_database_path` | RNA MSA search database. | Default `${DB_DIR}/rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta`. |
| `--rna_central_database_path` | RNA MSA search database. | Default `${DB_DIR}/rnacentral_active_seq_id_90_cov_80_linclust.fasta`. |
| `--pdb_database_path` | PDB mmCIF directory for templates. | Default `${DB_DIR}/mmcif_files`. |
| `--seqres_database_path` | PDB sequence FASTA for templates. | Default `${DB_DIR}/pdb_seqres_2022_09_28.fasta`. |

## Sharded Database Z-Values

When using sharded database specs such as `database.fasta@16`, set the matching Z-value flag so E-values are scaled across the full database rather than a shard.

| Database flag | Z-value flag | Value type |
| --- | --- | --- |
| `--small_bfd_database_path` | `--small_bfd_z_value` | integer sequence count |
| `--mgnify_database_path` | `--mgnify_z_value` | integer sequence count |
| `--uniprot_cluster_annot_database_path` | `--uniprot_cluster_annot_z_value` | integer sequence count |
| `--uniref90_database_path` | `--uniref90_z_value` | integer sequence count |
| `--ntrna_database_path` | `--ntrna_z_value` | float megabase count |
| `--rfam_database_path` | `--rfam_z_value` | float megabase count |
| `--rna_central_database_path` | `--rna_central_z_value` | float megabase count |

## HMMER Binary Flags

The data pipeline discovers these binaries with `shutil.which()` by default. Pass explicit paths when running outside the Docker image, inside minimal containers, or on systems with multiple HMMER installs.

| Flag | Binary |
| --- | --- |
| `--jackhmmer_binary_path` | `jackhmmer` |
| `--nhmmer_binary_path` | `nhmmer` |
| `--hmmalign_binary_path` | `hmmalign` |
| `--hmmsearch_binary_path` | `hmmsearch` |
| `--hmmbuild_binary_path` | `hmmbuild` |

## Data Pipeline Performance and Semantics

| Flag | Purpose | Notes |
| --- | --- | --- |
| `--jackhmmer_n_cpu` | CPUs per Jackhmmer process. | Defaults to up to 8; more than 8 often gives little per-process speedup. |
| `--jackhmmer_max_parallel_shards` | Max Jackhmmer shards searched in parallel. | Only applies to sharded databases. |
| `--nhmmer_n_cpu` | CPUs per Nhmmer process. | Defaults to up to 8. |
| `--nhmmer_max_parallel_shards` | Max Nhmmer shards searched in parallel. | Only applies to sharded databases. |
| `--resolve_msa_overlaps` | Deduplicate unpaired MSA against paired MSA. | Set `false` when custom paired MSA encoded in unpaired fields must remain exact. |
| `--max_template_date` | Latest template release date, `YYYY-MM-DD`. | Also controls whether CCD model coordinates may be used as fallback for older components. |
| `--conformer_max_iterations` | Override RDKit conformer search iterations. | Leave unset unless troubleshooting ligand conformer generation. |
| `--fix_standalone_glycans` | Remove standalone leaving atoms from glycan ligands. | Changes behavior away from the training/evaluation regime; use deliberately. |

## Inference Performance

| Flag | Purpose | Notes |
| --- | --- | --- |
| `--gpu_device` | Zero-based GPU index used for inference. | If `CUDA_VISIBLE_DEVICES` filters GPUs, this index is after filtering. |
| `--buckets` | Comma-separated token-size compilation buckets. | Default includes `256` through `5120`; add larger buckets to avoid repeated recompilation for similar large inputs. |
| `--flash_attention_implementation` | Attention backend: `triton`, `cudnn`, or `xla`. | `triton` is default and fastest on supported Ampere-or-newer GPUs; use `xla` for older/portable devices. |
| `--jax_compilation_cache_dir` | Persistent JAX compilation cache directory. | Reuses compilations across runs when cache storage is available. |
| `--num_recycles` | Number of inference recycles. | Default `10`; lower values trade accuracy for speed. |
| `--num_diffusion_samples` | Number of diffusion samples per seed. | Default `5`; increasing raises runtime and output volume. |
| `--num_seeds` | Expand a single input seed into sequential random seeds. | Requires the input JSON to contain exactly one seed. |

## Optional Model Outputs

| Flag | Purpose | Caveat |
| --- | --- | --- |
| `--save_embeddings` | Save final trunk single and pair embeddings. | Very large: single embeddings scale with tokens, pair embeddings scale with tokens squared. |
| `--save_distogram` | Save final distogram. | Very large: scales with tokens squared. |

## Command Builder

Print a Docker command:

```bash
python scripts/build_run_command.py \
  --mode docker \
  --json_path /host/input/fold_input.json \
  --output_dir /host/output \
  --model_dir /host/models \
  --db_dir /host/public_databases
```

Print an inference-only local command using a precomputed JSON:

```bash
python scripts/build_run_command.py \
  --mode local \
  --json_path enriched_input.json \
  --output_dir af_output \
  --model_dir model_parameters \
  --no-run_data_pipeline \
  --run_inference
```
