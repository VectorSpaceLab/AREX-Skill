# Prediction CLI Workflows

These workflows build direct `run_alphafold` commands. Replace `DATA_DIR`, `OUT_DIR`, and FASTA paths with user-owned locations. Do not run these commands during skill verification; use `scripts/check_prediction_inputs.py` first.

## Validate Before Running

Run the bundled checker before proposing a full inference command:

```bash
python scripts/check_prediction_inputs.py \
  --fasta_paths=target.fasta \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=monomer \
  --db_preset=reduced_dbs \
  --use_gpu_relax=false \
  --infer_database_paths
```

The checker never imports AlphaFold, runs external MSA tools, loads model weights, starts JAX, or performs inference.

## Monomer with Reduced Databases

Use this for a faster monomer run with lower database requirements:

```bash
run_alphafold \
  --fasta_paths=monomer.fasta \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=monomer \
  --db_preset=reduced_dbs \
  --uniref90_database_path="$DATA_DIR/uniref90/uniref90.fasta" \
  --mgnify_database_path="$DATA_DIR/mgnify/mgy_clusters_2022_05.fa" \
  --small_bfd_database_path="$DATA_DIR/small_bfd/bfd-first_non_consensus_sequences.fasta" \
  --pdb70_database_path="$DATA_DIR/pdb70/pdb70" \
  --template_mmcif_dir="$DATA_DIR/pdb_mmcif/mmcif_files" \
  --obsolete_pdbs_path="$DATA_DIR/pdb_mmcif/obsolete.dat" \
  --models_to_relax=none \
  --use_gpu_relax=false
```

Do not include `--bfd_database_path` or `--uniref30_database_path` with `--db_preset=reduced_dbs`.

## Monomer pTM with Full Databases

Use `monomer_ptm` when the user wants PAE/pTM-style confidence outputs for a monomer:

```bash
run_alphafold \
  --fasta_paths=target.fasta \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=monomer_ptm \
  --db_preset=full_dbs \
  --uniref90_database_path="$DATA_DIR/uniref90/uniref90.fasta" \
  --mgnify_database_path="$DATA_DIR/mgnify/mgy_clusters_2022_05.fa" \
  --bfd_database_path="$DATA_DIR/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt" \
  --uniref30_database_path="$DATA_DIR/uniref30/UniRef30_2021_03" \
  --pdb70_database_path="$DATA_DIR/pdb70/pdb70" \
  --template_mmcif_dir="$DATA_DIR/pdb_mmcif/mmcif_files" \
  --obsolete_pdbs_path="$DATA_DIR/pdb_mmcif/obsolete.dat" \
  --models_to_relax=best \
  --use_gpu_relax=true
```

Do not include `--pdb_seqres_database_path` or `--uniprot_database_path` for monomer presets.

## Multimer with Full Databases

Use `multimer` for complexes represented as multi-sequence FASTA files:

```bash
run_alphafold \
  --fasta_paths=complex.fasta \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=multimer \
  --db_preset=full_dbs \
  --uniref90_database_path="$DATA_DIR/uniref90/uniref90.fasta" \
  --mgnify_database_path="$DATA_DIR/mgnify/mgy_clusters_2022_05.fa" \
  --bfd_database_path="$DATA_DIR/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt" \
  --uniref30_database_path="$DATA_DIR/uniref30/UniRef30_2021_03" \
  --pdb_seqres_database_path="$DATA_DIR/pdb_seqres/pdb_seqres.txt" \
  --uniprot_database_path="$DATA_DIR/uniprot/uniprot.fasta" \
  --template_mmcif_dir="$DATA_DIR/pdb_mmcif/mmcif_files" \
  --obsolete_pdbs_path="$DATA_DIR/pdb_mmcif/obsolete.dat" \
  --num_multimer_predictions_per_model=1 \
  --models_to_relax=none \
  --use_gpu_relax=false
```

Do not include `--pdb70_database_path` for `--model_preset=multimer`. The default `--num_multimer_predictions_per_model=5` runs five seeds per model; setting it to `1` reduces runtime for exploratory work.

## Multiple FASTA Files

Pass multiple FASTA files as a comma-separated list to fold them sequentially:

```bash
run_alphafold --fasta_paths=target_a.fasta,target_b.fasta ...
```

Every FASTA stem must be unique. `target.fasta` and `other/target.fa` conflict because both create the `target` output subdirectory.

## Reusing Precomputed MSAs

Use MSA reuse only when the FASTA sequence, database versions, and relevant data-pipeline flags are intentionally unchanged:

```bash
run_alphafold \
  --fasta_paths=target.fasta \
  --output_dir="$OUT_DIR" \
  --use_precomputed_msas=true \
  ...
```

The existing MSA files are looked up under `OUT_DIR/<target_name>/msas/`. AlphaFold does not verify that cached MSAs match the current sequence, database, model preset, or template settings.

## Random Seeds and Benchmark Timing

- Add `--random_seed=<integer>` when comparing command variants; the CLI derives each model seed from the base seed and model index.
- Do not promise bitwise determinism. GPU inference, software versions, hardware, and changed input databases can still alter results.
- Add `--benchmark=true` only when the user wants an extra model call to measure prediction time excluding JAX compilation; this increases runtime and affects `timings.json` interpretation.

## Convert a Docker Prediction Command to Direct CLI

A Docker-oriented plan with FASTA, data, output, model preset, and database preset becomes a direct command by replacing container mounts with host paths, replacing Docker-only flags with direct CLI flags, and adding explicit database paths:

```bash
run_alphafold \
  --fasta_paths=your_protein.fasta \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=monomer \
  --db_preset=reduced_dbs \
  --uniref90_database_path="$DATA_DIR/uniref90/uniref90.fasta" \
  --mgnify_database_path="$DATA_DIR/mgnify/mgy_clusters_2022_05.fa" \
  --small_bfd_database_path="$DATA_DIR/small_bfd/bfd-first_non_consensus_sequences.fasta" \
  --pdb70_database_path="$DATA_DIR/pdb70/pdb70" \
  --template_mmcif_dir="$DATA_DIR/pdb_mmcif/mmcif_files" \
  --obsolete_pdbs_path="$DATA_DIR/pdb_mmcif/obsolete.dat" \
  --models_to_relax=none \
  --use_gpu_relax=false
```

The direct command does not accept Docker-only flags such as `--gpu_devices`, `--use_gpu`, `--enable_gpu_relax`, `--docker_image_name`, or `--docker_user`.
