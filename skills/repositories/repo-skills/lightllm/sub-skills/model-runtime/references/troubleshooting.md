# Model-runtime troubleshooting

## Registry miss

### Symptoms
- `ValueError` or a similar message saying the model type is unsupported.
- The wrong class is selected for a family that should be registered.

### Causes
- The registry entry is missing.
- The `condition` does not match the supplied config.
- The model family is multimodal or conditional, but the config does not expose
  the expected flag combination.

### Recovery
- Re-check the supported-model reference and the model config.
- Confirm the family name, modality, and backend flags.
- If this is a new integration, follow the add-new-model checklist.

## Backend validator failure

### Symptoms
- Validation rejects the selected attention backend or fallback path.
- The model loads on one host but not another.

### Causes
- The GPU or driver stack does not satisfy the selected kernel path.
- Optional acceleration packages are absent.
- The chosen quantization mode requires a backend that is not installed.

### Recovery
- Separate optional acceleration from required model support.
- Choose a fallback only when the docs and the selected workflow permit it.
- Re-run the CUDA/backend smoke checks for the target environment.

## Quantization mismatch

### Symptoms
- Load-time assertions around `quant_type`, `quant_cfg`, or KV settings.

### Causes
- The checkpoint does not match the selected quantized runtime.
- Text and vision quantization flags were mixed up.

### Recovery
- Match the checkpoint, quantization config, and model family.
- Use the documented tutorial or cookbook for the target family.

## Multimodal mismatch

### Symptoms
- A vision or audio model behaves like a text-only model.
- An expected multimodal path is unavailable.

### Causes
- `--enable_multimodal` was not set.
- `--disable_vision` or `--disable_audio` is suppressing the needed modality.
- The selected model family is multimodal only when a condition is met.

### Recovery
- Compare the runtime flags with the supported-model notes.
- Re-check the model cards or docs for modality requirements.

## New model integration problems

### Symptoms
- The new family builds locally but is not discoverable in the runtime flow.
- Docs and code disagree about the expected flags or class names.

### Recovery
- Treat the registry, the model directory, and the docs as one unit.
- Add or refresh a representative smoke or regression test.
- Confirm the class is reachable from the runtime flags used by the serving
  path.
