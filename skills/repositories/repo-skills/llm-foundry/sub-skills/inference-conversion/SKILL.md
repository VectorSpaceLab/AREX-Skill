---
name: inference-conversion
description: "Use LLM Foundry inference helpers for Hugging Face generation,
  chat, Composer-to-HF conversion, ONNX export, and optional backend routing
  without owning training or evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Inference and Conversion

Use this sub-skill when a task needs to run or prepare LLM Foundry models for inference-time use:

- generate completions or chat interactively with a local or Hub Hugging Face causal LM;
- convert a Composer `Trainer` checkpoint into a Hugging Face `save_pretrained` folder;
- export a Hugging Face checkpoint to ONNX;
- reason about advanced FasterTransformer or endpoint-generation prerequisites without running those backends;
- diagnose authentication, object-store, dtype/device, memory, ONNX, or backend-load failures in these workflows.

## Operating checklist

1. Identify the artifact the user has now: Hugging Face folder or Hub id, Composer checkpoint, ONNX target folder, FT checkpoint, or endpoint URL.
2. Confirm side effects before taking them: model download, checkpoint conversion, object-store upload, Hugging Face Hub upload, endpoint call, or FT runtime execution.
3. Prefer local, already-available model/checkpoint paths for verification. Do not download private models or upload checkpoints unless the user explicitly provides credentials and asks for it.
4. Run the bundled safe smoke probe first when requirements are unclear:

   ```bash
   python scripts/llmfoundry_inference_smoke.py --help
   ```

5. Route tasks outside this boundary:
   - training or producing Composer checkpoints -> `training-finetuning`;
   - MPT internals, registry, or deep config editing -> `package-apis-configuration`;
   - ICL or benchmark evaluation -> `evaluation`;
   - dataset/tokenization preparation -> `data-preparation`.

## References

- Generation and chat workflows: [references/workflows.md](references/workflows.md)
- Composer/HF/ONNX conversion details: [references/conversion-reference.md](references/conversion-reference.md)
- Optional backends, export prerequisites, and smoke probing: [references/backends-and-export.md](references/backends-and-export.md)
- Failure-mode triage: [references/troubleshooting.md](references/troubleshooting.md)

## Guardrails

- Treat FasterTransformer and endpoint generation as advanced reference-only unless the user explicitly asks to run them and the required external service or library is present.
- Never test Hugging Face Hub upload with `--test_uploaded_model` unless the user accepts a network download/reload and has a valid Hub token.
- `trust_remote_code` is powerful: enable it only for model repos or local folders the user trusts.
- `--device` and `--device_map` are mutually exclusive in the HF generation/chat helpers; choose one loading strategy before execution.
- Keep full training, eval, and model-internal configuration explanations in their owning sub-skills and link back here only for inference/export decisions.
