# Structure-Prediction Data Formats

Use this reference to validate user inputs and path contracts before planning HelixFold-family execution. The bundled validator covers HelixFold3/S1 entity JSON; FASTA and database paths still need user-provided files and, for execution, the full runtime environment.

## HelixFold3 Entity JSON

Minimal form:

```json
{
  "entities": [
    {"type": "protein", "sequence": "MSEQUENCE", "count": 1},
    {"type": "ligand", "ccd": "QF8", "count": 1}
  ]
}
```

Top-level contract:

- Must be a JSON object.
- Must contain non-empty `entities`.
- May contain extra fields, but unsupported fields should be treated conservatively unless documented by a newer local version.

Entity contract:

- `type` must be one of `protein`, `dna`, `rna`, `ligand`, or `ion`.
- `count` is required and must be a positive integer.
- `protein`, `dna`, and `rna` require a non-empty `sequence` string.
- `ligand` requires at least one of `ccd` or `smiles`; if both are present, native preprocessing prefers `ccd`, so ask the user which representation they intend.
- `ion` requires `ccd`; do not use `smiles` for ions.
- `modification`, when present, must be a list and is valid only on polymer entities.

Polymer sequence alphabets:

- Protein examples use uppercase amino-acid letters. If strict validation is requested, allow common one-letter protein symbols plus ambiguity letters, and warn on anything else.
- DNA examples use `A`, `C`, `G`, and `T`.
- RNA examples use `A`, `C`, `G`, and `U`.
- HelixFold preprocessing may have its own tolerance; use strict alphabet checks as an early quality gate, not as a replacement for model preprocessing.

Modification contract:

```json
{"type": "residue_replace", "ccd": "5CM", "index": 2}
```

- `index` is 1-based.
- `index` must fall within the unexpanded sequence length.
- `ccd` must be a non-empty string.
- HelixFold3 docs currently document `residue_replace` as the supported type.

## HelixFold-S1 Entity JSON

S1 uses the same general `entities` array and adds top-level run fields:

```json
{
  "job_name": "example",
  "recycle": 10,
  "ensemble": 30,
  "entities": [
    {"type": "protein", "sequence": "MSEQUENCE", "count": 1},
    {"type": "protein", "sequence": "OTHERSEQ", "count": 1}
  ],
  "model_type": "HelixFold-S1"
}
```

S1-specific checks:

- `job_name` is required, must be non-empty, should be safe for file names, and is limited by the native schema to 200 characters.
- `recycle` and `ensemble`, when present, must be positive integers no greater than 100.
- `model_type` is required by the native S1 schema and should be `HelixFold-S1` for S1 planning.
- Entity `count` is limited by the native S1 schema to 1 through 50.
- The README warns that S1 requires at least two chains. Count expanded polymer/ligand copies and reject single-chain inputs for S1 planning.
- `s1_sample_constraint`, when present, is a list of at most 10 interface sampling constraints with only `left_entity` and `right_entity` values in `<entity>-<copy>` format, such as `1-1`.
- `constraint` is not supported by S1 in the bundled source validation; do not mix it with `model_type: HelixFold-S1`.
- S1 examples include `sidechain_replace` modification objects with fields such as `R_smiles` and `R_connect_idx`; the safe validator treats those as accepted only in `--mode helixfold-s1`, and accepts `R_connect_idx: 0` because the bundled S1 demo uses it.
- Do not specify multiple modifications for the same residue index; native validation rejects duplicate modification indices.

## Multimodal Example Pattern

A difficult but valid HelixFold3-style case can combine protein, modified DNA, unmodified DNA, and a ligand:

```json
{
  "entities": [
    {"type": "protein", "sequence": "MSTNPKPQR", "count": 1},
    {"type": "dna", "sequence": "CCATTATAGC", "count": 1,
     "modification": [{"type": "residue_replace", "ccd": "5CM", "index": 2}]},
    {"type": "dna", "sequence": "GCTATAATGG", "count": 1},
    {"type": "ligand", "smiles": "CCO", "count": 1}
  ]
}
```

Use this kind of case to validate routing and memory warnings without running inference.

## FASTA Inputs

HelixFold and HelixFold-Single use FASTA rather than entity JSON.

HelixFold requirements:

- `--fasta_paths` is a comma-separated list of FASTA files.
- Every FASTA basename must be unique because each basename becomes an output subdirectory.
- For full MSA-backed inference, database paths and MSA binaries are still required.

HelixFold-Single requirements:

- `--fasta_file` points to one FASTA file.
- The script reads one header and sequence until another header or EOF; prefer a single protein sequence per file.
- `--init_model` must point to the HelixFold-Single checkpoint.
- `--output_dir` receives `unrelaxed.pdb`.

## Database Path Contracts

HelixFold3 reduced database path set:

- `small_bfd/bfd-first_non_consensus_sequences.fasta`
- `uniprot/uniprot.fasta`
- `pdb_seqres/pdb_seqres.txt`
- `uniref90/uniref90.fasta`
- `mgnify/mgy_clusters_2018_12.fa`
- `pdb_mmcif/mmcif_files/`
- `pdb_mmcif/obsolete.dat`
- `ccd_preprocessed_etkdg.pkl.gz`
- `Rfam-14.9_rep_seq.fasta`

HelixFold-S1 uses similar database families, with S1 docs/launcher also referencing an RNA species identifier map and an Rfam path under an RNA MSA database layout. The S1 launcher uses `small_bfd_database_path` while HelixFold3 uses `reduced_bfd_database_path`.

HelixFold AlphaFold2-style path set:

- `bfd/...` for full databases or `small_bfd/bfd-first_non_consensus_sequences.fasta` for reduced databases.
- `uniclust30/...` when full database preset is used.
- `uniref90/uniref90.fasta`, `mgnify/mgy_clusters_2018_12.fa`, `pdb70/pdb70`.
- `pdb_mmcif/mmcif_files/` and `pdb_mmcif/obsolete.dat`.
- Model parameters under a `params/` directory inside `--data_dir`.

## Checkpoint Contracts

- HelixFold3: `--init_model` points to a `.pdparams` file for the selected all-atom model config.
- HelixFold-S1: module 1 and module 2 use separate checkpoint paths, usually under an `init_models/` directory.
- HelixFold: model parameters are resolved from `--data_dir/params/params_<model_name>.pdparams` or `.npz`.
- HelixFold-Single: `--init_model` points to `helixfold-single.pdparams` or an equivalent trained checkpoint.

Do not infer that a checkpoint exists from a directory name alone. Check exact file presence before any approved run.

## Optional Dependency Boundary

The base PaddleHelix inspection environment can verify source-layout `pahelix` imports and documentation-derived contracts, but it intentionally does not prove HelixFold execution readiness. Treat PaddlePaddle GPU, MSA binaries, OpenMM/PDBFixer, `pgl`, RDKit, model parameters, and sequence/template databases as optional workflow dependencies that must be checked or installed only with explicit user approval.

## Output Path Contracts

- HelixFold3 creates `<output_dir>/<input-json-stem>/` and stores `msas/`, per-sample `*-pred-*` folders, and ranked `*-rank*` folders containing `predicted_structure.cif` and `all_results.json`.
- HelixFold-S1 writes directly into the provided output directory: `final_features.pkl`, `user_input.json`, `job_status.json`, `timings_featurization.json`, `msas/`, `interface_infos/`, `module1/`, `module2/`, and `previous_sampled_interface/`.
- HelixFold creates `<output_dir>/<fasta-stem>/` with `features.pkl`, `msas/`, `ranked_*.pdb`, `relaxed_model_*.pdb`, `unrelaxed_model_*.pdb`, `result_model_*.pkl`, `ranking_debug.json`, and `timings.json`.
- HelixFold-Single writes `unrelaxed.pdb` in `--output_dir`.

## Evidence Labels

This reference distills evidence from HelixFold3/S1 demo JSON files, HelixFold3/S1 README files and launchers, HelixFold inference docs, and HelixFold-Single README/inference script.
