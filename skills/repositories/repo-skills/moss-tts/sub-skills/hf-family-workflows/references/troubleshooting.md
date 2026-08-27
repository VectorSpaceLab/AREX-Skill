# Troubleshooting Hugging Face family workflows

Use this matrix for MOSS-TTS Delay/Local Hugging Face remote-code workflows, TTSD, VoiceGenerator, SoundEffect v1, and Gradio-style launchers.

## Import and packaging failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'moss_tts_delay'` after `pip install -e .` | Current package metadata can create distribution metadata without exposing source modules because `[tool.setuptools] py-modules = []` leaves the setuptools mapping empty. | Run from a checkout root, set `PYTHONPATH` to the source root for that process, or install a corrected wheel/editable layout that includes package directories. For HF generation, prefer `AutoProcessor`/`AutoModel` with `trust_remote_code=True`. |
| `pip show moss-tts` succeeds but imports fail | Distribution metadata is present; package exposure is not. | Treat metadata success as insufficient. Verify imports from the same working directory and Python executable that will run generation. |
| `ImportError` for `torch`, `transformers`, `torchaudio`, or `torchcodec` | Only lightweight/base dependencies are installed, not the runtime extra. | Install the torch runtime profile with a PyTorch wheel backend matching the host, e.g. `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime]"`. |
| Audio loading/decoding errors mention FFmpeg, codec, or unsupported media | FFmpeg is missing or not visible to `torchcodec`/`torchaudio`; media format is unsupported. | Install FFmpeg (`apt-get install ffmpeg` or `brew install ffmpeg`), restart the process, and try WAV/FLAC/M4A known to load with torchaudio. |
| `trust_remote_code` warning or failure to find custom classes | Remote code was not trusted or model snapshot lacks code/config files. | Pass `trust_remote_code=True` to both processor and model loads; use a complete model snapshot; pin a revision if cache contents are inconsistent. |

## Attention, dtype, and device failures

| Symptom | Likely cause | Fix |
|---|---|---|
| FlashAttention import/build failure | `flash-attn` is optional and hardware/compiler-specific. | Do not block on it. Use `attn_implementation="sdpa"` on CUDA or `"eager"` on CPU. |
| Crash or bad performance with cuDNN SDPA | The workflow disables cuDNN SDPA and keeps flash/mem-efficient/math kernels. | In runtime scripts, call `torch.backends.cuda.enable_cudnn_sdp(False)` before loading/generation. |
| `flash_attention_2` selected but fails at runtime | GPU capability, dtype, or package version does not support it. | Select FlashAttention only when CUDA is available, dtype is fp16/bf16, `flash_attn` imports, and compute capability is Ampere or newer; otherwise use SDPA. |
| CPU generation is extremely slow or OOMs | 8B models and audio codecs are heavy. | Use CUDA with `bfloat16` when possible. For CPU/edge/low-memory, route torch-free GGUF/ONNX work to `../llama-cpp-backend/SKILL.md`. |
| CUDA OOM during model load or first generation | 8B model + codec + long prompt/reference consumes VRAM; max tokens too high. | Reduce `max_new_tokens`, shorten text/reference, use one request at a time, use `bfloat16`, prefer FlashAttention/SDPA, or use lower-memory backends. |
| `torch_dtype`/`dtype` keyword warnings | Transformers API version difference. | Use the keyword supported by the installed Transformers version; `torch_dtype=dtype` is broadly compatible, while newer versions may prefer `dtype=dtype`. |

## Model download and cache failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `from_pretrained` hangs or fails with network errors | Model/codec snapshot download is required and network/cache is unavailable. | Pre-download model and codec snapshots in a stable environment, set the standard HF cache variables before process start, or use a local model directory. |
| `local_files_only=True` fails | Required model or codec files are not cached. | Disable `local_files_only` for the first download or point to a complete local snapshot. Remember TTSD may need an explicit codec path. |
| Config/tokenizer mismatch after copying cache files manually | Partial copy or mixed revisions. | Re-download or recopy a complete snapshot. Keep model code, tokenizer assets, config, weight shards, and codec revision together. |
| `safetensors` index references missing shard | Incomplete model directory. | Verify all shard filenames in `model.safetensors.index.json` exist and are relative paths. |

## Prompt and reference-audio failures

| Symptom | Likely cause | Fix |
|---|---|---|
| v1.5 multilingual output uses wrong pronunciation/accent | Missing or wrong `language` label. | Set `language` to a supported language label when known, such as `French`, `English`, or `Chinese`. Do not invent tags; omit if uncertain. |
| Bad Pinyin/IPA pronunciation | Pinyin tones or IPA wrapper are malformed. | Use tone-numbered Pinyin (`ni3 hao3`) and wrap IPA in `/.../`. Keep punctuation clear. |
| Explicit pause ignored | Incorrect pause syntax or unsupported model. | Use v1.5-compatible `[pause X.Ys]`, e.g. `[pause 3.2s]`; do not assume 1.0 checkpoints follow it as reliably. |
| Continuation repeats or starts in the wrong place | Prefix transcript was not prepended to `text`, or the assistant prefix audio does not match the transcript. | Build user text as `prefix_transcript + new_text`; put prefix audio in `processor.build_assistant_message(audio_codes_list=[...])`; use `mode="continuation"`. |
| Voice clone similarity is poor | Noisy, too long, too short, wrong-language, or mismatched reference audio. | Use clean speech-dominant reference, trim silence/noise, avoid music/background, and test one reference at a time. v1.5 is more stable than 1.0 for long-reference short-text cloning. |
| `torchaudio.load` or encoding fails on reference | Bad path/URL, unsupported format, empty audio, or missing FFmpeg. | Confirm the path exists, convert to WAV if needed, install FFmpeg, and resample through the processor rather than manually changing code shapes. |
| Duration is too short/long | `tokens` is a soft prompt field; `max_new_tokens` is a hard cap. | Use `1s ≈ 12.5 tokens` for `tokens`; increase `max_new_tokens` above the expected output duration. Do not enable duration control for continuation UI modes. |

## TTSD-specific failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Dialogue must include speaker tags` or wrong speaker output | Missing or malformed `[S1]`, `[S2]`, ... tags. | Use explicit tags throughout the prompt and generated dialogue. Keep tags consistent with the speaker count. |
| Error because a speaker has audio but no prompt text | TTSD continuation requires both reference audio and prompt transcript for each cloned speaker. | Provide both for every cloned speaker or provide neither. Prompt text may be auto-prefixed with `[Sx]` by a wrapper, but the API text should be explicit. |
| Speaker voices swapped | Reference list/order does not match prompt text/order; concatenated prompt audio order differs. | Encode references in speaker order; concatenate prompt waveforms in the same order; align `reference=[S1_codes, S2_codes, ...]` with `[S1]`/`[S2]`. |
| `audio_codes` / `n_vq` mismatch | TTSD-v1.0 uses a 16-codebook checkpoint while MOSS-TTS Delay commonly uses 32. | Re-encode prompt audio with the TTSD processor/codec; do not reuse TTS 32-codebook codes. Verify `processor.model_config.n_vq`. |
| Gibberish after replacing code for a TTSD fine-tuned checkpoint | Mixed model code, config, tokenizer, or codec from a different Delay-family checkpoint. | Revert to the checkpoint's matching remote code, then only replace code according to a complete compatibility recipe. Verify `n_vq`, token IDs, architecture, and codec. |

## VoiceGenerator-specific failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Please enter a voice instruction` or bland voice | `instruction` is missing or too vague. | Provide concrete timbre/style/emotion/accent/speed guidance. |
| User tries to clone reference audio with VoiceGenerator | VoiceGenerator is instruction-based voice design, not reference-based cloning. | Use MOSS-TTS-v1.5 for reference cloning. Use VoiceGenerator when there is no reference audio. |
| Output ignores instruction | Contradictory or overly long instruction; sampling too random. | Shorten the instruction, remove contradictions, use recommended sampling (`temperature=1.5`, `top_p=0.6`, `top_k=50`, repetition penalty `1.1`). |

## SoundEffect v1 vs v2 confusion

| Symptom | Likely cause | Fix |
|---|---|---|
| User asks for `seconds`, DiT, Flow Matching, DAC VAE, or SoundEffect-v2.0 | This is the separate v2 pipeline, not Delay-family SoundEffect v1. | Route to `../soundeffect-v2/SKILL.md`. |
| SoundEffect v1 prompt passed as `text` | Delay SoundEffect v1 examples use `ambient_sound`. | Build with `processor.build_user_message(ambient_sound="...", tokens=...)`. |

## Gradio-style launcher failures

| Symptom | Likely cause | Fix |
|---|---|---|
| App takes a long time before first page is usable | Launchers preload model/processor at startup. | Expect cold-start latency; verify model downloads/cache and VRAM before assuming the UI is stuck. |
| App silently uses CPU despite `--device cuda:0` | CUDA is unavailable to the process or PyTorch wheel is CPU-only. | Check `torch.cuda.is_available()`, installed PyTorch backend, and visible devices. |
| `--attn_implementation auto` still uses SDPA/eager | FlashAttention package/device/dtype conditions were not met. | This is expected fallback, not a failure. Install FlashAttention only if needed and supported. |
| Public sharing fails | Gradio share/network restrictions. | Use `--host 127.0.0.1` for local-only, `--host 0.0.0.0` for LAN/container exposure, and `--share` only when allowed by policy/network. |

## Mixed code/checkpoint gibberish checklist

When audio is syntactically generated but sounds like noise, wrong language, or random fragments:

1. Confirm the model ID/directory is the one intended.
2. Print `type(processor).__name__`, `type(model).__name__`, `processor.model_config.n_vq`, and `processor.model_config.sampling_rate`.
3. Confirm the architecture is Delay vs Local vs Local v1.5 vs TTSD.
4. Confirm codec path/revision and whether the model is fused or unfused.
5. Confirm tokenizer assets and special audio tokens came from the same snapshot as config/model code.
6. Re-encode reference/prompt audio with the same processor that will generate.
7. Run a short direct generation with no reference, then add reference, then add continuation, isolating the failure step.
8. If a custom/fine-tuned checkpoint is involved, route data/training questions to `../finetuning-data-prep/SKILL.md` and packaging compatibility back to `references/model-packaging.md`.
