# Cross-Cutting Troubleshooting

Read this when a Huatuo/BenTsao workflow fails before the issue is clearly owned by one sub-skill.

## Dependency and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | Torch is imported by model scripts but is not listed in the documented dependency file. | Install a Torch build compatible with the intended CPU/CUDA backend before installing or running the rest of the ML stack. |
| `ModuleNotFoundError` for `peft`, `transformers`, `datasets`, `fire`, `gradio`, or `wandb` | Task-specific dependencies were skipped or installed in another environment. | Install only the dependencies for the selected workflow; do not install serving/training extras for a format-only task. |
| PEFT or Transformers API errors while loading adapters | Version mismatch between legacy repo code and installed libraries. | Prefer versions close to the documented stack, then run a small import/help check before loading model weights. |
| bitsandbytes or 8-bit errors | Incompatible CUDA/Torch/bitsandbytes build, or CPU-only runtime. | Disable 8-bit for diagnosis or install a compatible CUDA/bitsandbytes combination for the GPU. |

## Model and adapter asset failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Base model path/id cannot be resolved | Model weights are absent, gated, private, or network downloads were not authorized. | Provide a local path or explicitly authorize/download the model. |
| Adapter path lacks `adapter_config.json` or `adapter_model.bin` | Directory is not a PEFT LoRA adapter or extraction/download is incomplete. | Use a complete adapter directory and verify it matches the base-model family. |
| Nonsensical or repeated outputs | Wrong template, wrong adapter for base model, generation settings, low-quality base model for Chinese medical QA, or expected stochastic variation. | Recheck model family, adapter, template, response split, and generation defaults; compare only with explicit caveats. |

## CUDA, memory, and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NameError: device is not defined` in batch/literature inference | The observed inference scripts define `device` only when CUDA is available. | Run on a CUDA-capable environment or adapt the runtime to set a CPU/MPS device explicitly; do not claim CPU execution was validated. |
| CUDA out of memory | 7B model, long prompts, large batch/micro-batch, or half/8-bit setting mismatch. | Lower batch or micro-batch size, shorten cutoff/max tokens, disable simultaneous runs, or use a larger GPU. |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only Torch wheel, driver/runtime mismatch, or no container GPU passthrough. | Install the correct Torch CUDA wheel and verify a tiny CUDA tensor allocation before running model code. |

## Template and format failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Can't read templates/<name>.json` | Template lookup is relative to the current working directory in the original helper. | Run from an asset root containing `templates/`, or adapt runtime code to pass an explicit template path. |
| Output includes prompt text or parsing fails | `response_split` does not match the generated prompt template. | Validate the template with `prompt-data-formats/scripts/validate_assets.py` and match template to model/workflow. |
| Training data loads incorrectly | JSON array vs JSONL confusion, missing `instruction`/`input`/`output`, or non-string fields. | Use the prompt/data validator or the fine-tuning builder's `--validate-data` option before training. |

## Serving and medical-safety failures

- Do not expose Gradio serving broadly (`0.0.0.0` or share links) unless explicitly approved.
- Treat all medical model responses as research output, not clinical advice.
- If a user asks for clinical use, route to risk/disclaimer handling and human expert review rather than treating model output as authoritative.

## When to stop and ask for assets or authorization

Stop instead of proceeding silently when a task requires:

- Downloading gated or large base-model weights.
- Downloading or trusting external LoRA adapters.
- Running expensive GPU inference/training/export.
- Exposing a medical model service on a network.
- Using outputs for diagnosis, treatment, or patient-facing advice.
