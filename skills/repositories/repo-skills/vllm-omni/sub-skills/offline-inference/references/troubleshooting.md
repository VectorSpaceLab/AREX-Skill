# Offline inference troubleshooting

Use this when local `Omni`/`AsyncOmni` scripts fail, produce missing modality payloads, or appear unsafe to run. Prefer fixing the smallest script first; only escalate to deploy/offload/parallel changes when the request itself is valid.

## Version mismatch warning

Symptom examples:

- Importing `vllm_omni` prints a warning that vLLM and vLLM-Omni major/minor versions are misaligned.
- `vllm` CLI behavior does not match vLLM-Omni docs or `--omni` is not handled as expected.
- Imports work, but runtime behavior is strange after mixing editable installs and wheel installs.

Actions:

1. Inspect package versions in the target environment:

   ```python
   import vllm
   import vllm_omni
   print("vllm", vllm.__version__)
   print("vllm_omni", vllm_omni.__version__)
   ```

2. Align the major/minor release family of `vllm` and `vllm_omni`.
3. If using an editable/dev checkout whose SCM version does not resemble the paired vLLM release, treat the warning as a compatibility risk until an import probe and a small non-model helper pass.
4. Recreate the environment instead of layering unrelated vLLM versions into the same prefix when imports become inconsistent.

## Model cache, gated repository, or network failures

Symptom examples:

- `Repository not found`, `GatedRepoError`, `401`, `403`, or license/access errors.
- Model construction hangs or fails while resolving weights.
- The user expected offline use, but the model id triggers a download.

Actions:

1. Prefer a local model directory path when the user has already downloaded weights.
2. For gated models, the user must accept the license/request access with the model host and authenticate the environment before model construction.
3. Set cache environment variables only if the user asks or the runtime environment already uses them; do not hard-code private cache paths in reusable scripts.
4. Use `scripts/build_offline_request.py` to generate code without loading the model when network/cache status is uncertain.
5. Do not run full model examples just to validate syntax. Validate script syntax and argument construction first.

## CUDA OOM or worker killed during generation

Symptom examples:

- CUDA out-of-memory exception.
- Worker exits, engine dead errors, silent process death, or a request never finishes.
- OOM appears only with multiple prompts or high frame count.

Request-level mitigations first:

- Lower `height`/`width` for image/edit tasks.
- Lower `num_frames`, `fps`/`frame_rate`, or output resolution for video tasks.
- Lower concurrent prompts or `max_in_flight` for `AsyncOmni`.
- Use fewer `num_outputs_per_prompt`.
- For chat models, reduce `max_tokens` and media count/size.
- For TTS/audio, stream chunks to disk instead of accumulating all chunks when the script supports it.

Then route deeper decisions:

- Offload, HSDP, tensor/sequence/ring/CFG parallelism, quantization, VAE tiling/slicing, cache backends, and per-stage memory limits belong to model-recipes and stage-configuration.
- Do not guess deploy YAML changes from an offline script. Build a small reproduction and then plan the stage/memory change.

## Missing image output

Symptom examples:

- `outputs[0].images` is empty.
- `final_output_type` is not `image` when an image was expected.
- The script returns an object but saving `.images[0]` fails.

Checks:

1. Confirm the prompt has explicit image routing for diffusion image generation:

   ```python
   {"prompt": "...", "modalities": ["image"]}
   ```

2. Inspect all known image locations:

   ```python
   for output in outputs:
       print(output.final_output_type, output.finished, output.to_dict() if hasattr(output, "to_dict") else output)
       print("images", len(getattr(output, "images", []) or []))
       mm = getattr(output, "multimodal_output", None)
       print("mm keys", list(mm.to_dict().keys() if hasattr(mm, "to_dict") else getattr(mm, "keys", lambda: [])()))
   ```

3. Check `output.images`, then `output.multimodal_output['image']`, `['images']`, or `['model_outputs']`.
4. For tensor payloads, detach and convert on CPU before saving.
5. For image-to-image/edit, verify `multi_modal_data={'image': PIL_image_or_supported_list}` and that the target model supports the number of input images.

## Missing audio output or empty WAV

Symptom examples:

- Text is produced but no audio is saved.
- `output.outputs[0].multimodal_output` lacks `audio`.
- Async flow writes only the final chunk or repeats chunks.

Checks:

1. Select audio output when the model supports multiple final modalities:

   ```python
   omni = Omni(model=model, output_modalities=["audio"])
   # or per request with AsyncOmni.generate(..., output_modalities=["audio"])
   ```

2. Inspect both AR and diffusion-style locations:

   ```python
   mm = None
   if output.outputs:
       mm = getattr(output.outputs[0], "multimodal_output", None)
   if not mm:
       mm = getattr(output, "multimodal_output", None)
   ```

3. Audio may be a tensor or a list of chunks. Concatenate list chunks along the last dimension when possible, then flatten CPU data before writing.
4. Sample rate may be `sr`, `sample_rate`, `audio_sample_rate`, or nested metadata. Fall back only when the model documentation says a default sample rate is correct.
5. In async delta flows, only write new chunks once. Track the number of consumed list entries if the payload is cumulative.

## Missing or unexpected video output

Symptom examples:

- Video generation returns `final_output_type='image'`.
- Frames appear inside `images`, a tuple, or a dict rather than a `video` key.
- Audio accompanying video is missing.

Actions:

- Treat video diffusion frames as image-like payloads unless the model explicitly returns `multimodal_output['video']`.
- Check `output.images`; a single item may be:
  - a list of frames,
  - a tuple `(frames, audio)`, or
  - a dict with `frames`, `video`, `audio`, and/or `audio_sample_rate`.
- Also check `output.multimodal_output` for `audio`, `audio_sample_rate`, `fps`, and nested `metadata.video.fps`.
- Lower `num_frames`, `height`, and `width` before changing the deploy configuration.

## Latents or trajectory fields are missing

Symptom examples:

- `output.latents` or `output.trajectory_latents` is `None`.
- `return_trajectory_latents=True` appears ignored.

Actions:

1. Confirm the target model/pipeline supports latent or trajectory return.
2. Set the relevant request flags:

   ```python
   OmniDiffusionSamplingParams(
       return_trajectory_latents=True,
       return_trajectory_decoded=True,
   )
   ```

3. Check both direct and trajectory-specific fields: `latents`, `trajectory_latents`, `trajectory_timesteps`, `trajectory_log_probs`, `trajectory_decoded`, and `custom_output`.
4. Do not assume trajectory payloads are serializable; detach tensors and move to CPU first.

## Sampling parameter shape/type errors

Common causes:

- Passing a plain dict as `sampling_params_list` instead of `OmniDiffusionSamplingParams` or vLLM `SamplingParams`.
- Passing a per-stage list whose length does not match the resolved pipeline.
- Using a list prompt with `AsyncOmni.generate` for a diffusion-stage pipeline.
- Putting offload/parallel/cache settings in `OmniDiffusionSamplingParams` instead of constructor/deploy kwargs.

Fixes:

- Single diffusion request: `omni.generate(prompt, OmniDiffusionSamplingParams(...))`.
- Multi-stage request: start from `omni.default_sampling_params_list`, clone, and replace the diffusion-stage object.
- Async diffusion batching: submit one task/request per prompt; do not pass a list prompt to one `AsyncOmni.generate` call.
- Route deployment, parallelism, offload, cache, and quantization to the appropriate sibling sub-skill.

## Unsafe full-model examples

Many full-model examples are intentionally not safe as smoke tests because they can:

- download large/gated model weights,
- require CUDA or a vendor accelerator with substantial VRAM,
- assume local media files or demo assets,
- start multiple workers/processes,
- write output directories, logs, or profiler traces,
- run for a long time or consume benchmark-scale resources.

Use them only as conceptual patterns already distilled into this sub-skill. For quick validation, run safe code generation (`scripts/build_offline_request.py --help`) and syntax checks on generated snippets. Run live model inference only after the user confirms model cache/access, hardware, output path, and time budget.

## Lifecycle cleanup

- `Omni.generate(..., py_generator=False)` returns after completion but the `Omni` object may still own workers. Call `omni.close()` when done.
- `Omni.generate(..., py_generator=True)` closes the object when the generator is fully consumed, but explicit `finally: omni.close()` is still safe.
- `AsyncOmni` should be shut down in `finally` with `async_omni.shutdown()`.
- On exceptions, the entrypoints attempt to abort active requests; still perform normal cleanup in the caller.
