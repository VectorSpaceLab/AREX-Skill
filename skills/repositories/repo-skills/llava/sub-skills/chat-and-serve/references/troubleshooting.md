# Chat and Serve Troubleshooting

## Missing CUDA or unsupported backend

**Symptoms**
- `torch.cuda.is_available()` is false.
- The worker or CLI fails while moving tensors to CUDA.
- A model load succeeds on CPU-only import checks but generation cannot start.

**Likely causes**
- CPU-only Torch was installed.
- The GPU driver/runtime is unavailable in the current container.
- The checkpoint is too large for the selected GPU memory.

**Recovery**
- Reinstall the pinned CUDA-enabled stack.
- Use a smaller checkpoint or quantization where supported.
- Reduce worker concurrency.
- Re-run `scripts/check_chat_runtime.py` and the root `scripts/check_install.py --require-cuda` helper.

## LoRA checkpoint warnings

**Symptoms**
- The loader warns that `lora` is present in the model name but `model_base` is missing.
- Answers look wrong or the load path falls back to a partial model.

**Recovery**
- Supply the base model that matches the adapter family.
- If you want merged weights, use the train sub-skill's merge or apply-delta guidance first.

## Gradio starts but no model appears

**Symptoms**
- The UI opens, but the model list is empty.

**Likely causes**
- No worker registered with the controller.
- The controller URL or port is wrong.
- The worker crashed while loading the checkpoint.

**Recovery**
- Start controller first, then worker, then Gradio.
- Confirm the worker and controller ports match.
- Use `--model-list-mode reload` in Gradio.
- Check worker logs for checkpoint or CUDA errors.

## Worker prompt/image mismatch

**Symptoms**
- `Number of images does not match number of <image> tokens in prompt`.

**Likely causes**
- The prompt text and image list are out of sync.
- The template or placeholder was copied from another model family.

**Recovery**
- Count the `<image>` tokens after conversation formatting.
- Use the model family template table in the image reference.
- Prefer the bundled command builder over hand-editing the prompt.

## Quantization and platform limitations

**Symptoms**
- `--load-4bit` or `--load-8bit` fails on macOS or Windows.
- bitsandbytes import errors appear.

**Recovery**
- Use Linux/CUDA for quantized serving.
- On macOS, stay with supported 16-bit inference and `--device mps` when available.
- On Windows, prefer WSL2 for the full Linux-like stack.

## SGLang optional backend missing

**Symptoms**
- The optional SGLang worker cannot import `sglang`.
- The worker expects an endpoint that is not running.

**Recovery**
- Treat SGLang as an optional alternate backend, not a required baseline.
- Install `sglang[all]` separately and start a matching backend endpoint before launching the worker.
