# Troubleshooting Docking Inference

## Purpose

Use this reference when `python -m inference` fails before, during, or after docking prediction. It focuses on recoverable command, input, model, dependency, backend, and GNINA issues.

## Fast Triage

1. Run [validate_inference_inputs.py](../scripts/validate_inference_inputs.py) on the CSV or single-complex arguments.
2. Rebuild the command with [build_inference_command.py](../scripts/build_inference_command.py) to catch mode conflicts before launching inference.
3. Check model directories and checkpoints using [configuration.md](configuration.md).
4. Distinguish PDB input failures from sequence/ESMFold failures; sequence mode has heavier dependencies.
5. If the failure is benchmark metrics or evaluation-only GNINA output, route to the evaluation-benchmarks sub-skill.

## Missing Heavy Dependencies

### Symptoms

- `ModuleNotFoundError` or `ImportError` for `torch`, `torch_geometric`, `rdkit`, `prody`, `esm`, `openfold`, `Bio`, `torch_cluster`, or related packages.
- Importing `inference.py` fails before any arguments are processed.

### Likely Cause

DiffDock inference imports the heavy Torch/PyG/RDKit/ProDy/ESM/OpenFold stack at module import time. The repository is script-style and does not expose installable package metadata that would automatically declare all runtime extras.

### Recovery

- Use the root install/runtime reference if available: [../../../references/install-and-runtime.md](../../../references/install-and-runtime.md).
- Prefer the repository's documented environment or container setup for actual inference runs.
- Do not use this sub-skill's helper scripts as proof that full DiffDock inference dependencies are installed; they intentionally avoid heavy imports.

## CPU, CUDA, and Runtime Pressure

### Symptoms

- Runs are extremely slow on CPU.
- CUDA out-of-memory errors during ESM, ESMFold, graph construction, or sampling.
- First run pauses before sampling.

### Likely Cause

DiffDock chooses `cuda` when available and otherwise CPU. PDB-based inference can run on CPU but is much slower. Sequence-only inputs can trigger ESMFold and the implementation moves that model to CUDA. The first run on a device may precompute SO(2)/SO(3) lookup tables.

### Recovery

- For a smoke run, use PDB inputs, reduce `--samples_per_complex`, reduce `--batch_size`, and consider reducing `--actual_steps`.
- Avoid sequence-only rows unless ESMFold dependencies, model loading, and GPU memory are available.
- Treat lookup-table precomputation as expected startup overhead if it happens only on first use.

## Model Directory or Download Failure

### Symptoms

- Error stating models were not found locally and failed to download.
- `FileNotFoundError` for `model_parameters.yml`.
- `FileNotFoundError` for `best_ema_inference_epoch_model.pt`, `best_model.pt`, or `best_model_epoch75.pt`.

### Likely Cause

`model_dir` is missing, incomplete, or points to the wrong location. If it does not exist, inference tries release downloads; network restrictions, changed release assets, or unavailable URLs can fail.

### Recovery

- Pre-stage local model files instead of relying on download.
- Set `--model_dir` to the local score model directory, commonly a `score_model` directory.
- Set `--confidence_model_dir` to the local confidence model directory, commonly a `confidence_model` directory.
- Match `--ckpt` and `--confidence_ckpt` to actual filenames in those directories.
- Confirm both model directories contain `model_parameters.yml`.

## Invalid CSV or Single-Complex Inputs

### Symptoms

- `KeyError` for `complex_name`, `protein_path`, `protein_sequence`, or `ligand_description`.
- Rows are skipped because the dataset did not contain a complex.
- Output directories appear with fallback names like `complex_0`, but expected names are missing.

### Likely Cause

CSV columns are missing, required values are blank, or single-complex arguments are incomplete. In CSV mode, DiffDock expects all four schema columns even when some row values are blank.

### Recovery

- Use [input-output-formats.md](input-output-formats.md) for the exact schema.
- Run:

```bash
python scripts/validate_inference_inputs.py \
  --protein-ligand-csv inputs/protein_ligand.csv
```

- Ensure each row has either `protein_path` or `protein_sequence`.
- Ensure `ligand_description` is non-empty for every row.
- Use unique `complex_name` values when deterministic output directory names matter.

## RDKit Ligand Parsing Failure

### Symptoms

- Messages like `Failed to read molecule ... We are skipping it`.
- Errors around unsupported molecule file formats, sanitization, conformer generation, or invalid SMILES.

### Likely Cause

`ligand_description` is not a valid SMILES string and is not a supported readable file, or the file exists but RDKit cannot parse or sanitize it.

### Recovery

- For file inputs, prefer `.sdf` or `.mol2` ligand files with valid coordinates and chemistry.
- Check that paths in CSV files are correct relative to the working directory used for `python -m inference`.
- For SMILES, quote strings in shell commands when they contain special characters.
- If a molecule file is intended, use a supported suffix: `.sdf`, `.mol2`, `.pdbqt`, or `.pdb`.

## Protein PDB Parsing or Receptor Graph Failure

### Symptoms

- Rows are skipped after ProDy or receptor parsing errors.
- Errors mention missing C-alpha atoms, receptor structure extraction, or receptor size.

### Likely Cause

The protein file is not a usable PDB for DiffDock receptor graph construction, lacks expected residues/atoms, is too large, or points to the wrong path.

### Recovery

- Validate the path and `.pdb` suffix with the bundled validator.
- Use a cleaned protein PDB with standard amino-acid residues and C-alpha atoms.
- Reduce problematic multi-chain or very large systems before inference when appropriate.
- If the user is evaluating benchmark preprocessing rather than ad-hoc inference, route to evaluation-benchmarks or training-data as appropriate.

## ESMFold and `protein_sequence` Failures

### Symptoms

- Sequence-only rows fail before ligand sampling.
- Errors mention ESMFold, OpenFold, CUDA, model loading, or out of memory.
- Expected generated `<complex_name>_esmfold.pdb` files are absent.

### Likely Cause

Rows with no `protein_path` trigger ESMFold structure generation. This path requires additional model dependencies and substantial compute.

### Recovery

- Prefer providing a PDB file via `protein_path` when available.
- If sequence mode is required, confirm ESM/OpenFold dependencies and sufficient GPU memory.
- Use a tiny sequence-only smoke case before running a large CSV.
- Keep sequence rows separate from ordinary PDB rows when debugging so failures are isolated.

## Confidence Output Surprises

### Symptoms

- Confidence-ranked filenames are missing, malformed, or confidence values are confusing.
- Users interpret confidence as binding affinity.

### Likely Cause

Confidence output depends on a loaded confidence model. Confidence is a pose-quality signal, not binding affinity.

### Recovery

- Use a config with a valid `confidence_model_dir` and confidence checkpoint.
- Interpret top-pose confidence roughly as high when `c > 0`, moderate when `-1.5 < c < 0`, and low when `c < -1.5`, with downward adjustment for out-of-distribution systems.
- Do not report confidence as binding affinity.

## Reverse-Process Visualization Issues

### Symptoms

- `rankN_reverseprocess.pdb` files are missing.
- Output directory contains SDF predictions but no PDB trajectory-style files.

### Likely Cause

`--save_visualisation` was not enabled, or the complex failed before saving.

### Recovery

- Add `--save_visualisation` for runs where reverse diffusion traces are needed.
- Expect one reverse-process PDB per rank only for successfully sampled complexes.
- Disable visualization during high-throughput runs unless the extra files are needed.

## GNINA External Binary Issues

### Symptoms

- Shell or subprocess errors mention `gnina` not found.
- Expected GNINA logs, minimized ligand files, or GNINA metrics are missing.
- GNINA output files cannot be parsed.

### Likely Cause

GNINA is an external executable, not a Python dependency. The inference parser exposes GNINA flags, while the explicit minimization and metric aggregation path is evidenced in evaluation code. Runtime availability and wiring can differ by command path.

### Recovery

- Confirm `gnina` is installed and executable, or pass `--gnina_path /path/to/gnina`.
- Treat GNINA minimization as optional post-processing, not required for standard DiffDock SDF predictions.
- For aggregate GNINA metrics, use the evaluation-benchmarks route.
- If relying on GNINA inside `python -m inference`, first inspect or smoke-test the active checkout's command path because parser support alone does not guarantee extra GNINA outputs.

## When to Stop and Ask

Stop and ask the user before proceeding when:

- The fix requires installing heavyweight GPU, Torch/PyG, RDKit, ESM, OpenFold, or GNINA dependencies.
- Model weights must be downloaded in a restricted environment.
- The user wants sequence folding without available GPU memory details.
- Existing output directories may be overwritten or mixed with previous predictions.
