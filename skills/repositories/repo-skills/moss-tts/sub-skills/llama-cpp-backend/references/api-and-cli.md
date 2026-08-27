# API and CLI operation

## Command-line entry points

The backend exposes both a console script and a Python module:

```bash
moss-tts-llama-cpp --config <config.yaml> --text "Hello, world!" --output output.wav
python -m moss_tts_delay.llama_cpp --config <config.yaml> --text "Hello, world!" --output output.wav
```

Voice cloning with reference audio:

```bash
moss-tts-llama-cpp \
  --config <config.yaml> \
  --text "Speak this sentence in the reference voice." \
  --reference reference.wav \
  --language en \
  --output cloned.wav
```

Useful overrides:

```bash
moss-tts-llama-cpp \
  --config <config.yaml> \
  --text "Short smoke test." \
  --output smoke.wav \
  --heads-backend numpy \
  --n-gpu-layers 0 \
  --max-tokens 256 \
  --profile
```

Supported CLI flags:

| Flag | Purpose |
|---|---|
| `--config` | Required YAML path. |
| `--text` | Required synthesis text. |
| `--reference` | Optional reference WAV for zero-shot voice cloning. |
| `--output` | Output WAV path; defaults to `output.wav`. |
| `--instruction` | Optional instruction text inserted into the generation prompt. |
| `--quality` | Optional quality control field inserted into the prompt. |
| `--language` | Optional language field such as `en` or `zh`. |
| `--tokens` | Optional prompt token-control field. |
| `--max-tokens` | Overrides `max_new_tokens`. |
| `--text-temp` | Overrides text sampling temperature. |
| `--audio-temp` | Overrides audio-code sampling temperature. |
| `--audio-rep-penalty` | Overrides audio repetition penalty. |
| `--n-gpu-layers` | Overrides llama.cpp GPU offload. |
| `--heads-backend` | One of `auto`, `numpy`, `torch`. |
| `--low-memory` | Forces staged low-memory mode. |
| `--profile` | Prints timing and optional GPU-memory summaries. |

## Python API

```python
from moss_tts_delay.llama_cpp import LlamaCppPipeline, PipelineConfig
import soundfile as sf

config = PipelineConfig.from_yaml("config.yaml")
config.heads_backend = "numpy"      # optional override
config.max_new_tokens = 512          # optional bounded smoke-test override

with LlamaCppPipeline(config) as pipeline:
    waveform = pipeline.generate(
        text="Hello, world!",
        reference_audio=None,         # or a WAV path / float32 NumPy waveform
        instruction=None,
        tokens=None,
        quality=None,
        language="en",
    )

sf.write("output.wav", waveform, 24000)
```

`generate()` returns a `float32` NumPy waveform sampled at **24 kHz**. If a string reference is supplied, the backend reads it with `soundfile`; if its sample rate is not 24 kHz, `librosa` is needed for resampling.

## Pipeline behavior

The generation path is:

```text
text + optional reference audio
  -> Rust tokenizers BPE tokenizer
  -> prompt builder producing (sequence, 33) IDs
  -> NumPy embedding lookup
  -> llama.cpp GGUF backbone through libbackbone_bridge.so
  -> text logits + hidden state
  -> NumPy or Torch LM heads for 32 audio codebooks
  -> NumPy delay-state machine and top-k/top-p sampling
  -> audio codes
  -> ONNX, TensorRT, or Torch audio tokenizer decode
  -> loudness-normalized 24 kHz waveform
```

The 33 channels are one text channel plus 32 RVQ audio channels. The delay state staggers the audio codebooks diagonally, then de-delays generated codes before audio decoding.

## Audio tokenizer backend choices

| `audio_backend` | Required config | Runtime characteristics |
|---|---|---|
| `onnx` | `audio_encoder_onnx`, `audio_decoder_onnx`, `use_gpu_audio` | Torch-free. Works on CPU or GPU depending on ONNX Runtime build and `use_gpu_audio`. Recommended starting point. |
| `trt` | `audio_encoder_trt`, `audio_decoder_trt` | Torch-free. Fastest audio tokenizer, but engines must be built locally and match the deployment GPU/TensorRT/CUDA stack and shape limits. |
| `torch` | `audio_model_name_or_path`, optional `use_gpu_audio` | Uses PyTorch + Transformers remote-code model loading. Not torch-free and incompatible with `low_memory: true`. |

Low-memory mode can load only the encoder for reference encoding, then unload it, load the llama.cpp backbone plus embeddings/heads for generation, unload them, and finally load the decoder. This lowers peak VRAM but prevents true streaming decode during generation; a callback receives the final waveform after decode.

## LM-head backend choices

| `heads_backend` | Behavior |
|---|---|
| `numpy` | Fully torch-free. LM-head matmul is CPU-bound and can use several GB of host RAM for the 33 `.npy` heads. Best for CPU and 8 GB GPU profiles. |
| `torch` | Requires PyTorch import and CUDA availability for the intended acceleration path. Fails fast if Torch is unavailable. |
| `auto` | Uses Torch only when CUDA Torch is importable; otherwise falls back to NumPy. Good for convenience, but pin `numpy` for reproducible torch-free deployments. |

## Config loading and validation

`PipelineConfig.from_yaml(path)` accepts top-level keys matching the dataclass. Unknown keys are ignored with a warning by the package. Relative path fields are resolved against a discovered project root when possible, then against the config directory and current working directory.

`PipelineConfig.validate()` enforces:

- `audio_backend` is one of `onnx`, `trt`, `torch`.
- `heads_backend` is one of `auto`, `numpy`, `torch`.
- `low_memory: true` is not combined with `audio_backend: torch`.
- Core paths exist: `backbone_gguf`, `embedding_dir`, `lm_head_dir`, `tokenizer_dir`.
- Backend-specific paths exist for ONNX or TRT.
- `audio_model_name_or_path` is nonempty for Torch audio.

Use the bundled inspector before model loading:

```bash
python <this-skill>/scripts/inspect_llama_cpp_config.py <config.yaml>
```

## Practical generation tips

- Start with a short sentence and `--max-tokens 128` or `256` for smoke testing.
- Use `--profile` to see prefill, generation, decode, total RTF, and GPU-memory snapshots when GPU monitoring is available.
- If prompt length is close to `n_ctx`, shorten text/reference audio or increase `n_ctx` with a matching VRAM budget.
- Use `n_gpu_layers: 0` to force CPU backbone, `-1` to offload all possible layers, or a positive number for partial offload.
- Pin `heads_backend: numpy` when validating a torch-free deployment; `auto` can silently use Torch on one machine and NumPy on another.
- Keep `audio_temperature`, `audio_top_p`, and `audio_top_k` near the provided defaults when comparing quality to released quantization numbers.
