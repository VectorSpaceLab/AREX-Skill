# VGen cross-cutting troubleshooting

Use this reference when a VGen workflow fails before you reach a route-specific troubleshooting page.

## Missing CUDA or GPU access

**Symptom:** `.cuda()` errors, NCCL startup failures, or a smoke check reports no available GPU.

**Likely cause:** the environment is CPU-only, the NVIDIA driver stack is not visible, or stale distributed environment variables are confusing a launch.

**Fix:**

- Use a CUDA-capable environment for generation, training, or reward fine-tuning.
- Clear `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and `MASTER_PORT` before retrying a distributed run.
- For a fast preflight, run `scripts/check_runtime.py --repo-root <checkout> --require-cuda`.

## Missing video tooling

**Symptom:** video save helpers fail, MP4s are not playable, or metric helpers cannot inspect generated files.

**Likely cause:** `ffmpeg` or a compatible OpenCV/image I/O stack is missing.

**Fix:**

- Ensure `ffmpeg` is on PATH.
- Keep `imageio` and `imageio-ffmpeg` available for helpers that render GIF or MP4 previews.
- Use `scripts/check_runtime.py` to confirm the binary and import stack before a long run.

## OpenCV / NumPy ABI mismatch

**Symptom:** importing `cv2` fails after a NumPy upgrade.

**Likely cause:** a NumPy 2.x wheel is incompatible with the OpenCV wheel in this repo's runtime stack.

**Fix:**

- Use a NumPy 1.x release when OpenCV import errors mention ABI mismatches.
- Reinstall OpenCV after repairing NumPy if the environment was mutated in place.

## Registry or config failures

**Symptom:** `TASK_TYPE` is unknown, a config builds the wrong model family, or `train_net.py` / `inference.py` stops early.

**Likely cause:** the YAML and the entrypoint do not match, or a config's `_BASE` / `vldm_cfg` / `subject_cfg` / `motion_cfg` layering is wrong.

**Fix:**

- Read `references/configuration.md` to confirm whether the config is a train or inference route.
- Use `scripts/dispatch_config.py --dry-run --repo-root <checkout> --cfg <yaml>` to verify the selected registry before launching.
- Copy and edit a YAML instead of relying on raw CLI overrides for typed fields.

## Malformed list files

**Symptom:** the loader crashes when it splits a prompt list or a path-plus-caption list.

**Likely cause:** the list format does not match the workflow.

**Fix:**

- Prompt-only lists: one prompt per line.
- Path-plus-caption lists: `path|||caption`.
- DreamVideo metric lists: `video|||reference_dir|||prompt`.
- Use `scripts/inspect_list_file.py` before a long job.

## Missing checkpoints

**Symptom:** `FileNotFoundError` or strict `load_state_dict` mismatches.

**Likely cause:** `test_model`, `base_model`, `infer_checkpoint`, `embedder.pretrained`, or `auto_encoder.pretrained` does not point at the correct family.

**Fix:**

- Match the checkpoint to the config family.
- Check the README and the relevant sub-skill reference before swapping a model path.
- Avoid mixing family checkpoints unless you are intentionally rewriting the config.

## Stale generated or temporary files

**Symptom:** a new run reuses old outputs, or a preview script appears to read the wrong file.

**Likely cause:** the workspace still contains stale outputs from a previous run.

**Fix:**

- Use a fresh workspace or a new log directory when comparing runs.
- Keep generated previews and scratch outputs outside the runtime skill tree.

## Private-path leakage

**Symptom:** a draft instruction mentions a local conda prefix, a private cache path, or another machine-specific path.

**Likely cause:** a helper was written for a local debugging session rather than for a reusable skill.

**Fix:**

- Replace the private path with a repo-relative path or a placeholder that future users can set.
- Keep review/test artifacts and ephemeral environments out of runtime `SKILL.md` files.
