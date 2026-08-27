---
name: speechlm2
description: "Use for NeMo SpeechLM2/SALM/SALMAutomodel, duplex STT/S2S/EAR-TTS,
  Nemotron VoiceChat, HuggingFace export/conversion, vLLM plugin, Automodel
  backends, and voice-agent troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechLM2

Use this sub-skill for NeMo SpeechLM2 speech-LLM work: SALM/SALMAutomodel, duplex STT and speech-to-speech models, Duplex EAR-TTS inside SpeechLM2 pipelines, Nemotron VoiceChat, HuggingFace/safetensors export, the NeMo SpeechLM vLLM plugin, Automodel optional compiled backends, and local voice-agent configuration.

This guidance is self-contained. It distills repository evidence from `docs/source/speechlm2/intro.rst`, `docs/source/speechlm2/models.rst`, `docs/source/speechlm2/datasets.rst`, `docs/source/speechlm2/configs.rst`, `docs/source/speechlm2/training_and_scaling.rst`, `docs/source/checkpoints/intro.rst`, `examples/speechlm2/*.py`, `examples/speechlm2/conf/*.yaml`, `examples/voice_agent/**`, `nemo/collections/speechlm2/**`, `nemo/agents/voice_agent/**`, and `tests/collections/speechlm2/**`.

## Route Here When

- The task mentions `nemo.collections.speechlm2`, `SALM`, `SALMAutomodel`, `SALMWithAsrDecoder`, `DuplexS2SModel`, `DuplexS2SSpeechDecoderModel`, `DuplexSTTModel`, `DuplexEARTTS`, or `NemotronVoiceChat`.
- The user needs speech+LLM generation, SpeechLM2 training configs, Lhotse conversation datasets, duplex speech-to-speech/STT evaluation, or SpeechLM2 inference with audio placeholder tokens.
- The task involves SpeechLM2 HuggingFace export, `model.safetensors`, distributed checkpoint consolidation, `NemotronVoiceChat.from_pretrained`, or vLLM serving with `nemo_speechlm`.
- The task involves NeMo voice-agent server/client configuration, tool calling, vLLM/HF LLM backend selection, streaming ASR/TTS service composition, or backchannel/turn-taking settings.

## Route Elsewhere

- Classic ASR transcription, ASR fine-tuning, CTC/RNNT decoding, Parakeet/Canary model recipes, or ASR manifests belong in `../asr/SKILL.md` unless SpeechLM2 is explicitly involved.
- TTS-only FastPitch, HiFiGAN, Magpie, Kokoro, or speech synthesis outside a SpeechLM2/Nemotron VoiceChat/voice-agent pipeline belongs in `../tts/SKILL.md`.
- Repo development, test authoring, packaging, lint, CI, and source-tree maintenance belong in the repo-development sub-skill when available.

## First Steps

1. Identify the workflow: SALM generation/eval, SALM/SALMAutomodel training, duplex STT/S2S, Duplex EAR-TTS inference, Nemotron VoiceChat, HF export, vLLM serving, or voice-agent deployment.
2. Read `references/workflows.md` for the concrete API/command-shape workflow and safe adaptation notes.
3. Read `references/configuration.md` before editing YAML, Hydra overrides, dataset paths, conversation roles, parallelism, or voice-agent config.
4. Read `references/checkpoints-and-export.md` before loading, resuming, converting, exporting, or serving checkpoints.
5. Read `references/troubleshooting.md` when imports, CUDA, compiled backends, data schemas, Hydra overrides, vLLM, or voice-agent services fail.
6. Run `scripts/check_speechlm2_config.py --help` and then use it on user-provided SpeechLM2 YAML/JSON configs before long-running jobs.

## Core Facts

- SpeechLM2 is active development code for augmenting pretrained LLMs with speech understanding and speech generation; expect APIs/configs to change more often than classic ASR/TTS.
- `SALM` uses HuggingFace Transformers for the LLM backbone; `SALMAutomodel` uses NeMo Automodel and is the right path for FSDP2, TP, PP, CP, EP/MoE, HSDP, native Automodel LoRA, and distributed inference.
- Distributed SALM generation/evaluation requires `SALMAutomodel`; plain `SALM` should stay single-process/single-device for inference.
- `NemotronVoiceChat` is inference-only. Train or fine-tune its STT and EAR-TTS components separately, then export a joint VoiceChat checkpoint.
- SpeechLM2 model checkpoints are HuggingFace-style directories with `config.json` and `model.safetensors`; `.nemo` is used in this collection mainly as an input format for pretrained ASR/perception components.
- Training and most inference require a compatible GPU/CUDA/PyTorch stack. Optional Automodel compiled backends such as TransformerEngine, DeepEP, grouped GEMM, flash-attn, vLLM, Pipecat, browser/client tooling, and Node/npm must be installed only when that workflow actually needs them.

## Bundled Assets

- `references/workflows.md`: SALM/SALMAutomodel generation and training, duplex STT/S2S/EAR-TTS, Nemotron VoiceChat, vLLM, and voice-agent workflows.
- `references/configuration.md`: SpeechLM2 YAML structure, data schemas, Hydra overrides, parallelism, and voice-agent configuration patterns.
- `references/checkpoints-and-export.md`: checkpoint formats, `from_pretrained`, `save_pretrained`, HF export, vLLM readiness, and Nemotron VoiceChat conversion.
- `references/troubleshooting.md`: actionable failure diagnosis for install/import, CUDA/backends, data/config, API/CLI, export, vLLM, and voice-agent issues.
- `scripts/check_speechlm2_config.py`: deterministic local checker for SpeechLM2 YAML/JSON-like configs; it performs text-level validation without importing NeMo or downloading models.
