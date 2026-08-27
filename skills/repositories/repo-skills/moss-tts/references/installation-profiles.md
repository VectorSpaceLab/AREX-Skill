# Installation profiles

Read this before installing dependencies, diagnosing import failures, or deciding whether a CPU check is enough for a MOSS-TTS task.

## Choose the smallest matching profile

| Profile | Command shape | Covers | Do not use for |
|---|---|---|---|
| Metadata/lightweight helpers | `python -m pip install -e .` plus any small helper deps | package metadata, bundled validators, normalizer, lightweight llama.cpp config inspection | torch model generation, training, SoundEffect v2 |
| HF generation runtime | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime]"` | Delay/Local/Reatime HF model loading, `torchcodec`, `transformers`, `accelerate` | torch-free deployment or SoundEffect v2 |
| HF generation + FlashAttention | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime,flash-attn]"` | faster/lower-memory CUDA attention when supported | CPU-only hosts or unsupported GPUs |
| Fine-tuning | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime,finetune]"` | preprocessing, SFT, Accelerate/W&B-oriented workflows | DeepSpeed ZeRO-3 unless extra below is installed |
| Fine-tuning + DeepSpeed | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime,finetune-deepspeed]"` | ZeRO-3 style training | ordinary inference or DDP/FSDP-only training |
| llama.cpp ONNX | `python -m pip install -e ".[llama-cpp-onnx]"` | torch-free Delay-family backend with ONNX audio tokenizer | TensorRT engine path or full HF torch generation |
| llama.cpp TensorRT | `python -m pip install -e ".[llama-cpp-trt]"` | TensorRT audio tokenizer after user builds machine-specific engines | hosts without CUDA/TensorRT engine build support |
| llama.cpp Torch heads | `python -m pip install -e ".[llama-cpp-onnx,llama-cpp-torch]"` | optional torch-accelerated LM heads | strict torch-free deployments |
| SoundEffect v2 | install the `moss-soundeffect-v2` package in its own clean Python 3.12 environment with its torch CUDA extra | DiT sound-effect pipeline, v2 fine-tune/export | root MOSS-TTS runtime; dependency sets conflict |

Replace the CUDA wheel tag with the host's supported PyTorch backend when necessary. The repository documents CUDA 12.8-style wheels for current releases; CPU, older CUDA, ROCm, or MPS paths require deliberate wheel selection and separate verification.

## Host prerequisites

- Python: top-level MOSS-TTS supports Python `>=3.10`; current docs prefer Python 3.12. SoundEffect v2 requires Python 3.12 and has a distinct dependency stack.
- FFmpeg: required for `torchcodec` audio I/O in HF generation/training profiles.
- CUDA GPU: practically required for large model generation, realtime streaming, and training. CPU can validate metadata and some parser/config helpers, but CPU is not proof that generation/training is viable.
- FlashAttention: optional; requires a supported NVIDIA GPU, matching torch/CUDA ABI, and fp16/bf16-style dtype.
- TensorRT: optional for llama.cpp audio tokenizer; engines are machine-specific and are not shipped prebuilt.
- Hugging Face/model cache: full generation paths need model and codec snapshots; set `local_files_only=True` only after assets are cached or present locally.

## Package exposure caveat

The current top-level package metadata can install `moss-tts` distribution metadata while failing to expose source packages such as `moss_tts_delay` from arbitrary current working directories. The symptom is:

```text
importlib.metadata.version("moss-tts") succeeds
import moss_tts_delay fails with ModuleNotFoundError
```

Safe recovery options:

1. Run from a source checkout that is already on Python's import path.
2. Set `PYTHONPATH` to the checkout root for the process that needs local source imports.
3. Use a packaging layout/wheel that explicitly includes the package directories.
4. For HF model generation, prefer `AutoProcessor.from_pretrained(..., trust_remote_code=True)` and `AutoModel.from_pretrained(..., trust_remote_code=True)` so the model snapshot supplies remote-code files.

Do not call an environment ready for source-package inspection until both distribution metadata and the intended imports work.

## Verification checklist

Before expensive work, run cheap gates:

```bash
python scripts/check_moss_tts_environment.py --json
```

Then add workflow-specific checks:

- HF generation: import `torch`, `transformers`, `torchaudio`, `torchcodec`; query `torch.cuda.is_available()` when CUDA is selected; confirm FFmpeg is installed for audio I/O.
- llama.cpp: run `moss-tts-llama-cpp --help` or module help; use `sub-skills/llama-cpp-backend/scripts/inspect_llama_cpp_config.py` on the intended config.
- Local v1.5: confirm codec v2, stereo 48 kHz expectations, and device split before starting the streaming app.
- Realtime: confirm server/client dependencies and a single-GPU or multi-GPU placement plan before starting long-lived services.
- Fine-tuning: validate JSONL with `sub-skills/finetuning-data-prep/scripts/validate_training_jsonl.py` before codec preprocessing or SFT.
- SoundEffect v2: validate metadata with `sub-skills/soundeffect-v2/scripts/validate_soundeffect_metadata.py` in the separate v2 workflow.

## When to stop and ask for runtime approval

Ask before:

- downloading multi-GB model/checkpoint assets;
- building FlashAttention or TensorRT engines;
- starting FastAPI/Gradio services;
- running any training/preprocessing job over real datasets;
- rewriting/fusing multi-GB safetensors;
- changing system packages such as FFmpeg, CUDA drivers, or compilers.
