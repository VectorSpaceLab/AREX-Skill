# CLI Reference

## Purpose

Use this reference to plan DiffDock command-line docking prediction with `python -m inference`. It distills the README inference workflow and the `inference.py` argument parser so future agents do not need to reopen repository files.

## Command Patterns

### Batch CSV input

```bash
python -m inference \
  --config default_inference_args.yaml \
  --protein_ligand_csv inputs/protein_ligand.csv \
  --out_dir results/user_predictions
```

Batch mode uses the CSV instead of `--protein_path`, `--protein_sequence`, and `--ligand_description`.

### Single complex with a PDB protein

```bash
python -m inference \
  --config default_inference_args.yaml \
  --complex_name target_001 \
  --protein_path inputs/target_001_protein.pdb \
  --ligand_description inputs/target_001_ligand.sdf \
  --out_dir results/target_001
```

A ligand SMILES string can be used instead of a ligand file:

```bash
python -m inference \
  --config default_inference_args.yaml \
  --complex_name target_001_smiles \
  --protein_path inputs/target_001_protein.pdb \
  --ligand_description "COc(cc1)ccc1C#N" \
  --out_dir results/target_001_smiles
```

### Single complex with protein sequence folding

```bash
python -m inference \
  --config default_inference_args.yaml \
  --complex_name target_001_sequence \
  --protein_sequence "GIQSYCTPPYSVLQDPPQPVV" \
  --ligand_description "COc(cc1)ccc1C#N" \
  --out_dir results/target_001_sequence
```

Sequence mode causes DiffDock to generate a missing protein structure with ESMFold inside the complex output directory. This path is heavier than PDB input and may require ESM/OpenFold dependencies and model loading.

### Dry command construction

From this sub-skill directory, use the bundled helper when preparing commands for users or CI checks:

```bash
python scripts/build_inference_command.py \
  --config default_inference_args.yaml \
  --protein-ligand-csv inputs/protein_ligand.csv \
  --out-dir results/user_predictions \
  --samples-per-complex 10
```

The helper prints a shell-quoted command and never imports DiffDock or runs inference.

## Important Arguments

| Argument | Use | Notes |
| --- | --- | --- |
| `--config` | Load YAML defaults before running | Parser default is `default_inference_args.yaml`; YAML values overwrite parser defaults. |
| `--protein_ligand_csv` | Batch input table | When set, it replaces single-complex protein and ligand flags. |
| `--complex_name` | Single-complex output name | Defaults to `complex_0` in single mode when omitted. Blank CSV names become `complex_<row_index>`. |
| `--protein_path` | Protein PDB file | Preferred for predictable inference and CPU fallback; ignored when CSV mode is used. |
| `--protein_sequence` | Amino-acid sequence for ESMFold | Used only when `protein_path` is absent; may trigger structure generation and heavy model loading. |
| `--ligand_description` | Ligand SMILES or molecule file path | RDKit tries SMILES first, then reads supported file types when SMILES parsing fails. |
| `--out_dir` | Prediction root | Inference creates one subdirectory per complex. |
| `--samples_per_complex` | Number of generated poses per complex | Default parser value is `10`; config may override it. |
| `--batch_size` | Sampling batch size | Default parser value is `10`; reduce for memory pressure. |
| `--inference_steps` | Denoising schedule length | Default parser value is `20`; config may override. |
| `--actual_steps` | Number of denoising steps actually performed | When set, sampling uses this instead of `--inference_steps`. |
| `--save_visualisation` | Save reverse diffusion PDB traces | Writes `rankN_reverseprocess.pdb` files per complex when enabled. |
| `--model_dir` | Score model directory | Must contain `model_parameters.yml` and the score checkpoint, or DiffDock tries model download. |
| `--ckpt` | Score model checkpoint filename | Parser default is `best_ema_inference_epoch_model.pt`. |
| `--confidence_model_dir` | Confidence model directory | Enables confidence sorting and confidence-ranked SDF filenames. |
| `--confidence_ckpt` | Confidence model checkpoint filename | Parser default is `best_model.pt`, while the bundled default config uses `best_model_epoch75.pt`. |
| `--loglevel` | Log verbosity | Parser aliases include `-l`, `--log`, and `--loglevel`; default is `WARNING`. |

## Sampling Temperature Arguments

`inference.py` exposes separate temperature controls for translation, rotation, and torsion:

- `--temp_sampling_tr`, `--temp_psi_tr`, `--temp_sigma_data_tr`
- `--temp_sampling_rot`, `--temp_psi_rot`, `--temp_sigma_data_rot`
- `--temp_sampling_tor`, `--temp_psi_tor`, `--temp_sigma_data_tor`

Prefer the values from the known-good inference config unless a user has a concrete reason to tune sampling behavior.

## GNINA Flags

The inference parser includes `--gnina_minimize`, `--gnina_path`, `--gnina_log_file`, `--gnina_full_dock`, `--gnina_autobox_add`, and `--gnina_poses_to_optimize`. Treat these as advanced external-binary controls:

- `--gnina_path` defaults to `gnina` and requires the executable to be available on `PATH` or supplied as a path.
- The GNINA utility writes temporary predicted ligand SDF files, minimized ligand SDF files, and logs in output-related directories when called.
- The current `inference.py` parser exposes the flags, while the explicit GNINA minimization loop is evidenced in evaluation code. Before promising extra GNINA outputs from `python -m inference`, verify the active code path in the target checkout.
- For benchmark-time GNINA metrics and aggregate RMSD reporting, use the evaluation-benchmarks sub-skill instead of this inference route.

## Preflight Checklist

Before a costly run:

1. Run [validate_inference_inputs.py](../scripts/validate_inference_inputs.py) on the CSV or single-complex paths.
2. Confirm model directories contain `model_parameters.yml` and the configured checkpoint files, or confirm network access for auto-download.
3. Prefer PDB inputs for lightweight validation; sequence mode may load ESMFold and generate structure files.
4. Pick an output directory that can be created and is safe to overwrite with one subdirectory per complex.
5. If running on CPU, reduce batch size and samples for an initial smoke run.
