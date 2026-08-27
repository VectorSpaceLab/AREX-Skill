# Alpamayo R1 inference troubleshooting

## Hugging Face gated access

**Symptom:** model or dataset download fails with a 401 / 403 / gated-resource error.

**Likely cause:** you have not been granted access to the Alpamayo R1 weights or the PhysicalAI-AV dataset, or the local HF token is missing.

**Fix:**

1. Request access to both gated resources on Hugging Face.
2. Authenticate before running inference.
3. Confirm the token is available to the runtime that launches the smoke script.

The inference path needs both the model weights and the PhysicalAI-AV clip data.

## CUDA out of memory / insufficient VRAM

**Symptom:** `torch.cuda.OutOfMemoryError`, launch failure while loading the model, or OOM during sampling.

**Likely cause:** the 10B model plus vision stack and trajectory sampling exceed available VRAM.

**Fix:**

- Use an NVIDIA GPU with at least 24 GB VRAM.
- Keep `num_traj_samples=1` while debugging.
- Reduce `max_generation_length` if you are exploring longer reasoning traces.
- Close other GPU-heavy workloads before starting inference.

The repo's bundled smoke script uses the low-memory default `num_traj_samples=1` for this reason.

## flash-attn build or runtime issues

**Symptom:** `flash_attn` fails to import, the model crashes while loading with `flash_attention_2`, or you see compiler / build-toolchain errors during installation.

**Likely cause:** the local CUDA toolchain is incomplete, `CUDA_HOME` points to the wrong toolkit, or the current GPU / driver combination is incompatible with the flash-attn build.

**Fix:**

- Keep the CUDA path as the primary route when it works.
- Ensure the CUDA toolkit is visible to the build environment before reinstalling flash-attn.
- Set `CUDA_HOME` to the active toolkit prefix when building from source, and make sure a CUDA compiler is available.
- If flash-attn is still not viable, reload the model with `attn_implementation="sdpa"` on the config or model load call.

SDPA is a fallback for compatibility problems; do not treat it as a full replacement for the normal CUDA path.

## Device mismatch / missing CUDA backend

**Symptom:** `Expected all tensors to be on the same device`, `CUDA is not available`, or a CPU tensor sneaks into the model inputs.

**Likely cause:** the model, processor output, or history tensors were not moved together to the same CUDA device.

**Fix:**

- Check `torch.cuda.is_available()` before loading the model.
- Move the model to the same device you pass to `helper.to_device`.
- Run `helper.to_device({...}, "cuda")` on the whole model-input bundle, not on only part of it.
- Keep the autocast context on the same CUDA device.

## Invalid clip id or too-early `t0_us`

**Symptom:** the loader raises `ValueError` or the dataset interface cannot find the requested clip.

**Likely cause:** the clip id is not accessible in the gated dataset, or `t0_us` is inside the history window.

**Fix:**

- Reuse a validated PhysicalAI-AV clip id.
- Keep `t0_us > num_history_steps * time_step * 1_000_000`.
- With the default settings, `t0_us` must be greater than `1_600_000` microseconds.
- Leave `maybe_stream=True` if the clip is not already cached locally.

## Incorrect frame rank or unsupported prompt construction

**Symptom:** `helper.create_message` raises `ValueError: ... expected 4 (N, C, H, W)` or the text trace looks malformed.

**Likely cause:** the frame tensor was not flattened to 4D, or the chat template was changed so the assistant turn no longer continues the prompt correctly.

**Fix:**

- Call `data["image_frames"].flatten(0, 1)` before `create_message`.
- Keep `add_generation_prompt=False` and `continue_final_message=True` in `apply_chat_template`.
- Use the Alpamayo processor built from `helper.get_processor(model.tokenizer)`.
- Do not switch to a generic Qwen tokenizer without Alpamayo's trajectory tokens.

## Reusing tokenized input after one call

**Symptom:** a second inference call fails because `input_ids` is missing.

**Likely cause:** `sample_trajectories_from_data_with_vlm_rollout` pops `tokenized_data["input_ids"]` during generation.

**Fix:**

- Rebuild the processor output for each run, or
- Deep-copy the tokenized input before the first call if you need to reuse it.

## Unexpected text output or missing Chain-of-Causation trace

**Symptom:** `extra["cot"]` is empty, `meta_action` is missing, or the output text does not line up with the trajectories.

**Likely cause:** `return_extra=True` was omitted, the prompt was malformed, or the model stopped early because the generation settings were too tight.

**Fix:**

- Pass `return_extra=True` when you need the text trace.
- Keep the default `top_p=0.98` and `temperature=0.6` first, then tune gradually.
- Increase `max_generation_length` only if you explicitly need longer reasoning traces.
