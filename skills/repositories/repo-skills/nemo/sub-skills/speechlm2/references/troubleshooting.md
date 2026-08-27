# SpeechLM2 Troubleshooting

Use this guide before long-running training, conversion, vLLM serving, or voice-agent debugging. It covers failure modes observed in SpeechLM2 docs, configs, source, examples, and tests.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'nemo.collections.speechlm2'`.
- Import succeeds for `nemo` but fails on `nemo_automodel`, `lhotse`, `transformers`, `safetensors`, `vllm`, `flash_attn`, `transformer_engine`, `pipecat`, or browser/client dependencies.
- A config or script imports classic NeMo but cannot import SpeechLM2 model classes.

Actions:

1. Confirm the user installed a NeMo Speech build that includes SpeechLM2 extras. A generic minimal install may not include `nemo_automodel`, Lhotse, vLLM, or voice-agent extras.
2. Install a compatible PyTorch/CUDA stack first, then install SpeechLM2 dependencies. Current docs say NeMo Speech targets Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training/recommended inference, while package metadata allows Python >=3.10.
3. Install only the optional stack needed by the workflow: SpeechLM2 for SALM/duplex models, Automodel/compiled backends for SALMAutomodel MoE/distributed workflows, vLLM for serving, voice-agent dependencies plus Node/npm for the browser demo.
4. If the task only needs config inspection, use `../scripts/check_speechlm2_config.py`; it avoids importing NeMo and avoids network/model downloads.

## CUDA, GPU, and Distributed Failures

Symptoms:

- `torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))` fails because `LOCAL_RANK` is missing.
- `torch.distributed.init_process_group(backend="nccl")` hangs or errors.
- Distributed SALM inference raises that it requires `SALMAutomodel`.
- GPU memory OOMs during model loading, long audio encoding, or validation scoring.

Actions:

1. Use `torchrun` for scripts that initialize distributed/NCCL or expect `LOCAL_RANK`.
2. Keep plain `SALM` inference non-distributed. If `tp_size`, `ep_size`, `pp_size`, or `cp_size` is greater than one, load `SALMAutomodel` and ensure the checkpoint config has `use_nemo_automodel: true`.
3. Match `trainer.devices`, launcher process count, and strategy sizes. The product of model-parallel dimensions must fit world size.
4. For long SALM audio, set `model.encoder_chunk_size_seconds` to split the speech encoder input.
5. Reduce `batch_size`, `batch_duration`, `batch_tokens`, or `max_tokens`; disable validation scoring ASR if the immediate task is generation smoke testing.
6. Use `activation_checkpointing_llm` and/or `activation_checkpointing_perception` for SALMAutomodel memory pressure, accepting slower training.

## SALMAutomodel Backend and Parallelism Failures

Symptoms:

- NaN gradients shortly after enabling context parallelism.
- Errors mentioning BSHD, CP, THD, `packed_sequences`, or `attn=te`.
- TransformerEngine/DeepEP/grouped GEMM/flash-attn import or kernel errors.
- MoE training is unexpectedly slow or expert utilization is imbalanced.

Actions:

1. If `trainer.strategy.cp_size > 1`, set `model.packed_sequences: true`. BSHD plus CP is unsupported and can produce NaN gradients.
2. If `model.packed_sequences: true`, use `model.automodel_backend.attn: te`; the THD path requires TE varlen attention.
3. For packed TE attention, set launcher environment `NVTE_FUSED_ATTN=0` when using Blackwell `sm_120` or when THD gradients explode; this forces FlashAttention dispatch and requires compatible `flash-attn`.
4. If optional compiled kernels fail, pin safer backends: `automodel_backend.attn: sdpa`, `linear: torch`, `experts: torch_mm`, or `dispatcher: torch` as appropriate, then measure performance.
5. For MoE imbalance, enable `model.moe_metrics.enabled`, inspect top/bottom expert utilization, and consider `aux_loss_coeff` or `train_gate` only after confirming data and routing behavior.
6. Ensure Automodel-native LoRA keys are used for SALMAutomodel (`dim`, `alpha`) instead of HF PEFT keys (`r`, `lora_alpha`).

## Data and Manifest Mistakes

Symptoms:

- Empty labels, empty generations, or loss not decreasing.
- Lhotse reader errors for `cuts_path`, `shar_path`, `manifest_filepath`, tarred audio, or AIStore URLs.
- Role-specific errors or model learns to answer as the wrong speaker.
- Audio placeholder count mismatch errors.

Actions:

1. For SALM, verify each `lhotse_as_conversation` entry has `audio_locator_tag` matching `model.audio_locator_tag` and an appropriate `tags.context`.
2. For duplex STT/S2S/VoiceChat, verify `data.input_roles` and `data.output_roles` exactly match manifest supervision `speaker` labels, including capitalization.
3. Check `data.source_sample_rate` for user/input audio and `data.target_sample_rate` for generated/target speech. Common values are 16000 and 22050 respectively.
4. For S2S/VoiceChat manifests, confirm target/assistant audio exists when the model expects `target_audio`.
5. For fixed batching OOMs, switch to duration/token bucketing and reduce bucket/token limits.
6. If using AIStore GetBatch, set `USE_AIS_GET_BATCH=true` only for compatible tarred multimodal conversation manifests; otherwise leave it unset to use the normal tar reader.
7. In direct `generate()` calls, ensure each audio placeholder token in prompts has one corresponding audio segment; do not pass both prompt-embedded audio paths and `audios` tensors.

## Hydra and CLI Misuse

Symptoms:

- Hydra says a key does not exist.
- New overrides are ignored or config fields stay `???`.
- Script starts but uses default data/checkpoint paths.

Actions:

1. Use `key=value` for existing keys and `++key=value` for new keys.
2. Resolve all `???` placeholders before launching training/evaluation.
3. Quote strings containing shell-special characters, lists, braces, colons, or commas.
4. Prefer full YAML edits over long command lines for multi-field experiments.
5. Do not copy example `--config-path=conf` assumptions unless the user is actually running from a directory where that relative path exists; in user-owned scripts, load configs explicitly or pass the correct config directory.

## Checkpoint Loading and Conversion Failures

Symptoms:

- `Missing config.json` or `Missing model.safetensors` during `from_pretrained`.
- State dict key mismatches between SALM and SALMAutomodel.
- Distributed checkpoint export hangs or writes only partial files.
- vLLM prep warns that a checkpoint is HF-only.

Actions:

1. Confirm whether the source is a HF directory, DCP directory, single `.ckpt`/`.pt`, `.safetensors`, or `.nemo` archive.
2. Use `model.init_from_checkpoint` for weights-only fine-tuning and `exp_manager.resume_from_checkpoint` for full run resume.
3. Do not load SALM checkpoints into SALMAutomodel or vice versa without an explicit adaptation plan; embedding and module names differ.
4. For DCP export, launch with a world size and strategy compatible with the training config and consolidate only on rank 0.
5. If `pretrained_llm` or `audio_locator_tag` is missing from the model config, vLLM prep cannot patch tokenizer/config files.
6. If vLLM prep fails, keep the HF export as NeMo-loadable and fix vLLM-specific fields separately.

## vLLM Serving Failures

Symptoms:

- vLLM cannot load `model_type: nemo_speechlm`.
- Error says `audio_locator_tag` must be `<|audio|>`.
- Placeholder count mismatch for audio requests.
- Hybrid/Mamba/Nemotron backbone KV cache errors.

Actions:

1. Ensure the NeMo SpeechLM vLLM plugin is importable and registered in the serving environment.
2. Confirm `config.json` includes `model_type: "nemo_speechlm"` and `architectures: ["NeMoSpeechLMForConditionalGeneration"]`.
3. Use `audio_locator_tag: "<|audio|>"`; the plugin rejects custom audio tokens by design.
4. Confirm tokenizer files include the audio token and `tokenizer_config.json` uses `extra_special_tokens: {"audio_token": "<|audio|>"}`.
5. Use `--trust-remote-code` when the selected backbone requires custom HF code.
6. For hybrid Nemotron backbones, use vLLM versions that support the needed Mamba/hybrid cache path and set backend-specific flags such as Mamba state dtype only when required.

## Duplex EAR-TTS and Nemotron VoiceChat Failures

Symptoms:

- `NemotronVoiceChat.training_step is not implemented`.
- Generated audio is silent, very noisy, or stops too early.
- Speaker conditioning does not use the expected voice.
- Validation logs have predicted text but missing audio or ASR-transcribed speech.

Actions:

1. Do not train `NemotronVoiceChat` directly. Train `DuplexSTTModel` and `DuplexEARTTS` separately, then export a joint checkpoint.
2. Check speaker-conditioning precedence: explicit `speaker_audio` arguments override `inference_speaker_name`, which overrides `inference_speaker_reference`.
3. Verify `model.speech_generation.model.inference_guidance_enabled`, `inference_guidance_scale`, `inference_noise_scale`, `inference_top_p_or_k`, and `inference_force_speech_silence_on_eos`.
4. Confirm TTS target sample rate and speaker reference sample rate are resampled consistently.
5. For EAR-TTS JSONL, verify each line has `text`, `context_audio_filepath`, and `audio_filepath`; `text` may be a string or a list for multi-turn generation.
6. For VoiceChat evaluation, confirm `model.scoring_asr` is available if metrics require ASR-transcribing generated speech.

## Voice-Agent Failures

Symptoms:

- Browser cannot connect to the server.
- Browser cannot access microphone or `enumerateDevices` is undefined.
- vLLM server fails to start or tool calling does not work.
- The agent answers only tool-related questions or refuses unrelated questions.
- Node/npm client errors such as unsupported syntax or broken `node_modules`.

Actions:

1. Confirm the server host/port matches the browser client's WebSocket `baseUrl` and any `SERVER_PUBLIC_HOST` setting.
2. For non-HTTPS local origins, allow microphone access in the browser settings or secure-origin allowlist.
3. Update Node/npm when the client build reports syntax support issues; remove and reinstall `node_modules` when dependency state is corrupt.
4. Use `llm.type: vllm` for tool calling with supported models; HF fallback may not support tool calling.
5. Tune the system prompt suffix to avoid commitment bias: instruct the LLM to use tools only when needed and to answer non-tool questions normally.
6. Disable diarization or adjust VAD/backchannel settings if turns are missed, speakers are confused, or backchannels interrupt the bot.
7. For manually started vLLM servers, set `start_vllm_on_init: false` and make sure server parameters match the chosen model.

## Quick Preflight Checklist

Before a heavy SpeechLM2 run:

- `../scripts/check_speechlm2_config.py CONFIG.yaml` reports no errors.
- All checkpoint, data, and output paths are user-owned and exist or are intentionally created.
- The config contains no unresolved `???` placeholders.
- The selected model class matches `model.use_nemo_automodel` and requested parallelism.
- CUDA, launcher process count, and strategy sizes agree.
- Optional compiled/vLLM/voice-agent dependencies are installed only when that workflow needs them.
