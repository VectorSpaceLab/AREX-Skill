# Configuration

## Purpose

Use this reference to choose and override DiffDock inference config values. It summarizes the inference parser and the bundled `default_inference_args.yaml` behavior without requiring access to the original config file.

## How Config Loading Works

`python -m inference` accepts `--config`, defaulting to `default_inference_args.yaml`. At startup, DiffDock loads the YAML and overwrites matching parsed arguments before model loading. CLI values for keys also present in the YAML can be replaced by the config load, so use one of these patterns:

- Edit or copy the YAML config and pass it with `--config`.
- Put values not controlled by the config directly on the command line.
- When in doubt, inspect the active config and command together before a long run.

The bundled command builder prints only the command. It does not validate YAML precedence or load DiffDock.

## Key Default Inference Fields

Known default inference config fields include:

| Field | Typical default | Meaning |
| --- | --- | --- |
| `model_dir` | `./workdir/v1.1/score_model` | Score model directory containing `model_parameters.yml` and the score checkpoint. |
| `confidence_model_dir` | `./workdir/v1.1/confidence_model` | Confidence model directory containing `model_parameters.yml` and the confidence checkpoint. |
| `ckpt` | `best_ema_inference_epoch_model.pt` | Score model checkpoint filename. |
| `confidence_ckpt` | `best_model_epoch75.pt` | Confidence model checkpoint filename used by the default config. |
| `inference_steps` | `20` | Denoising schedule length. |
| `actual_steps` | `19` | Actual denoising steps performed when not null. |
| `samples_per_complex` | `10` | Number of poses generated per complex. |
| `no_final_step_noise` | `true` | Avoids noise in the final reverse diffusion step. |
| `old_score_model` | `false` | Score model compatibility flag. |
| `old_confidence_model` / `old_filtering_model` | compatibility defaults | Confidence/filtering compatibility controls used by the current config family. |
| `initial_noise_std_proportion` | numeric | Initial ligand noise scale. |
| `temp_sampling_tr`, `temp_sampling_rot`, `temp_sampling_tor` | numeric | Sampling temperature controls for translation, rotation, and torsion. |
| `temp_psi_tr`, `temp_psi_rot`, `temp_psi_tor` | numeric | Psi controls for translation, rotation, and torsion sampling. |
| `temp_sigma_data_tr`, `temp_sigma_data_rot`, `temp_sigma_data_tor` | numeric | Sigma-data controls for translation, rotation, and torsion sampling. |

Keep the provided temperature and schedule values unless reproducing a specific experiment or intentionally exploring sampling behavior.

## Model Directory Requirements

Each model directory must contain:

- `model_parameters.yml`
- The configured checkpoint file, such as `best_ema_inference_epoch_model.pt` for the score model.

The confidence model directory must also contain its own `model_parameters.yml` and confidence checkpoint.

If `model_dir` does not exist, inference attempts to download `diffdock_models.zip` from release URLs derived from the repository URL, first from the latest release and then from the `v1.1` release. If download fails, inference raises an exception that models were not found locally and could not be downloaded.

For offline or restricted-network environments:

1. Pre-stage the model files in a local work directory.
2. Point `--model_dir` to the local score model directory.
3. Point `--confidence_model_dir` to the local confidence model directory.
4. Ensure `--ckpt` and `--confidence_ckpt` match filenames actually present in those directories.

## Output and Compute Overrides

Common safe overrides:

- `--out_dir`: use a run-specific output root to avoid mixing predictions.
- `--samples_per_complex`: lower to `1` or `2` for smoke tests, raise for production sampling.
- `--batch_size`: lower on CPU or small GPU memory.
- `--actual_steps`: lower for a fast exploratory run, but expect lower quality.
- `--save_visualisation`: enable only when reverse-process PDB traces are needed; it adds files per rank.

## Input-Dependent Runtime Behavior

- PDB inputs avoid ESMFold structure generation but still compute ESM language-model embeddings for receptor features.
- Sequence-only inputs generate missing PDB files with ESMFold under the output complex directory and can be much heavier.
- The first run on a device may precompute and cache SO(2)/SO(3) lookup tables, adding startup time.
- CUDA is preferred; CPU can work for PDB input workflows but is significantly slower.

## Config Review Checklist

Before running inference:

1. Confirm `model_dir` and `confidence_model_dir` point to directories, not checkpoint files.
2. Confirm both model directories contain `model_parameters.yml`.
3. Confirm checkpoint filenames in the command/config exist under their model directories.
4. Confirm `samples_per_complex * number_of_complexes` is reasonable for the available runtime.
5. Confirm sequence-only rows are intentional because they may trigger ESMFold.
6. Confirm the output directory is unique for the run or safe to reuse.
