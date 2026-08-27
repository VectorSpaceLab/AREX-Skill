# Cross-Cutting Troubleshooting

## Heavy Import Failures

Symptoms include `ModuleNotFoundError` for `torch`, `torch_geometric`, `rdkit`, `prody`, `esm`, `openfold`, `e3nn`, `wandb`, or model modules. DiffDock imports many optional-heavy packages at module import time, so simple `--help` commands can fail in incomplete environments.

Use bundled command builders and validators when planning. Prepare the full runtime stack only before actual inference, UI, training, or evaluation.

## Script-Style Import Context

DiffDock is not packaged with console entry points. Run core module commands from a runtime context where the DiffDock modules are importable, or set `PYTHONPATH` to the runtime checkout. The Gradio app also uses sibling imports inside its app directory; see the web-ui troubleshooting reference for launch details.

## Model Checkpoint Failures

Typical symptoms:

- Missing `model_parameters.yml` under score or confidence model directories.
- Config points to a model directory that does not exist.
- Checkpoint filename does not match the selected `--ckpt` or `--confidence_ckpt`.
- Network model download fails when local model directories are absent.

Prefer explicit local model directories for reproducible runs. Keep `model_parameters.yml` with checkpoint files when copying trained models.

## Data Path Failures

Training and evaluation paths are layout-sensitive. Validate dataset roots, split files, ESM embedding indexes, and input CSVs before a long run. Use the nearest sub-skill helper rather than launching a model command first.

## Backend And Memory Failures

- Lower `--batch_size`, `--samples_per_complex`, `--num_workers`, and validation-inference frequency for memory pressure.
- Avoid sequence-mode folding, ESM extraction, all-atom models, and full benchmarks as initial smoke tests.
- If CUDA wheels import but CUDA allocation fails, verify driver compatibility and wheel CUDA tag before debugging DiffDock logic.

## GNINA Failures

GNINA is an external executable. A missing binary, incompatible receptor path, or failed score parsing can make GNINA metrics invalid even when DiffDock poses exist. Treat zero GNINA scores as possible tool failure until logs and minimized SDF outputs are checked.

## Network And Large Asset Boundaries

Do not silently download model weights, processed datasets, ESM models, or Docker images. Confirm the user's intended runtime, network access, disk budget, and hardware before starting those operations.
