# Training Troubleshooting

## Purpose

Use this when the generic training path, config schema, or data layout fails.

## Common problems

### `KeyError: 'data_params'` or `TypeError` around `gpus`

**Symptoms:** `run.py` or a training attempt fails before the model is built.

**Likely causes:** the config follows the legacy VampVAE layout, or `trainer_params.gpus` is a scalar where the generic runner expected a list-like value.

**Recovery:** use the bundled training wrapper. It normalizes the legacy layout and accepts both list-like and scalar GPU specifications.

### CelebA file or split errors

**Symptoms:** `FileNotFoundError`, `RuntimeError`, or torchvision dataset complaints during `VAEDataset.setup()`.

**Likely causes:** the extracted CelebA tree is missing, the path in `data_params.data_path` is wrong, or the dataset was not unpacked under the expected root.

**Recovery:** point `data_path` at the extracted CelebA root and verify that the train/test splits are present. If the upstream integrity check is the only blocker, the repo's `MyCelebA` workaround is already used by the default data module.

### Lightning version mismatch

**Symptoms:** imports fail around `DDPPlugin`, `Trainer`, or other old Lightning APIs.

**Likely causes:** Lightning 2.x or a newer incompatible stack was installed.

**Recovery:** use the verified Lightning 1.5.x stack for this repo.

### No GPU / wrong `gpus` setting

**Symptoms:** CUDA errors, device mismatch errors, or trainer initialization fails on a CPU-only host.

**Likely causes:** the config assumes a CUDA run and the chosen host does not provide one.

**Recovery:** move to a CUDA-capable host or limit the task to model-reference CPU smoke checks.

### Logs or checkpoints are not where you expect

**Symptoms:** TensorBoard opens but shows no experiment, or checkpoint files appear in a different folder.

**Likely causes:** the `logging_params.save_dir` or `logging_params.name` fields do not match what you are inspecting.

**Recovery:** look under `logs/<name>/version_*` and the nested `checkpoints/` directory created by the logger.

## Model-specific note

For model-specific runtime issues such as conditional labels or sample availability, switch to the model-reference sub-skill instead of staying in the training path.
