# Inference Troubleshooting

## Invalid request or family mismatch

### Symptoms
- `set_config()` raises a `ValueError` before the runner is built.
- `model_cls` and `task` clearly do not match.
- An omni-vision task complains about a missing or extra subtask.

### Likely cause
The request does not match the family contract.

### Recovery
- Re-read `model-families.md`.
- Keep `model_cls`, `task`, and any family-specific path override aligned.
- For `sensenova_vision`, make sure the omni-vision task shape is correct.

## Model-path or config-path problems

### Symptoms
- The runner refuses to start because a file is missing.
- `config_json` or the model root points at the wrong layout.
- A family-specific branch expects `config.json`, `transformer/config.json`, or another file that is not present.

### Likely cause
The checkpoint tree does not match the family's expected layout.

### Recovery
- Confirm the file tree before retrying.
- Check whether the family uses a root `config.json`, a transformer subdirectory, low-noise/high-noise branches, or a special subfolder.
- For WorldMirror, verify the weights are under the right subfolder before adding `--subfolder`.

## Optional backend or optimization failures

### Symptoms
- Errors mention `flash_attn`, `sageattn`, `qtorch`, or a CUDA extension build.
- Multi-GPU or quantized settings fail early.

### Likely cause
An optional accelerator package is missing or incompatible with the selected workflow.

### Recovery
- Install the missing backend only when that workflow actually needs it.
- If the task can run without the optimization, drop the optional flag and retry.
- Use the family reference to confirm whether the optimization is even supported for that model.

## Input-shape mismatches

### Symptoms
- Generation starts but then fails when a prompt, image, video, audio, pose, or mask field is missing.
- The requested task expects a control input that was not provided.

### Likely cause
The selected task needs a different request shape than the one supplied.

### Recovery
- Read the family notes and the main workflow reference.
- Ensure the correct fields are present for the task: image, audio, pose, last-frame, mask, input path, or SR ratio.

## What not to do

- Do not use a CPU-only smoke import as proof that a CUDA or quantized path is usable.
- Do not collapse family-specific failures into a generic "LightX2V is broken" answer.
- Do not route server or disagg failures back through this sub-skill; those belong in their own route.
