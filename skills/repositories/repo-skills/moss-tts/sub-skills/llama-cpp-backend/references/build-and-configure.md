# Build and configure the llama.cpp backend

This backend is for **MOSS-TTS-Delay** inference with the Qwen3 backbone in GGUF format. It can be torch-free when using NumPy LM heads and ONNX/TensorRT audio tokenizers; PyTorch is optional only for faster LM heads or for the Torch audio tokenizer.

## Installation profiles

Install only the backend mix you intend to use:

| Profile | Command pattern | Main dependencies | When to use |
|---|---|---|---|
| CPU ONNX | `pip install -e ".[llama-cpp]"` plus CPU `onnxruntime` | NumPy, PyYAML, tokenizers, soundfile, CPU ONNX Runtime | No GPU or CUDA driver; slow but portable. |
| Torch-free ONNX GPU | `pip install -e ".[llama-cpp-onnx]"` | Adds `onnxruntime-gpu` | Recommended first GPU profile; no PyTorch required. |
| Torch-free TensorRT | `pip install -e ".[llama-cpp-trt]"` | Adds TensorRT and cuda-python | Maximum audio-tokenizer speed; engines must be built for the local GPU/TensorRT version. |
| Torch LM heads | `pip install -e ".[llama-cpp-onnx,llama-cpp-torch]"` or with `llama-cpp-trt` | Adds PyTorch | Optional acceleration for LM-head matmuls; not required for torch-free operation. |

The console entry point is `moss-tts-llama-cpp`; the module entry point is `python -m moss_tts_delay.llama_cpp`.

## Required model and tokenizer layout

A default config expects paths equivalent to this layout under a user-selected weights root:

```text
MOSS-TTS-GGUF/
  MOSS_TTS_Q4_K_M.gguf
  embeddings/
    embed_tokens.npy
    emb_ext_00.npy ... emb_ext_31.npy
  lm_heads/
    lm_head_text.npy
    lm_head_audio_00.npy ... lm_head_audio_31.npy
  tokenizer/
    tokenizer.json
    tokenizer_config.json             # optional but commonly present
    special_tokens_map.json           # optional but commonly present
    added_tokens.json / merges.txt / vocab.json as available
MOSS-Audio-Tokenizer-ONNX/
  encoder.onnx
  decoder.onnx
MOSS-Audio-Tokenizer-TRT/
  encoder.engine                      # user-built, not shipped prebuilt
  decoder.engine                      # user-built, not shipped prebuilt
```

Prebuilt public artifacts are normally downloaded from:

```bash
huggingface-cli download OpenMOSS-Team/MOSS-TTS-GGUF --local-dir <weights-root>/MOSS-TTS-GGUF
huggingface-cli download OpenMOSS-Team/MOSS-Audio-Tokenizer-ONNX --local-dir <weights-root>/MOSS-Audio-Tokenizer-ONNX
```

TensorRT engines are intentionally not shipped because they are tied to GPU architecture, TensorRT version, CUDA version, precision flags, and maximum shape choices. Build them from the ONNX encoder/decoder on the deployment machine.

## C bridge build requirements

The Python backend uses a shared library named `libbackbone_bridge.so` to feed precomputed embeddings into llama.cpp and read hidden states/logits. The package searches for that library next to the installed `moss_tts_delay.llama_cpp` Python files and in nearby build directories.

Build prerequisites:

1. A llama.cpp checkout compiled from source with shared-library support.
2. C compiler support for `-shared` and `-fPIC`.
3. llama.cpp headers under `include/` and `ggml/include/`.
4. A built llama library under one of `build/bin`, `build/src`, or `build`.

Manual build pattern:

```bash
python - <<'PY'
from pathlib import Path
import moss_tts_delay.llama_cpp.backbone as backbone
print(Path(backbone.__file__).resolve().parent)
PY

# Let PKG_LLAMA_CPP_DIR be the printed directory, and LLAMA_CPP_DIR be a built llama.cpp tree.
gcc -shared -fPIC -O2 \
  -o "${PKG_LLAMA_CPP_DIR}/libbackbone_bridge.so" \
  "${PKG_LLAMA_CPP_DIR}/backbone_bridge.c" \
  -I"${LLAMA_CPP_DIR}/include" \
  -I"${LLAMA_CPP_DIR}/ggml/include" \
  -L"${LLAMA_CPP_DIR}/build/bin" \
  -lllama \
  -Wl,-rpath,"${LLAMA_CPP_DIR}/build/bin"
```

If the llama library was built under `build/src` or directly under `build`, change the `-L` and `-Wl,-rpath` directory accordingly. Verify that the resulting shared object can resolve `libllama` before running inference.

## YAML profiles

The backend consumes a top-level YAML mapping matching `PipelineConfig`. Four common profiles are:

| Profile | Key settings | Purpose |
|---|---|---|
| `default` | `audio_backend: onnx`, `heads_backend: auto`, `n_gpu_layers: -1`, `use_gpu_audio: true` | Recommended GPU start using ONNX audio and auto Torch heads if available. |
| `cpu-only` | `audio_backend: onnx`, `heads_backend: numpy`, `n_gpu_layers: 0`, `use_gpu_audio: false`, higher `n_threads` | Fully CPU path; no CUDA required. |
| `trt` | `audio_backend: trt`, `audio_encoder_trt`, `audio_decoder_trt`, `heads_backend: auto`, `n_gpu_layers: -1` | High-throughput audio tokenizer with locally built engines. |
| `trt-8gb` | `audio_backend: trt`, `heads_backend: numpy`, `low_memory: true`, `flash_attn: enabled`, `n_ctx: 4096`, `n_gpu_layers: -1` | Staged loading for 8 GB-class GPUs. |

Minimal ONNX GPU config:

```yaml
backbone_gguf: weights/MOSS-TTS-GGUF/MOSS_TTS_Q4_K_M.gguf
embedding_dir: weights/MOSS-TTS-GGUF/embeddings
lm_head_dir: weights/MOSS-TTS-GGUF/lm_heads
tokenizer_dir: weights/MOSS-TTS-GGUF/tokenizer

audio_backend: onnx
audio_encoder_onnx: weights/MOSS-Audio-Tokenizer-ONNX/encoder.onnx
audio_decoder_onnx: weights/MOSS-Audio-Tokenizer-ONNX/decoder.onnx

heads_backend: auto
n_ctx: 4096
n_batch: 512
n_threads: 4
n_gpu_layers: -1
max_new_tokens: 3072
use_gpu_audio: true

text_temperature: 1.5
text_top_p: 1.0
text_top_k: 50
audio_temperature: 1.7
audio_top_p: 0.8
audio_top_k: 25
audio_repetition_penalty: 1.0
```

Minimal CPU config changes:

```yaml
heads_backend: numpy
n_batch: 256
n_threads: 8
n_gpu_layers: 0
use_gpu_audio: false
audio_backend: onnx
```

Low-memory 8 GB changes:

```yaml
audio_backend: trt
heads_backend: numpy
low_memory: true
use_gpu_audio: true
n_ctx: 4096
n_gpu_layers: -1
kv_cache_type_k: f16
kv_cache_type_v: f16
flash_attn: enabled
```

## Important config keys

| Key | Values | Effect |
|---|---|---|
| `backbone_gguf` | path | GGUF Qwen3 backbone. Required for all modes. |
| `embedding_dir` | path | Directory of text and external audio embedding `.npy` files. Required. |
| `lm_head_dir` | path | Directory of text and 32 audio LM-head `.npy` files. Required. |
| `tokenizer_dir` | path | Directory containing `tokenizer.json`. Required. |
| `audio_backend` | `onnx`, `trt`, `torch` | Audio tokenizer implementation. |
| `audio_encoder_onnx`, `audio_decoder_onnx` | paths | Required when `audio_backend: onnx`. |
| `audio_encoder_trt`, `audio_decoder_trt` | paths | Required when `audio_backend: trt`. |
| `audio_model_name_or_path` | model id or path | Required when `audio_backend: torch`. |
| `heads_backend` | `auto`, `numpy`, `torch` | `auto` uses Torch only if CUDA Torch is importable; `numpy` is torch-free; `torch` fails fast if Torch is unavailable. |
| `n_gpu_layers` | `-1`, `0`, or positive int | llama.cpp GPU offload: all layers, CPU only, or first N layers. |
| `low_memory` | bool | Staged load/unload of encoder, backbone, and decoder. Requires ONNX or TRT audio, not Torch audio. |
| `n_ctx` | int | Context window for prompt plus generated steps. Increase only with VRAM awareness. |
| `n_batch` | int | llama.cpp prefill batch size. Lower this if prefill memory spikes. |
| `kv_cache_type_k`, `kv_cache_type_v` | `f32`, `f16`, `bf16`, `q8_0`, `q5_0`, `q4_0` | KV-cache memory/quality tradeoff. |
| `flash_attn` | `auto`, `enabled`, `disabled` | llama.cpp flash-attention selection; enabling can reduce prefill VRAM. |
| sampling keys | numeric | Separate text and audio temperature/top-k/top-p plus audio repetition penalty. |
