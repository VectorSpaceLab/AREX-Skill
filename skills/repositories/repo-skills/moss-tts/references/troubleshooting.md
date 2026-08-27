# Cross-cutting MOSS-TTS troubleshooting

Use this root reference when a failure happens before you know which workflow sub-skill owns it, or when a problem spans installation, imports, model assets, backends, and audio files.

## Distribution metadata succeeds but imports fail

Symptoms:

- `moss-tts` appears installed.
- `import moss_tts_delay`, `moss_tts_local`, or related source packages fails.
- A console entry point fails with `ModuleNotFoundError`.

Likely cause: the current package metadata may install distribution metadata without exposing source packages from arbitrary working directories.

Actions:

1. Run `scripts/check_moss_tts_environment.py --json` from this skill to distinguish metadata and import checks.
2. If only metadata works, use a source checkout on `PYTHONPATH`, run from a checkout that exposes packages, or use a fixed packaging layout/wheel.
3. For Hugging Face generation, rely on `trust_remote_code=True` model snapshots when possible.
4. Do not treat metadata-only success as proof that source APIs or CLIs are available.

## Missing torch/transformers/codec stack

Symptoms:

- `ModuleNotFoundError: torch`, `transformers`, `torchaudio`, `torchcodec`, or `flash_attn`.
- Model code imports but audio save/load fails.
- HF examples fail before model download.

Actions:

1. Choose the correct profile in `references/installation-profiles.md`.
2. Install `torch-runtime` for HF generation/training; install FFmpeg for `torchcodec` audio I/O.
3. Add `flash-attn` only when the host supports it. Otherwise set attention to SDPA on CUDA or eager on CPU.
4. Re-run a short import/backend check before loading models.

## CUDA, dtype, and attention mismatch

Symptoms:

- `torch.cuda.is_available()` is false on a GPU host.
- FlashAttention import/build errors.
- `no kernel image is available`, illegal memory access, or dtype errors.
- Generation OOMs immediately.

Actions:

1. Confirm the PyTorch wheel tag matches driver/runtime support.
2. Use `bfloat16`/`float16` only where supported; use `float32` on CPU.
3. Disable unsupported cuDNN SDPA paths if model guidance says so; use SDPA or eager fallback.
4. Reduce `max_new_tokens`, batch size, or use llama.cpp low-memory/TensorRT/ONNX alternatives when appropriate.
5. Do not call GPU generation verified until a tiny tensor allocation and one short model load/generation path succeed.

## Model or codec download/cache failure

Symptoms:

- Hugging Face download errors, missing `config.json`, missing tokenizer files, missing codec path.
- `local_files_only=True` fails.
- Generation starts with a model but fails when loading `audio_tokenizer`.

Actions:

1. Confirm the model id and codec id match the intended family in `references/model-family-overview.md`.
2. If offline, pre-stage model and codec snapshots before setting `local_files_only=True`.
3. Keep model and codec revisions pinned together for reproducibility.
4. Avoid mixing files from different model families unless `sub-skills/hf-family-workflows/references/model-packaging.md` compatibility checks pass.

## Bad audio, gibberish, or shape mismatches

Symptoms:

- Generated audio is empty, noisy, or gibberish.
- Tensor/code shape mismatch mentions `n_vq`, channels, or sampling rate.
- Fine-tuned checkpoint loads but output quality collapses.

Actions:

1. Identify model/code family: Delay, Local 1.0, Local v1.5, TTSD, VoiceGenerator, Realtime, SoundEffect v1, or SoundEffect v2.
2. For TTSD, verify prompt templates/code files and `n_vq=16` alignment.
3. For Local v1.5, preserve 48 kHz stereo and 12-codebook assumptions.
4. For fine-tuning data, run `sub-skills/finetuning-data-prep/scripts/validate_training_jsonl.py` on raw and prepared manifests.
5. Revert to a known-matched model snapshot and change one category at a time: code files, tokenizer, codec, then weights.

## Services do not stream audio

Symptoms:

- FastAPI endpoint returns session id but `/audio` is empty.
- Browser app starts but no PCM playback.
- Realtime text deltas appear but audio lags forever.

Actions:

1. Route to the right service: Local v1.5 browser streaming is `sub-skills/local-v15-streaming`; MOSS-TTS-Realtime voice-agent service is `sub-skills/realtime-voice-agent`.
2. Check model/codec/device placement and GPU memory before starting services.
3. For Realtime, send start, push text chunks, mark final text, drain/flush, then close the session.
4. For Local v1.5 continuation, include a transcript matching the reference audio.
5. Avoid testing a service by opening a long-lived listener during skill verification; use payload/config helpers first.

## SoundEffect v2 conflicts with root runtime

Symptoms:

- Installing SoundEffect v2 changes NumPy/Transformers/Diffusers/Torch versions and breaks root MOSS-TTS.
- `MossSoundEffectPipeline` fails after installing top-level `moss-tts` extras.

Actions:

1. Use `sub-skills/soundeffect-v2/SKILL.md`.
2. Create a separate Python 3.12 environment for SoundEffect v2.
3. Install the v2 CUDA torch extra only in that environment.
4. Use `TORCHDYNAMO_DISABLE=1` when Triton/TorchDynamo compilation fails and speed is less important than getting a result.

## Cheap diagnostics first

- Root environment: `scripts/check_moss_tts_environment.py --json`.
- llama.cpp config: `sub-skills/llama-cpp-backend/scripts/inspect_llama_cpp_config.py`.
- Local v1.5 duration estimates: `sub-skills/local-v15-streaming/scripts/estimate_local_v15_tokens.py`.
- Realtime session payloads: `sub-skills/realtime-voice-agent/scripts/realtime_session_payloads.py`.
- Fine-tuning JSONL: `sub-skills/finetuning-data-prep/scripts/validate_training_jsonl.py`.
- SoundEffect v2 metadata: `sub-skills/soundeffect-v2/scripts/validate_soundeffect_metadata.py`.
