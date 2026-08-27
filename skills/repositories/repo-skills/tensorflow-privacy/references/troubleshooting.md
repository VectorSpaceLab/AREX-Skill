# Troubleshooting

## Purpose

This page covers repo-wide install and runtime problems that affect several sub-skills.

## Import or install problems

### `tensorflow_privacy` does not import

**Likely causes**
- The environment is using the wrong Python version.
- The repo was not installed editable or the published package is missing.
- Required TensorFlow / NumPy / SciPy / sklearn dependencies are missing or incompatible.

**What to do next**
- Re-read `references/install-and-scope.md`.
- Verify the installed distribution with `python -I -c "from importlib.metadata import version; print(version('tensorflow-privacy'))"`.
- Run `scripts/check_env.py`.

### `pip check` reports broken requirements

**Likely causes**
- A resolver downgraded one of the TensorFlow or scientific Python packages.
- A later manual install introduced an incompatible wheel.

**What to do next**
- Reinstall the minimum runtime set from `requirements.txt`.
- Prefer a clean prefix instead of repairing a user-owned environment.

## TensorFlow / training issues

### DP optimizer complains that gradients were not used

**Symptom**
- Assertion or error about `get_gradients()` / `_compute_gradients()` not being called.

**Likely causes**
- The optimizer was used like a standard optimizer but the loss was not routed through the DP path.
- The model is using an incompatible custom training loop.

**What to do next**
- Check `sub-skills/training/references/troubleshooting.md`.
- Make sure the loss is per-example when required and the optimizer is the DP variant.

### Loss shape or microbatch errors

**Symptom**
- Shape mismatch, reduction mismatch, or microbatching assertion.

**Likely causes**
- A scalar loss was passed where a per-example loss vector was expected.
- `num_microbatches` does not match the batch layout.

**What to do next**
- Check the training sub-skill's per-example loss guidance.
- Try the bundled tiny training smoke helper.

## Privacy accounting issues

### CLI help prints but returns non-zero through `conda run`

This was observed for both accounting CLIs when `absl` printed usage text. The usage text itself is the expected signal; the non-zero exit is a wrapper behavior from `conda run` plus the help command, not a repo failure.

### User-level privacy statement says no bound is possible

**Likely causes**
- `max_examples_per_user` was not supplied.
- The privacy statement is being asked for add-or-remove-one-user guarantees without a user-participation bound.

**What to do next**
- Supply `max_examples_per_user` if you truly need user-level privacy.
- Otherwise interpret the example-level statement instead.

## Privacy test issues

### `run_attacks` fails on tiny data

**Likely causes**
- Too few samples for a balanced attack or cross-validation split.
- Loss / label / logit shapes are inconsistent.
- The wrong attack type was chosen for the available inputs.

**What to do next**
- Use the bundled tiny membership-inference smoke helper.
- Verify the `AttackInputData` fields and the selected `AttackType`.

### Secret-sharer exposure numbers look odd on toy data

**Likely causes**
- The toy vocabulary is too small.
- There are too few reference sequences.

**What to do next**
- Increase the vocabulary or reference count.
- Use the tiny secret-sharer smoke helper as a shape check, not as a scientific benchmark.

## Optional fast-clipping helper issues

### `tensorflow_models` / `tensorflow_hub` / TFDS imports fail

**Likely causes**
- The optional NLP/BERT helper path was selected without its extra dependency stack.
- A protobuf / TFDS compatibility issue surfaced in the optional path.
- `pkg_resources` is unavailable in the current prefix.

**What to do next**
- Keep the minimum scope on the core fast-clipping helpers.
- If you truly need the NLP/BERT helper path, prepare the extra dependency stack explicitly and verify it separately.

## Hardware questions

### TensorFlow reports that no GPU is visible

That is expected in the verified minimum environment. The core repo workflows in this skill are CPU-verifiable.

If you explicitly need a GPU/TPU-specific helper or example, switch to a scoped plan that claims that backend and prepare the matching environment first.
