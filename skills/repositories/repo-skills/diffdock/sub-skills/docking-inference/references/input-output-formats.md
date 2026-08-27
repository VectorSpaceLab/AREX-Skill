# Input and Output Formats

## Purpose

Use this reference to prepare DiffDock inference inputs and interpret prediction outputs. The schema and naming rules are distilled from README guidance, `data/protein_ligand_example.csv`, `inference.py`, and inference dataset helpers.

## Input Modes

DiffDock inference supports two practical input modes:

- **Batch CSV:** pass `--protein_ligand_csv path/to/file.csv`.
- **Single complex:** omit `--protein_ligand_csv` and pass `--protein_path` or `--protein_sequence`, plus `--ligand_description`.

When the CSV path is provided, DiffDock reads the CSV and ignores the single-complex protein and ligand arguments.

## Batch CSV Schema

Required columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `complex_name` | Column required; value may be blank | Output subdirectory name. Blank/NaN values become `complex_<row_index>`. |
| `protein_path` | Column required; value required unless `protein_sequence` is present | Path to a protein `.pdb` file. |
| `ligand_description` | Required and non-empty | Either a SMILES string or a ligand file path readable by RDKit. |
| `protein_sequence` | Column required; value required when `protein_path` is blank | Amino-acid sequence for ESMFold structure generation. |

A minimal batch CSV shape is:

```csv
complex_name,protein_path,ligand_description,protein_sequence
target_from_files,inputs/target_protein.pdb,inputs/target_ligand.sdf,
target_from_smiles,inputs/target_protein.pdb,COc(cc1)ccc1C#N,
target_from_sequence,,CCO,GIQSYCTPPYSVLQDPPQPVV
```

Do not depend on repository example paths in generated workflows. Copy or create the user's own input files and point the CSV at those files.

## Protein Inputs

### `protein_path`

- Expected to point to a `.pdb` file.
- Preferred when available because DiffDock can parse sequences from PDB and avoid ESMFold structure generation.
- CPU execution is possible for PDB inputs, but model inference is much slower than GPU execution.
- Very large receptors can fail during receptor graph construction; the source raises an error when receptor size is too large for the expected graph path.

### `protein_sequence`

- Used only when `protein_path` is missing for that row or single-complex command.
- Causes DiffDock to write an ESMFold-generated PDB as `<out_dir>/<complex_name>/<complex_name>_esmfold.pdb` when needed.
- Requires the ESM/OpenFold stack and can load/download large models depending on the environment.
- The implementation moves the ESMFold model to CUDA, so sequence mode can fail on CPU-only or GPU-memory-limited systems even when PDB input would be possible.

## Ligand Inputs

`ligand_description` can be:

- A SMILES string, parsed by RDKit and converted into a conformer.
- A molecule file path read by RDKit after SMILES parsing fails.

File suffixes supported by the repository molecule reader include:

- `.sdf`
- `.mol2`
- `.pdbqt`
- `.pdb`

RDKit parsing can fail for invalid SMILES, unsupported file suffixes, malformed molecule files, sanitization issues, or conformer-generation failures.

## Output Layout

For each complex, inference creates:

```text
<out_dir>/
  <complex_name>/
    rank1.sdf
    rank1_confidence<score>.sdf
    rank2_confidence<score>.sdf
    ...
    rankN_confidence<score>.sdf
    rank1_reverseprocess.pdb      # only when --save_visualisation is enabled
    rank2_reverseprocess.pdb      # only when --save_visualisation is enabled
```

Notes:

- `N` is `--samples_per_complex`.
- `rank1.sdf` is written for the top-ranked pose.
- Confidence-ranked files use two decimal places in the filename, such as `rank1_confidence0.42.sdf`.
- When a confidence model is loaded, poses are sorted by descending confidence before writing.
- When no confidence model is active, the source still attempts to write confidence-formatted filenames. Use the default config or explicit `--confidence_model_dir` for normal prediction workflows.
- `--save_visualisation` writes reverse diffusion traces as PDB files for each saved rank.

## Confidence Interpretation

The README gives rough confidence guidance for the top pose:

| Top confidence `c` | Rough interpretation |
| --- | --- |
| `c > 0` | High confidence |
| `-1.5 < c < 0` | Moderate confidence |
| `c < -1.5` | Low confidence |

This is not a binding-affinity prediction. It is a model confidence signal for pose quality. Shift expectations downward for very large ligands, large protein complexes, unbound or apo conformations, or inputs unlike the training distribution.

## Safe Validation

From this sub-skill directory, run the bundled validator before inference:

```bash
python scripts/validate_inference_inputs.py \
  --protein-ligand-csv inputs/protein_ligand.csv
```

For single-complex mode:

```bash
python scripts/validate_inference_inputs.py \
  --protein-path inputs/target_protein.pdb \
  --ligand-description inputs/target_ligand.sdf
```

The validator checks schema, required alternatives, basic suffixes, and existing path suffixes without importing DiffDock, RDKit, Torch, PyG, ProDy, ESM, or OpenFold.
