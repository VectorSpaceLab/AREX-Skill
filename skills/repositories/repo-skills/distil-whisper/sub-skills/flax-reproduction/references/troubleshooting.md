# Flax Reproduction Troubleshooting

## Purpose

Read this when the Flax package or one of the Flax scripts fails to import or when a conversion / evaluation command is too new for the repo-era stack.

## Common issues

### `AttributeError: module 'jax.core' has no attribute 'NamedShape'`

- **Symptoms:** `import distil_whisper` fails.
- **Likely cause:** JAX is too new for the package.
- **Recovery:** pin to a repo-compatible 0.4.x JAX / JAXLIB pair. The verified inspection stack used JAX 0.4.18.

### `AttributeError: module 'scipy.linalg' has no attribute 'tril'`

- **Symptoms:** `training/flax/run_eval.py` or the bundled `scripts/convert_train_state_to_hf.py` fails while importing Optax / JAX.
- **Likely cause:** SciPy is too new for the older JAX stack.
- **Recovery:** pin SciPy to a 1.11.x release that still exposes the expected linear-algebra helpers.

### NumPy 2 or `_ARRAY_API not found`

- **Symptoms:** JAX emits a NumPy compatibility warning or `jaxlib` fails to import.
- **Likely cause:** a newer NumPy was installed with older JAX/JAXLIB wheels.
- **Recovery:** pin NumPy to 1.26.x and keep ml-dtypes in the compatible 0.3.x range.

### `cannot import name 'send_example_telemetry' from 'transformers.utils'`

- **Symptoms:** `training/flax/run_eval.py` fails before argument parsing.
- **Likely cause:** Transformers is too new for the Flax scripts.
- **Recovery:** use a repo-compatible 4.x Transformers release; the verified inspection stack used 4.35.2.

### `ValueError: coordinator_address should be defined.`

- **Symptoms:** `scripts/convert_train_state_to_hf.py --help` fails immediately.
- **Likely cause:** the helper was run without the repo-compatible safe wrapper or the environment still expects explicit distributed initialization.
- **Recovery:** use the bundled helper, and set `DISTIL_WHISPER_ENABLE_JAX_DISTRIBUTED_INIT=1` only when you are about to run a real distributed job.

### `cached_property` missing

- **Symptoms:** `import distil_whisper` fails at `partitioner.py`.
- **Likely cause:** the helper package was not installed.
- **Recovery:** install `cached-property` and retry.

## Workflow-specific notes

- `training/flax/run_eval.py` is sensitive to the Transformers version.
- `training/flax/run_long_form_transcription.py` is more forgiving, but still depends on the JAX/Flax/SciPy trio above.
- The TPU-oriented scripts in `training/flax/*_scripts/` are often better treated as recipes than as default local helpers.

## Read next

- Use `../../scripts/check-env.py` to verify the current stack after any package change.
- If the issue is really about pseudo-labelling or PyTorch evaluation, route to `pytorch-training` instead.
