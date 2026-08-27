# llama.cpp backend troubleshooting

## First diagnostic order

1. Inspect YAML without model loading:

   ```bash
   python <this-skill>/scripts/inspect_llama_cpp_config.py <config.yaml>
   ```

2. Confirm required paths exist for the selected `audio_backend`.
3. Confirm `libbackbone_bridge.so` is present and can resolve `libllama`.
4. Run a short CPU or low-token smoke test before long generation:

   ```bash
   moss-tts-llama-cpp --config <config.yaml> --text "Smoke test." --max-tokens 128 --output smoke.wav --profile
   ```

## Missing C bridge or llama.cpp library

Symptoms:

- `Cannot find libbackbone_bridge.so`
- dynamic linker errors for `libllama`
- `Failed to load model` immediately after bridge loading

Fixes:

- Build `libbackbone_bridge.so` beside the installed `moss_tts_delay.llama_cpp` files.
- Compile llama.cpp first; the bridge links against `-lllama`.
- Use the correct llama.cpp library directory in both `-L` and runtime rpath.
- Rebuild the bridge after changing llama.cpp versions or moving the llama shared library.
- Check whether the installed package is in a read-only location; if so, install in an editable/user-writable environment or place the library in another searched package build directory.

## Missing GGUF, embeddings, LM heads, or tokenizer

Symptoms:

- `backbone_gguf: ... does not exist`
- `embedding_dir: ... does not exist`
- `lm_head_dir: ... does not exist`
- `tokenizer.json not found`
- shape mismatch during embedding/head operations

Fixes:

- Use a config whose paths point to the actual downloaded or converted artifacts.
- Keep GGUF, embeddings, LM heads, and tokenizer from the same checkpoint/version.
- Ensure `embedding_dir` contains `embed_tokens.npy` plus 32 `emb_ext_*.npy` files.
- Ensure `lm_head_dir` contains `lm_head_text.npy` plus 32 `lm_head_audio_*.npy` files.
- Ensure `tokenizer_dir/tokenizer.json` exists; optional tokenizer metadata files are useful but `tokenizer.json` is the hard requirement.
- Do not point `backbone_gguf` at a safetensors directory or full Hugging Face model directory.

## ONNX audio backend issues

Symptoms:

- ONNX Runtime provider not found.
- CUDA execution provider load failure.
- Encoder/decoder ONNX path missing.
- Audio decode errors after successful text/audio-code generation.

Fixes:

- For CPU-only, install CPU ONNX Runtime and set `use_gpu_audio: false`.
- For GPU ONNX, install a GPU ONNX Runtime build compatible with the local CUDA/cuDNN stack and set `use_gpu_audio: true`.
- Verify both `audio_encoder_onnx` and `audio_decoder_onnx` exist.
- If GPU provider fails, switch temporarily to CPU audio to isolate whether the issue is audio runtime or backbone/bridge.

## TensorRT backend issues

Symptoms:

- `audio_encoder_trt` or `audio_decoder_trt` missing.
- TensorRT import or engine deserialization failure.
- Engine works on one GPU but not another.
- Long reference/audio fails because engine shapes are too small.

Fixes:

- Build TensorRT engines locally from the ONNX encoder/decoder; prebuilt engines are not portable and are not shipped.
- Rebuild engines after TensorRT, CUDA, driver, GPU architecture, precision, or max-shape changes.
- Use ONNX backend first to validate weights and prompt behavior before debugging TensorRT.
- For long audio/reference cases, rebuild engines with larger max shapes. Larger max shapes can increase memory.

## Torch audio backend issues

Symptoms:

- PyTorch/Transformers import failure.
- remote-code model loading error.
- `low_memory mode requires audio_backend='trt' or 'onnx'`.

Fixes:

- Use `audio_backend: onnx` or `trt` for torch-free deployments.
- Use Torch audio only when a PyTorch/Transformers environment and `audio_model_name_or_path` are intentionally available.
- Do not combine `audio_backend: torch` with `low_memory: true`; the split encoder/decoder loading path is implemented only for ONNX/TRT.
- Treat external Hugging Face downloads as explicit setup steps; predownload or use a local model path in restricted/offline deployments.

## LM-head backend issues

Symptoms:

- `heads_backend: torch` fails because Torch is missing.
- `auto` behaves differently across machines.
- GPU memory unexpectedly high.

Fixes:

- Pin `heads_backend: numpy` for torch-free and 8 GB GPU profiles.
- Use `heads_backend: torch` only after proving PyTorch + CUDA is working.
- Avoid `auto` for reproducibility; it uses Torch when CUDA Torch is importable, otherwise NumPy.
- Remember NumPy heads use CPU matmul and host RAM; Torch heads use GPU memory but can be much faster.

## Low-memory and 8 GB GPU tradeoffs

Low-memory mode stages components:

1. load encoder only for reference encoding;
2. unload encoder;
3. load backbone, embeddings, and LM heads for generation;
4. unload generation components;
5. load decoder for waveform decoding.

Tradeoffs:

- Lower peak VRAM, suitable for 8 GB-class GPUs when paired with Q4_K_M, `heads_backend: numpy`, and `n_ctx: 4096`.
- More load/unload overhead and slower end-to-end latency.
- True streaming decode is unavailable; callback delivery is final-waveform only.
- Increasing `n_ctx` grows KV-cache memory. Check memory before moving from 4096 to 6144/8192.
- `flash_attn: enabled` can reduce prefill VRAM when supported.
- Quantized KV cache (`q8_0`, `q4_0`) can reduce memory but should be evaluated for quality/regression risk.

## `n_gpu_layers` and CUDA/driver limits

- `n_gpu_layers: -1` asks llama.cpp to offload all possible layers.
- `n_gpu_layers: 0` forces CPU backbone.
- Positive values partially offload layers.

If CUDA/driver/VRAM is insufficient:

1. Set `n_gpu_layers: 0` to prove the rest of the stack works on CPU.
2. Try partial offload.
3. Reduce `n_batch` if prefill fails.
4. Keep `n_ctx` at 4096 or lower for smoke tests.
5. Use `heads_backend: numpy` to avoid extra GPU memory.
6. Use ONNX CPU audio or staged low-memory mode to isolate the failing component.

## External Hugging Face downloads and offline environments

The backend needs two artifact groups: GGUF/side weights/tokenizer and audio tokenizer models. In restricted networks:

- Download artifacts ahead of time on a machine with access.
- Point YAML fields to local artifact paths.
- Avoid `audio_backend: torch` unless the Torch audio tokenizer model is also available locally.
- Never let a production run start before the config inspector confirms local paths for the selected backend.

## Batch-evaluation layout failures

Symptoms:

- No cases discovered.
- All cases skipped.
- Results missing `pred.wav`.
- Summary has many failures with missing labels/prompts.

Fixes:

- Use layout `<benchmark-dir>/<task>/<case-id>/label.txt` with optional `prompt.wav`.
- Use known task names or explicitly add language mappings for custom tasks.
- Disable skip-existing behavior when rerunning changed configs.
- Treat empty waveform as failure.
- Store `run_meta.json` with config, sampling, model, and backend values so metrics can be traced.
- For TensorRT, confirm engine max shape covers the longest prompt/reference duration in the benchmark.
