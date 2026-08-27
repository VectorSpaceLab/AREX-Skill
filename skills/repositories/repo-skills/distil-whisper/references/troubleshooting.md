# Troubleshooting

## Purpose

Read this for cross-cutting install, import, backend, and script failures that affect more than one route.

## Import and version mismatches

### `ModuleNotFoundError: No module named 'soundfile'`

- **Where it appears:** PyTorch pseudo-labelling helpers.
- **Likely cause:** the audio extra was not installed.
- **Fix:** install `soundfile` and re-run the help or smoke check.

### `No module named 'transformers.generation.flax_logits_process'`

- **Where it appears:** Flax package imports.
- **Likely cause:** Transformers is too new for the repo-era Flax code.
- **Fix:** use a 4.x Transformers release compatible with the repo, not a 5.x release.

### `cannot import name 'send_example_telemetry' from 'transformers.utils'`

- **Where it appears:** `training/flax/run_eval.py`.
- **Likely cause:** Transformers is too new.
- **Fix:** downgrade to a compatible 4.x release; the verified inspection stack used Transformers 4.35.2.

### `AttributeError: module 'jax.core' has no attribute 'NamedShape'`

- **Where it appears:** `distil_whisper` imports.
- **Likely cause:** JAX is too new for the repo-era Flax code.
- **Fix:** use an older CPU-compatible JAX/JAXLIB pair; the verified inspection stack used JAX 0.4.18.

### `AttributeError: module 'scipy.linalg' has no attribute 'tril'`

- **Where it appears:** Flax / Optax imports.
- **Likely cause:** SciPy is too new for the JAX/Flax combination.
- **Fix:** pin SciPy to a compatible 1.11.x release.

### `_ARRAY_API not found` or a NumPy 2 warning from JAX/JAXLIB

- **Where it appears:** JAX imports.
- **Likely cause:** NumPy 2 was installed with an older JAX/JAXLIB build.
- **Fix:** pin NumPy to a 1.26.x release and keep ml-dtypes in the compatible 0.3.x range.

## Workflow-specific failures

### `convert_train_state_to_hf.py` fails during `--help`

- **Symptom:** `ValueError: coordinator_address should be defined.`
- **Likely cause:** the source script initializes distributed JAX at import time.
- **Fix:** use the bundled `sub-skills/flax-reproduction/scripts/convert_train_state_to_hf.py` helper for safe local inspection, and only enable distributed JAX initialization when running a real multi-host job.

### CUDA not available in the inspection env

- **Symptom:** `torch.cuda.is_available()` is false or JAX falls back to CPU.
- **Likely cause:** the minimum inspection env uses CPU wheels.
- **Fix:** only treat this as a blocker if the user explicitly asked for GPU verification or the selected workflow truly requires CUDA.

### Hub or dataset access fails

- **Symptom:** `401`, `403`, dataset terms-of-use errors, or download failures.
- **Likely cause:** missing Hugging Face login, gated dataset access, or blocked network.
- **Fix:** log in to the Hub, accept the dataset terms, or switch to a tiny public fixture before retrying.

## Next checks

- Re-run `scripts/check-env.py` after any dependency change.
- For route-specific failures, continue in the owning sub-skill's troubleshooting reference.
