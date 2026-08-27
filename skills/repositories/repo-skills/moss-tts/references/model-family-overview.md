# MOSS-TTS model family overview

Read this before choosing a MOSS-TTS workflow or explaining why two examples use different prompt fields, codecs, or output formats.

## Family map

| Public model/workflow | Architecture/code family | Main task | Typical prompt fields | Audio/tokenizer assumptions | Route |
|---|---|---|---|---|---|
| `OpenMOSS-Team/MOSS-TTS-v1.5` | `MossTTSDelay` | high-fidelity long-form TTS, voice cloning, multilingual/pause/duration control | `text`, optional `reference`, `language`, `tokens` | Delay-pattern multi-head RVQ, standard MOSS audio tokenizer | `sub-skills/hf-family-workflows/SKILL.md` |
| `OpenMOSS-Team/MOSS-TTS` | `MossTTSDelay` | original flagship TTS | `text`, optional `reference`, `tokens` | Delay-family codec assumptions | `sub-skills/hf-family-workflows/SKILL.md` |
| `OpenMOSS-Team/MOSS-TTSD-v1.0` | TTSD-compatible `MossTTSDelay` | multi-speaker dialogue speech generation | dialogue `text` with speaker tags, `reference` list with nullable slots, `language` | often `n_vq=16`; code/prompt files must match TTSD checkpoint | `sub-skills/hf-family-workflows/SKILL.md` and fine-tuning route |
| `OpenMOSS-Team/MOSS-VoiceGenerator` | `MossTTSDelay` 1.7B voice-design checkpoint | design a voice from text instructions | `text` + `instruction` | no reference audio required for core voice design | `sub-skills/hf-family-workflows/SKILL.md` |
| MOSS-SoundEffect v1 | Delay-family SoundEffect | sound-effect generation with autoregressive audio tokens | `ambient_sound`, optional `tokens` | Delay-family, not SoundEffect v2 DiT | `sub-skills/hf-family-workflows/SKILL.md` |
| `OpenMOSS-Team/MOSS-TTS-Local-Transformer` | legacy `MossTTSLocal` | local-transformer TTS | `text`, optional `reference`, prompt fields similar to Delay | Local topology, 24 kHz-style workflow | `sub-skills/hf-family-workflows/SKILL.md` |
| `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5` | v1.5 `MossTTSLocal` | 48 kHz stereo batch and streaming TTS | `text`, optional `reference`, `language`, `tokens` | MOSS-Audio-Tokenizer-v2, 12 RVQ layers, 12.5 frames/sec, stereo output | `sub-skills/local-v15-streaming/SKILL.md` |
| `OpenMOSS-Team/MOSS-TTS-Realtime` | `MossTTSRealtime` | low-latency voice-agent streaming and multi-turn context | text deltas, prompt/reference audio tokens, turn/session state | 24 kHz codec stream, batch size 1 in service path | `sub-skills/realtime-voice-agent/SKILL.md` |
| `OpenMOSS-Team/MOSS-SoundEffect-v2.0` | DiT + DAC VAE + Qwen3 text encoder | text-to-audio sound effects up to long durations | `prompt`, `seconds`, `num_inference_steps`, `cfg_scale` | separate package/env, CUDA/Triton acceleration, not Delay-family | `sub-skills/soundeffect-v2/SKILL.md` |

## Language and prompt-control facts

- MOSS-TTS-v1.5 and Local v1.5 support a broad multilingual set; when the language is known, pass a language name such as `Chinese`, `English`, or `French` instead of relying on auto behavior.
- Pinyin and IPA inputs are text forms for the Delay-family processor; preserve them as text and avoid normalizers that remove tone numbers or slashes.
- Explicit pauses use inline markers like `[pause 3.2s]` in the `text` field.
- Duration control uses `tokens`; for Local v1.5, 12.5 frames is about one second, so `tokens=125` is roughly 10 seconds.
- TTSD dialogue uses speaker-tagged text and per-speaker references. Preserve `null` placeholders in reference lists to keep speaker alignment.
- VoiceGenerator needs an `instruction` describing voice style; do not solve it as ordinary voice cloning unless the user explicitly supplies a separate TTS task.
- SoundEffect v1 uses `ambient_sound`; SoundEffect v2 uses a separate diffusion pipeline `prompt`.

## Backend boundaries

- Full HF generation usually needs `torch`, `transformers`, `torchaudio`, `torchcodec`, FFmpeg, model downloads, and enough CPU/GPU memory. CUDA + bf16/fp16 is the practical route for large checkpoints.
- FlashAttention is optional. If unavailable, use SDPA on CUDA or eager on CPU.
- The llama.cpp path is the torch-free route for Delay-family inference, but it still needs GGUF backbone weights, side weights, tokenizer files, and ONNX/TRT/Torch audio-tokenizer artifacts depending on config.
- SoundEffect v2 deliberately has its own dependency stack and should be isolated from the top-level MOSS-TTS environment.

## Model-family mismatch symptoms

Use this table when a user reports gibberish audio, shape errors, or successful loading with bad output.

| Symptom | Likely mismatch | Next route |
|---|---|---|
| Audio code tensor depth mismatch | `n_vq` differs between manifest, processor, and checkpoint | `sub-skills/finetuning-data-prep/references/data-formats.md` |
| TTSD fine-tune loss looks normal but inference is gibberish | Delay-family code files used with TTSD prompt/token assumptions | `sub-skills/hf-family-workflows/references/model-packaging.md` |
| Local v1.5 output treated as mono or wrong sample rate | ignored 48 kHz stereo codec-v2 output | `sub-skills/local-v15-streaming/SKILL.md` |
| SoundEffect v2 install breaks root MOSS-TTS imports | mixed separate dependency stacks | `sub-skills/soundeffect-v2/references/troubleshooting.md` |
| llama.cpp config validates but generation cannot start | missing side-weight/model/codec paths or C bridge | `sub-skills/llama-cpp-backend/references/troubleshooting.md` |
