---
name: nemo
description: "Use for NVIDIA NeMo Speech ASR, TTS, audio processing, SpeechLM2
  and voice-agent workflows, speaker diarization, data tooling, and repository
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NeMo

Use this repo skill for NVIDIA NeMo Speech tasks involving automatic speech recognition, text-to-speech, audio-to-audio processing, SpeechLM2 and voice-agent workflows, speaker diarization, data preparation/tools, or maintaining the NeMo Speech repository.

NeMo Speech is a PyTorch speech AI toolkit. The active user-facing areas in this skill are ASR, TTS, audio, SpeechLM2, speaker tasks, shared data/tools, and repo development. The generated skill is self-contained: use the bundled sub-skill references and helper scripts instead of relying on the original checkout's docs, examples, tests, or scripts being present.

## Install And Import Check

Prefer the current public install guidance when preparing a NeMo runtime environment:

```bash
# Source checkout, reproducible supported stack.
uv sync --extra all --extra cu13

# Bring-your-own Python/PyTorch/CUDA stack.
uv pip install 'nemo-toolkit[asr,tts,audio,speechlm2]'

# Minimal import check for an installed environment.
python -c "import nemo; print(nemo.__version__)"
```

Use Python 3.12+, PyTorch 2.7+, and a CUDA-capable NVIDIA GPU for training. CPU-only inference may work for small checks but is slow and not representative for production speech workloads. Avoid `uv sync --locked` when the user explicitly wants to keep an existing PyTorch/CUDA stack.

Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout. If the commit, dirty state, package version, active collections, examples, or docs have changed, refresh the skill before relying on version-sensitive commands.

## Route By Task

- `sub-skills/asr/SKILL.md`: ASR model selection, `.nemo`/pretrained checkpoint loading, transcription, timestamps, streaming/cache-aware inference, fine-tuning, Lhotse batching, tokenizer changes, decoding customization, ASR evaluation, and ASR troubleshooting.
- `sub-skills/tts/SKILL.md`: TTS synthesis, FastPitch/HiFi-GAN cascades, MagpieTTS/EasyMagpie, G2P, audio codecs, TTS manifests, text/phoneme preprocessing, finetuning, evaluation, and TTS checkpoint troubleshooting.
- `sub-skills/audio/SKILL.md`: Audio enhancement, restoration, denoising, separation, beamforming, predictive/generative audio-to-audio models, audio manifests, evaluation, augmentation export, and multi-channel audio handling.
- `sub-skills/speechlm2/SKILL.md`: SpeechLM2/SALM/SALMAutomodel, duplex STT/S2S/EAR-TTS, Nemotron VoiceChat, HuggingFace conversion, vLLM plugin integration, voice-agent configuration, and Automodel backend troubleshooting.
- `sub-skills/speaker-diarization/SKILL.md`: Speaker recognition, embeddings, diarization, VAD, Sortformer diarization, ASR+diarization scoring, forced alignment, RTTM/CTM manifests, and speaker workflow troubleshooting.
- `sub-skills/data-tools/SKILL.md`: Shared NeMo JSON manifests, Lhotse and tarred datasets, duration bins, dataset weights, tokenizer utilities, ASR evaluator, CTC segmentation, speech data explorer/simulator, checkpoint utilities, and safe data validation.
- `sub-skills/repo-development/SKILL.md`: Repository maintenance, install variants, code style, focused tests, docs builds, bug reproduction, optional backend decisions, native verification, and PR/CI guidance.

## Common Decisions

- Start with the task's collection sub-skill, then route to `data-tools` only for shared data validation, conversion, sharding, tokenizer, or evaluation utilities.
- Keep ASR transcription/fine-tuning separate from speaker diarization and forced alignment; use `speaker-diarization` for RTTM, CTM, VAD, speaker embeddings, and NFA-style alignment tasks.
- Keep classic TTS synthesis and G2P in `tts`; use `speechlm2` only when the task involves SALM, duplex speech-to-speech, Nemotron VoiceChat, vLLM, HuggingFace export, or voice-agent services.
- Use bundled helper scripts for safe preflight validation before launching long GPU, model-download, training, checkpoint-conversion, or dataset-conversion jobs.
- Treat original NeMo examples and scripts as evidence. If a user wants to run source checkout examples, first verify the repo checkout, dependencies, hardware, data paths, and command safety with the relevant sub-skill.

## Bundled Helper Scripts

Each helper is safe by default and standard-library-only unless the sub-skill says otherwise:

- ASR: `sub-skills/asr/scripts/check_asr_manifest.py`
- TTS: `sub-skills/tts/scripts/check_tts_manifest.py`
- Audio: `sub-skills/audio/scripts/check_audio_manifest.py`
- SpeechLM2: `sub-skills/speechlm2/scripts/check_speechlm2_config.py`
- Speaker/diarization: `sub-skills/speaker-diarization/scripts/check_speaker_manifest.py`
- Data/tools: `sub-skills/data-tools/scripts/validate_manifest.py`
- Repo development: `sub-skills/repo-development/scripts/select_tests.py`

Run helpers from the nearest sub-skill directory, for example:

```bash
cd sub-skills/asr
python scripts/check_asr_manifest.py train.jsonl --canary --min-duration 0.1 --max-duration 30
```

## Troubleshooting First Steps

1. Confirm the correct collection extra is installed: `asr`, `tts`, `audio`, `speechlm2`, or a deliberate `all` install.
2. Confirm the user's PyTorch/CUDA stack before changing NeMo dependencies; do not replace a bring-your-own PyTorch install accidentally.
3. Validate manifests/configs with the bundled helper in the owning sub-skill before running long jobs.
4. For Hydra overrides, quote strings/lists deliberately and null conflicting settings when switching batch modes.
5. For checkpoint workflows, distinguish `.nemo`, PyTorch Lightning `.ckpt`, HuggingFace/safetensors, and distributed checkpoint directories before loading or converting.
6. For repository changes, reproduce the issue with a minimal test, add the test, fix the root cause, and run focused tests plus `isort --check` and `black --check` on changed Python paths.
