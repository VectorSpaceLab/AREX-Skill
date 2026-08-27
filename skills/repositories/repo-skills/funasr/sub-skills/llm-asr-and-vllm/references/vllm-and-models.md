# vLLM and LLM-ASR model reference

## Purpose

Read this when deciding whether a FunASR LLM-ASR checkpoint should use standard `AutoModel`, FunASR `AutoModelVLLM`, a direct Nano/GLM vLLM engine, or Qwen3-ASR's external runtime. This reference distills the package's model-family checks and public examples into a self-contained routing guide.

## Model-family routing table

| User-facing family | Typical model id | Standard `AutoModel` | FunASR `AutoModelVLLM` | Notes |
|---|---|---:|---:|---|
| Fun-ASR-Nano | `FunAudioLLM/Fun-ASR-Nano-2512` | Yes | Yes | LLM-based ASR with a SenseVoice-style audio encoder and Qwen3 decoder. Use vLLM for CUDA batch throughput; use `AutoModel` for simple or non-vLLM runs. |
| Fun-ASR-MLT-Nano | `FunAudioLLM/Fun-ASR-MLT-Nano-2512` | Yes | Same Nano family caveats | Multilingual Nano checkpoint. Treat timestamp/CTC output as optional because the current MLT checkpoint may not include complete `ctc_decoder.*` and `ctc.*` weights. Text transcription should still be available. |
| GLM-ASR-Nano | `zai-org/GLM-ASR-Nano-2512` or `ZhipuAI/GLM-ASR-Nano-2512` | Yes | Yes | vLLM path extracts the language model portion and decodes prompt embeddings. It is best for short/fixed segments; do not assume long-audio dynamic VAD support. |
| LLMASR / LLMASRNAR | Custom Whisper+LLM configs | Usually advanced/custom | Yes when config exposes the LLM-ASR pattern | Supported by the generic `AutoModelVLLM` wrapper, but not the common first route for package users. Verify the config before recommending it. |
| Qwen3-ASR | `Qwen/Qwen3-ASR-0.6B`, `Qwen/Qwen3-ASR-1.7B` | Yes, through the FunASR wrapper around `qwen-asr` | **No** | It is LLM-based, but FunASR's `AutoModelVLLM` explicitly rejects it because Qwen3-ASR uses the external `qwen-asr` package with its own optimized inference stack. |
| Paraformer / SenseVoice / Conformer / CT-Transformer | Common non-LLM ASR or punctuation models | Yes | **No** | vLLM accelerates autoregressive LLM decoding, not non-autoregressive CIF/CTC/attention or small punctuation models. Use the generic ASR route. |

`AutoModelVLLM`'s package-level applicability check returns `True` for `FunASRNano`, `GLMASR`, `LLMASR`, `LLMASRNAR`, and `QwenAudioWarp`; it raises a clear error for known non-applicable families such as `Paraformer`, `SenseVoice`, `Conformer`, `CTTransformer`, and `Qwen3ASR`.

## Which runtime to choose

### Use standard `AutoModel` when

- The user wants a one-off transcription, subtitles, ordinary CLI/API guidance, or a CPU-capable path.
- The model family is non-LLM or Qwen3-ASR.
- The machine lacks `vllm`, a CUDA-capable vLLM build, enough VRAM, or a tested accelerator runtime.
- Long audio should be segmented automatically by a high-level FunASR pipeline rather than passed as one huge vLLM prompt.

### Use FunASR `AutoModelVLLM` when

- The model is Fun-ASR-Nano, Fun-ASR-MLT-Nano, GLM-ASR-Nano, or an LLMASR-style config that passes the applicability check.
- The goal is offline/batch throughput or controlled SDK integration on a CUDA/vLLM environment.
- The full FunASR checkpoint root is available. Do not point `model` at an inner LLM config-only directory.
- You can accept vLLM startup cost and GPU memory reservation.

### Use Qwen3-ASR's external runtime when

- The model is `Qwen/Qwen3-ASR-*` and the user specifically wants Qwen3-ASR or its streaming/vLLM acceleration.
- The environment has a compatible `qwen-asr`, `transformers`, and `accelerate` set.
- For qwen-asr's native vLLM/streaming stack, keep the vLLM version pinned by `qwen-asr[vllm]`; do not replace it with a FunASR `AutoModelVLLM` installation recipe.

## Minimal diagnostic

From this sub-skill directory, run:

```bash
python scripts/check_vllm_ready.py --model-family Fun-ASR-Nano --target auto --device cuda:0 --dtype bf16
```

Useful variants:

```bash
# Explain why a non-LLM family should use standard AutoModel.
python scripts/check_vllm_ready.py --model-family Paraformer --target auto-model-vllm

# Check Qwen3 package compatibility without suggesting FunASR AutoModelVLLM.
python scripts/check_vllm_ready.py --model-family Qwen3-ASR --target qwen3-native --check-qwen3

# Emit machine-readable status for a higher-level verification script.
python scripts/check_vllm_ready.py --model-family GLM-ASR-Nano --dtype fp16 --json
```

The helper inspects imports, distribution versions, model-family routing, dtype/device caveats, and exact next steps. It intentionally does not download models or initialize vLLM.

## FunASR `AutoModelVLLM` usage pattern

Use this pattern only after the diagnostic says the family is applicable and `vllm` is available:

```python
from funasr.auto.auto_model_vllm import AutoModelVLLM

model = AutoModelVLLM(
    model="FunAudioLLM/Fun-ASR-Nano-2512",  # or a local full checkpoint root
    hub="ms",                              # or "hf"
    device="cuda:0",
    dtype="bf16",
    tensor_parallel_size=1,
    gpu_memory_utilization=0.8,
    max_model_len=4096,
)

results = model.generate(
    ["audio_001.wav", "audio_002.wav"],
    language="中文",
    hotwords=["开放时间", "张三"],
    temperature=0.0,
    top_p=1.0,
    repetition_penalty=1.0,
)
for item in results:
    print(item["key"], item["text"])
```

Expected result shape is a list of dictionaries with at least `key` and `text`. Timestamp fields are optional and appear only when CTC/timestamp components are fully initialized.

## Direct Nano/GLM vLLM engines

Use direct engines when a task needs engine-specific parameters or internal API behavior instead of the generic wrapper.

### Fun-ASR-Nano direct engine

```python
from funasr.models.fun_asr_nano.inference_vllm import FunASRNanoVLLM

engine = FunASRNanoVLLM.from_pretrained(
    model="FunAudioLLM/Fun-ASR-Nano-2512",
    hub="ms",
    device="cuda:0",
    dtype="bf16",
    tensor_parallel_size=1,
)
results = engine.generate(
    inputs=["audio.wav"],
    language="中文",
    hotwords=["开放时间"],
    max_new_tokens=512,
    temperature=0.0,
    repetition_penalty=1.0,
)
```

### GLM-ASR direct engine

```python
from funasr.models.glm_asr.inference_vllm import GLMASRVLLMEngine

engine = GLMASRVLLMEngine.from_pretrained(
    model="zai-org/GLM-ASR-Nano-2512",
    hub="hf",
    device="cuda:0",
    dtype="bf16",
)
results = engine.generate(
    ["short_segment.wav"],
    prompt="转录以下音频内容",
    max_new_tokens=500,
    temperature=0.0,
    repetition_penalty=1.0,
)
```

GLM result keys are derived from audio basenames and are de-duplicated when repeated basenames would otherwise collide.

## Qwen3-ASR usage pattern

Use standard FunASR `AutoModel` for the packaged Qwen3-ASR wrapper:

```python
from funasr import AutoModel

model = AutoModel(
    model="Qwen/Qwen3-ASR-1.7B",
    hub="hf",          # use "ms" where ModelScope is preferred
    device="cuda:0",
    dtype="bf16",
)
results = model.generate(
    input=["audio.wav"],
    language="Chinese",  # short aliases such as "zh" are normalized by the wrapper
    context="optional domain context",
)
print(results[0]["text"])
```

Dependencies for the wrapper should be compatible with the installed `qwen-asr` package. The documented baseline is:

```bash
pip install -U "qwen-asr==0.0.6" "transformers==4.57.6" accelerate
```

For Qwen3-ASR's own vLLM/streaming stack, use `qwen_asr.Qwen3ASRModel` as directed by that package and install the matching extra, for example:

```bash
pip install -U "qwen-asr[vllm]==0.0.6" "transformers==4.57.6" accelerate
```

Do not substitute FunASR `AutoModelVLLM` for this path.

## Weight preparation rules

- Fun-ASR-Nano checkpoints store audio encoder, adaptor, and LLM tensors together. The vLLM helper extracts tensors whose keys begin with `llm.` and writes a vLLM-ready language-model directory next to the checkpoint files. It copies the tokenizer/config from the nested Qwen3 LLM config directory.
- GLM-ASR vLLM preparation extracts tensors whose keys begin with `language_model.` from safetensors files, writes a language-model-only directory, and adapts the text config for Llama-style vLLM loading.
- If the vLLM-ready directory already contains safetensors or model binary files, the helper reuses it.
- Missing `model.pt`, missing nested config/tokenizer files, or missing `llm.*` / `language_model.*` tensors are checkpoint-preparation problems, not audio-input problems.
- Do not serve a config-only nested LLM directory directly with vLLM when using the FunASR split-engine path; point FunASR at the full checkpoint root.

## Dtype, device, and decoding defaults

- Prefer `dtype="bf16"` for Nano/GLM on modern CUDA GPUs.
- Use `dtype="fp32"` on GPUs without bfloat16 support, or while isolating numerical issues.
- Treat `dtype="fp16"` as a compatibility fallback only; Nano and GLM warn that fp16 can produce degraded or garbage transcription because of numerical overflow in the audio-embedding path.
- Let `vllm` determine the matching `torch` / `torchaudio` / `torchvision` wheel set. Installing those packages independently can create CUDA ABI mismatches before FunASR starts.
- Choose the vLLM version by the NVIDIA driver CUDA capability shown by the host, not by a random preinstalled runtime. Driver CUDA 12.x commonly needs a CUDA-12 vLLM build; newer drivers may use newer vLLM builds.
- Keep `temperature=0.0`, `top_p=1.0`, and `repetition_penalty=1.0` for prompt-embeds ASR paths. Non-neutral repetition penalties are clamped by FunASR helpers because prompt-embeds mode has no prompt token IDs to penalize and can crash vLLM.
- Pre-segment long recordings with VAD or use a high-level `AutoModel` path with VAD. Passing very long audio to a segment-level vLLM model can truncate or degrade output.

## Backend notes

- CUDA/vLLM is the intended acceleration path for Fun-ASR-Nano and GLM-ASR-Nano throughput.
- CPU can validate routing, imports, and standard `AutoModel` behavior, but it is not proof of vLLM throughput.
- Ascend/NPU evidence is compatibility-oriented, not a production recommendation. Separate PyTorch `AutoModel` validation from `AutoModelVLLM` validation because vLLM-Ascend can fail in Qwen rotary or operator conversion layers even when PyTorch `AutoModel` reaches the backend.
- Realtime service tuning, OpenAI-compatible endpoints, and deployment topology are owned by the serving sub-skill; return here only for the model family, dtype, and vLLM applicability decisions.
