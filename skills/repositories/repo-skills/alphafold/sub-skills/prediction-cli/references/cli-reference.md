# Local Prediction CLI Reference

AlphaFold 2.3.2 exposes the installed console script `run_alphafold`, which invokes `run_alphafold:main`. This reference covers the direct installed Python CLI only; Docker setup and data downloads are owned by `../docker-and-data-setup/`.

## Entry Point

Use this form when the package and external alignment binaries are available in the execution environment:

```bash
run_alphafold --fasta_paths=target.fasta ...
```

The CLI is an `absl.flags` application. It rejects positional arguments and validates several flag combinations before building the data pipeline or loading model parameters.

## Required Core Flags

These flags are required by the direct CLI for every prediction command:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--fasta_paths` | Comma-separated FASTA files | Each file is folded sequentially; each FASTA stem must be unique. |
| `--output_dir` | Directory for target subdirectories | Must be writable; each FASTA stem becomes `output_dir/<target_name>/`. |
| `--data_dir` | Directory containing AlphaFold data | Used for model parameters; direct CLI does not derive database flags from it. |
| `--max_template_date` | Latest allowed template release date | Use `YYYY-MM-DD`; important for historical benchmarks. |
| `--uniref90_database_path` | UniRef90 FASTA | Required for JackHMMER. |
| `--mgnify_database_path` | MGnify FASTA | Required for JackHMMER. |
| `--template_mmcif_dir` | Template mmCIF directory | Directory containing files named like `<pdb_id>.cif`. |
| `--obsolete_pdbs_path` | Obsolete PDB mapping file | Typically from the PDB mmCIF data directory. |
| `--use_gpu_relax` | Whether Amber relaxation uses GPU | Must be passed as true or false; details route to `../relaxation/`. |

If the external tools are not discoverable on `PATH`, also pass the binary path flags: `--jackhmmer_binary_path`, `--hhblits_binary_path`, `--hhsearch_binary_path`, `--hmmsearch_binary_path`, `--hmmbuild_binary_path`, and `--kalign_binary_path`.

## Presets and Conditional Database Flags

The CLI enforces `db_preset` and `model_preset` compatibility exactly; extra incompatible database flags are errors, not ignored.

| Choice | Required flags | Must not be set |
| --- | --- | --- |
| `--db_preset=full_dbs` | `--bfd_database_path`, `--uniref30_database_path` | `--small_bfd_database_path` |
| `--db_preset=reduced_dbs` | `--small_bfd_database_path` | `--bfd_database_path`, `--uniref30_database_path` |
| `--model_preset=monomer` | `--pdb70_database_path` | `--pdb_seqres_database_path`, `--uniprot_database_path` |
| `--model_preset=monomer_casp14` | `--pdb70_database_path` | `--pdb_seqres_database_path`, `--uniprot_database_path` |
| `--model_preset=monomer_ptm` | `--pdb70_database_path` | `--pdb_seqres_database_path`, `--uniprot_database_path` |
| `--model_preset=multimer` | `--pdb_seqres_database_path`, `--uniprot_database_path` | `--pdb70_database_path` |

### Model Presets

- `monomer`: five CASP14-style monomer models without extra ensembling.
- `monomer_casp14`: same five monomer model names with `num_ensemble=8`; slower and primarily for CASP14-style reproducibility.
- `monomer_ptm`: five pTM monomer models that write PAE data when present.
- `multimer`: five AlphaFold-Multimer v3 models; with default `--num_multimer_predictions_per_model=5`, this creates 25 model-runner entries.

### Database Presets

- `full_dbs`: uses full BFD and UniRef30 in addition to UniRef90 and MGnify.
- `reduced_dbs`: uses small BFD instead of BFD and UniRef30; lower hardware and disk requirements.

## Standard Data Layout Paths

The direct CLI expects explicit database paths. When using the standard AlphaFold data layout, construct them from the data directory like this:

| Flag | Standard relative path |
| --- | --- |
| `--uniref90_database_path` | `uniref90/uniref90.fasta` |
| `--mgnify_database_path` | `mgnify/mgy_clusters_2022_05.fa` |
| `--bfd_database_path` | `bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt` |
| `--small_bfd_database_path` | `small_bfd/bfd-first_non_consensus_sequences.fasta` |
| `--uniref30_database_path` | `uniref30/UniRef30_2021_03` |
| `--uniprot_database_path` | `uniprot/uniprot.fasta` |
| `--pdb70_database_path` | `pdb70/pdb70` |
| `--pdb_seqres_database_path` | `pdb_seqres/pdb_seqres.txt` |
| `--template_mmcif_dir` | `pdb_mmcif/mmcif_files` |
| `--obsolete_pdbs_path` | `pdb_mmcif/obsolete.dat` |

Some HH-suite database values are path prefixes rather than a single ordinary file. Validate them by checking either the exact path or files beginning with that prefix.

## Execution and Reuse Flags

| Flag | Default | Guidance |
| --- | --- | --- |
| `--models_to_relax` | `best` | `best` relaxes only the top-ranked model, `all` relaxes every model, and `none` skips relaxation and `relax_metrics.json`. |
| `--num_multimer_predictions_per_model` | `5` | Only used for `--model_preset=multimer`; set to `1` for faster lower-cost multimer exploration. |
| `--benchmark` | `false` | Runs a second model evaluation so `timings.json` can include prediction time excluding JAX compile time. |
| `--use_precomputed_msas` | `false` | Reuses existing MSA files under the same output target directory; no sequence/database/config compatibility check is performed. |
| `--random_seed` | random | Controls data-pipeline and per-model seed derivation, but does not guarantee identical results across hardware or data changes. |
| `--jackhmmer_n_cpu` | up to `8` | CPU count for JackHMMER; values above 8 provide little additional speedup according to the CLI help. |
| `--hmmsearch_n_cpu` | up to `8` | CPU count for HMMsearch, used for multimer template search. |
| `--hhsearch_n_cpu` | up to `8` | CPU count for HHsearch, used for monomer template search. |

## Output Directory Contract

For each FASTA path, the target name is `Path(fasta_path).stem`. The CLI creates `output_dir/<target_name>/` and writes artifacts for that target.

Expected target files include:

- `features.pkl`: input feature arrays passed to models.
- `msas/`: MSA outputs from the data pipeline, and the cache location for `--use_precomputed_msas=true`.
- `result_<model_name>.pkl`: raw model outputs as NumPy-backed dictionaries.
- `confidence_<model_name>.json`: per-residue pLDDT confidence JSON.
- `pae_<model_name>.json`: PAE JSON when the selected model output includes PAE.
- `unrelaxed_<model_name>.pdb` and `unrelaxed_<model_name>.cif`: unrelaxed structures with pLDDT stored in PDB B-factors.
- `relaxed_<model_name>.pdb` and `relaxed_<model_name>.cif`: present for relaxed models only.
- `ranked_<n>.pdb` and `ranked_<n>.cif`: structures sorted by model confidence.
- `ranking_debug.json`: confidence values and ranked model order; multimer-style predictions use the `iptm+ptm` label when available.
- `timings.json`: feature, prediction, optional benchmark, and optional relaxation timings.
- `relax_metrics.json`: present only when `--models_to_relax` is not `none`.

Use `../outputs-and-confidence/` to interpret confidence, PDB, mmCIF, and JSON contents after the run.
