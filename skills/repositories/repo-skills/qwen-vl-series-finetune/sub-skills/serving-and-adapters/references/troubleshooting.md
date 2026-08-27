# Troubleshooting

## Symptom: merge output is ambiguous

Likely cause:

- The save path was not explicit.
- The checkpoint is being treated as the wrong kind of artifact.

Fix:

- Provide `model-path`, `model-base`, and `save-model-path` explicitly.
- Keep the merge helper in dry-run mode until the command looks correct.

## Symptom: adapter loading fails

Likely cause:

- The base model was not provided for an adapter-backed checkpoint.

Fix:

- Keep `model-base` explicit.
- Verify whether the checkpoint is merged or adapter-backed before launching.

## Symptom: Gradio launch feels too aggressive

Likely cause:

- The command was executed instead of printed.

Fix:

- Start with the command builder’s dry-run output.
- Launch the service only when the user has confirmed the model and device.

## Symptom: quantized inference is unstable

Likely cause:

- The selected 4-bit or 8-bit path does not fit the model or backend choice.

Fix:

- Try a non-quantized load or the documented SDPA fallback for Qwen3.5.
