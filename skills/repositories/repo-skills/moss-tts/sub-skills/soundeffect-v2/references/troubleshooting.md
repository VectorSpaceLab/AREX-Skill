# MOSS-SoundEffect v2 troubleshooting

## Separate environment conflicts

Symptoms:

- Installing into an existing MOSS-TTS environment downgrades or upgrades core packages unexpectedly.
- Import errors mention incompatible `transformers`, `diffusers`, `numpy`, `torch`, `torchaudio`, or `gradio` versions.
- Delay-family MOSS-TTS workflows break after installing SoundEffect v2.

Likely cause:

- MOSS-SoundEffect v2 is a separate Python 3.12+ package with pinned runtime dependencies and PyTorch 2.9 CUDA 12.8 pins. It is not compatible with the top-level MOSS-TTS environment.

Fix:

1. Create a fresh Python 3.12+ environment.
2. Install SoundEffect v2 there, not into the existing MOSS-TTS environment.
3. Use the PyTorch CUDA 12.8 index when installing `torch-cu128`.
4. Re-check `python -c "import moss_soundeffect_v2; print(moss_soundeffect_v2.__all__)"` inside the new environment.

## Missing `torch-cu128` wheels or PyTorch index

Symptoms:

- Pip cannot find `torch==2.9.0+cu128`, `torchaudio==2.9.0+cu128`, or `torchvision==0.24.0+cu128`.
- Pip resolves CPU or non-CUDA wheels when CUDA 12.8 was intended.
- Errors include `No matching distribution found for torch==2.9.0+cu128`.

Likely cause:

- The PyTorch CUDA 12.8 wheel index was not supplied, or the Python/platform combination is unsupported.

Fix:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 \
  -e ".[torch-cu128]"
```

For fine-tuning:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 \
  -e ".[torch-cu128,finetune]"
```

Then verify:

```bash
python - <<'PY'
import torch, torchaudio
print(torch.__version__)
print(torchaudio.__version__)
print(torch.cuda.is_available())
PY
```

If CUDA is unavailable but the install is otherwise healthy, use `device="cpu"` only for import or tiny smoke tests; full generation is usually impractical on CPU.

## Hugging Face model download and cache failures

Symptoms:

- `from_pretrained("OpenMOSS-Team/MOSS-SoundEffect-v2.0")` fails during snapshot download.
- Errors mention network timeouts, permissions, missing repo files, or offline mode.
- Export with a repo id fails before copying frozen modules.

Likely cause:

- The model id must resolve through Hugging Face Hub unless a complete local directory is supplied.

Fix:

1. Confirm model id or local model directory spelling.
2. For private or gated mirrors, pass an appropriate token through the pipeline `from_pretrained` kwargs or authenticate with Hugging Face tooling.
3. For offline runs, pre-populate the Hugging Face cache and call `from_pretrained(..., local_files_only=True)`.
4. For export, use a complete local `SOURCE_HF_DIR` when network access is unreliable.
5. A valid source model directory must include `vae`, `text_encoder`, `tokenizer`, and `scheduler`; `model_index.json` and `transformer/config.json` are copied when present.

## TorchDynamo, Triton, or CUDA Graph compile errors

Symptoms:

- First inference stalls for a long time before producing audio.
- Errors mention TorchDynamo, `torch.compile`, Triton, CUDA Graph capture, invalid kernel, or compilation cache.
- Training fails while compiling VAE encode.

Likely cause:

- The DiT inference path and VAE training encode path can use compiled CUDA acceleration. Some driver/GPU/compiler combinations fail compilation even when eager execution works.

Fix:

Set TorchDynamo off before launching Python:

```bash
TORCHDYNAMO_DISABLE=1 python your_soundeffect_v2_command.py
```

For shell-style inference or Gradio:

```bash
TORCHDYNAMO_DISABLE=1 \
SOUNDEFFECT_MODEL_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0 \
SOUNDEFFECT_DEVICE=cuda \
python -m clis.moss_sound_effect_app
```

If disabling TorchDynamo fixes the issue, keep it in the runtime launch configuration. Expect slower first and steady-state performance than the compiled path.

## CUDA memory pressure

Symptoms:

- `torch.cuda.OutOfMemoryError` during load, inference, cache building, or training.
- The Gradio backend starts but fails when a request arrives.
- Fine-tuning fails during VAE/text-context cache generation or backward pass.

Likely cause:

- Duration, steps, batch size, cache workers, and model size all affect memory. The pipeline denoises the full configured maximum duration, then crops to requested `seconds`.

Fixes for inference:

1. Use `torch_dtype=torch.bfloat16` on CUDA.
2. Lower `seconds` for testing.
3. Lower `num_inference_steps` for smoke tests.
4. Run one request at a time; the Gradio queue already uses one generation concurrency.
5. Restart the process after OOM to clear fragmented CUDA state.

Fixes for fine-tuning:

1. Keep `BATCH_SIZE=1` and increase `GRADIENT_ACCUMULATION_STEPS` instead of batch size.
2. Reduce `DATASET_NUM_WORKERS` if CPU workers and caches increase memory pressure.
3. Use `--use_gradient_checkpointing_offload` only when host memory and speed trade-offs are acceptable.
4. Use a smaller sample length only when the downstream task can accept shorter training audio.

## Unsupported or excessive duration/steps

Symptoms:

- `ValueError: seconds must be > 0`.
- `ValueError: seconds=<x> exceeds max_inference_seconds=<y>`.
- Runs take much longer than expected.

Facts:

- `seconds` is rounded to one decimal place.
- Default maximum is 30 seconds unless `model_index.json` changes it.
- Gradio constrains duration to 1-30 seconds and steps to 10-150.
- Python pipeline calls allow other step values, but high values can be slow.

Fix:

- For a smoke test, use `seconds=1.0` and `num_inference_steps=10`.
- For normal quality, start from `seconds=10`, `num_inference_steps=100`, `cfg_scale=4.0`, `sigma_shift=5.0`.
- Do not request a duration above `pipe.max_inference_seconds` unless you know the loaded model supports it.

## Missing metadata `audio` or `prompt`

Symptoms:

- Fine-tuning loader warns it cannot load files or that `prompt` is not a string.
- Training silently skips samples or returns `None` items.
- Validation fails with missing field errors.

Required JSONL row shape:

```json
{"audio": "wavs/example.wav", "prompt": "A clear sound-effect caption."}
```

Fix:

1. Ensure every non-empty JSONL line is a JSON object.
2. Ensure every object has non-empty string `audio` and `prompt` fields.
3. Validate before training:

```bash
# From this sub-skill directory, or replace <this sub-skill> with its installed path.
python scripts/validate_soundeffect_metadata.py \
  --metadata captions.jsonl \
  --dataset-base ./soundeffects \
  --check-audio-exists
```

4. If the training launch expects paths it can open directly, use absolute `audio` paths or resolve relative paths against the intended dataset base before launching.

## Export fails because `SOURCE_HF_DIR` or frozen modules are missing

Symptoms:

- Export raises `FileNotFoundError` for `vae`, `text_encoder`, `tokenizer`, or `scheduler`.
- Export writes a transformer directory but the result cannot load.
- `SOURCE_HF_DIR` points to a fine-tune output that does not contain the frozen modules.

Likely cause:

- Export replaces only the DiT transformer weights. It must copy frozen components from the source model directory/repo id used for fine-tuning.

Fix:

1. Set `SOURCE_HF_DIR` to the complete base model directory or repo id, not to a partial checkpoint directory.
2. Confirm these source subdirectories exist: `vae`, `text_encoder`, `tokenizer`, `scheduler`.
3. Confirm `CKPT_PATH` points to a DiT `.safetensors` checkpoint, such as `epoch-0.safetensors` or a saved step checkpoint.
4. Export again and load the resulting `OUTPUT_DIR` with `MossSoundEffectPipeline.from_pretrained(OUTPUT_DIR)`.

## Exported model shape or key mismatch

Symptoms:

- Loading exported `transformer/diffusion_pytorch_model.safetensors` fails with missing or unexpected keys.
- The model loads but output is silent or corrupted after fine-tuning.

Likely cause:

- The checkpoint is not a SoundEffect v2 DiT checkpoint in the expected custom key naming, or `REMOVE_PREFIX_IN_CKPT` was changed incorrectly during training.

Fix:

- Keep training default `TRAINABLE_MODELS=dit` and `REMOVE_PREFIX_IN_CKPT=pipe.dit.` unless you also update export expectations.
- Export from checkpoints produced by the SoundEffect v2 fine-tuning module.
- Use the same base `SOURCE_HF_DIR` family/version that was used to initialize training.

## Gradio `SOUNDEFFECT_MODEL_DIR` and device problems

Symptoms:

- Demo starts with a placeholder model path and fails immediately.
- Demo uses CPU unexpectedly.
- Startup takes a long time before the page is responsive.
- Reverse-proxy paths or public sharing do not behave as expected.

Facts:

- `SOUNDEFFECT_MODEL_DIR` defaults the model directory/repo id; override it for real use.
- `SOUNDEFFECT_DEVICE` defaults to `cuda`, but the backend falls back to CPU when CUDA is unavailable.
- The backend is preloaded at startup, so model download/compilation happens before launch completes.
- `--root_path` or `GRADIO_ROOT_PATH` is required for some reverse-proxy mount paths.
- Queue concurrency is one generation at a time.

Fix:

```bash
SOUNDEFFECT_MODEL_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0 \
SOUNDEFFECT_DEVICE=cuda \
TORCHDYNAMO_DISABLE=1 \
python -m clis.moss_sound_effect_app --host 0.0.0.0 --port 7861
```

If CUDA is unavailable, decide explicitly whether a slow CPU demo is acceptable. For production demos, use a CUDA host and pre-warm the model before exposing the endpoint.

## Fine-tuning cache and resume issues

Symptoms:

- Cache generation restarts from scratch unexpectedly.
- Training resumes from a state but step/epoch metadata is inconsistent.
- Cache files exist but samples are skipped.

Fix:

- If `--cache_first` is set, ensure `--cache_folder` is provided.
- Delete a bad cache folder before rebuilding; the launcher treats existing cache metadata as populated.
- Use `--resume_from` only with a compatible accelerator/model logger state directory.
- Keep metadata stable between cache creation and training.
