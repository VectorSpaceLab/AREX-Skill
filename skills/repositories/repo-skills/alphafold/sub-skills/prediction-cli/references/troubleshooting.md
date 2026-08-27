# Prediction CLI Troubleshooting

Use this guide for failures before or around local `run_alphafold` execution. For Docker runtime, mounts, data downloads, output interpretation, or relaxation internals, route to the sibling sub-skill named in `SKILL.md`.

## Fast Diagnosis Table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `fasta_paths`, `output_dir`, or `data_dir` reported missing | Required core flag omitted | Add every required core flag from `cli-reference.md`; direct CLI has fewer defaults than the Docker wrapper. |
| `small_bfd_database_path must be set` | `--db_preset=reduced_dbs` without small BFD path | Add `--small_bfd_database_path` and remove `--bfd_database_path` / `--uniref30_database_path`. |
| `bfd_database_path must be set` or `uniref30_database_path must be set` | `--db_preset=full_dbs` without full database paths | Add BFD and UniRef30 path prefixes; remove `--small_bfd_database_path`. |
| `pdb70_database_path must not be set` | Multimer command includes monomer template DB | Remove `--pdb70_database_path`; add `--pdb_seqres_database_path` and `--uniprot_database_path`. |
| `pdb_seqres_database_path must be set` or `uniprot_database_path must be set` | Multimer command missing multimer-only databases | Add PDB SeqRes full file path and UniProt FASTA. |
| `All FASTA paths must have a unique basename` | Two FASTA paths share the same stem | Rename one FASTA or put unique filenames in the comma-separated list. |
| External binary path error | HMMER, HH-suite, or Kalign tool missing from `PATH` | Install the external tool or pass its `--*_binary_path` flag explicitly. |
| Cached MSA run gives surprising result | `--use_precomputed_msas=true` reused stale MSAs | Re-run without MSA reuse or ensure FASTA, database versions, and data-pipeline flags are unchanged. |
| No `relax_metrics.json` | `--models_to_relax=none` | This is expected when relaxation is skipped. |
| Only `ranked_0` is relaxed | `--models_to_relax=best` | Expected default; use `all` for every model or `none` to skip relaxation. |
| `timings.json` includes compile-heavy prediction time | JAX compilation included in first model call | Use `--benchmark=true` only if the user accepts a second prediction call for compile-excluded timing. |
| Output directory failure | Missing parent, not writable, or target directory conflicts | Create/write-check `--output_dir`; inspect `output_dir/<fasta_stem>/` before reusing it. |
| GPU memory or process killed | Long sequence, many chains, high MSA/template sizes, or multimer seeds | Reduce input size/chains when possible, lower multimer seeds, skip relaxation, or move to larger GPU resources. |

## Multimer Missing UniProt Plus Duplicate FASTA Basenames

If a multimer run uses FASTA paths such as `case/complex.fasta,rerun/complex.fa` and omits `--uniprot_database_path`, there are two independent blockers:

1. The duplicate stems both map to `output_dir/complex/`; rename one file or pass only one target per output stem.
2. `--model_preset=multimer` requires `--uniprot_database_path` and `--pdb_seqres_database_path`, and must not include `--pdb70_database_path`.

Validate with:

```bash
python scripts/check_prediction_inputs.py \
  --fasta_paths=case/complex.fasta,rerun/complex.fa \
  --data_dir="$DATA_DIR" \
  --output_dir="$OUT_DIR" \
  --max_template_date=2022-01-01 \
  --model_preset=multimer \
  --db_preset=full_dbs \
  --use_gpu_relax=false
```

Then repair the filenames and add the multimer database paths before running inference.

## Precomputed MSA Caveat

`--use_precomputed_msas=true` reads from the same target output directory used by a prior run. It is useful for comparing model presets or relaxation choices after MSA generation, but unsafe when any of these changed:

- FASTA sequence or chain composition.
- Database versions or `db_preset`.
- Template date or template database content.
- Output directory target stem.
- Monomer vs multimer data pipeline.

If uncertain, disable MSA reuse and regenerate the MSA files.

## Random Seed Caveat

Passing `--random_seed` improves comparability across command variants, but does not guarantee deterministic predictions. Explain that AlphaFold can still vary due to GPU nondeterminism, package/backend changes, and database updates.

## Relaxation Choice Caveat

- `--models_to_relax=none` is often the safest command-construction choice for dry-run planning, quick unrelaxed outputs, or environments with OpenMM issues.
- `--models_to_relax=best` is the default and relaxes only the top-ranked prediction.
- `--models_to_relax=all` can be much slower and writes relaxed outputs for every ranked model.

For OpenMM platform, GPU relaxation, or violation metric details, route to `../relaxation/`.
