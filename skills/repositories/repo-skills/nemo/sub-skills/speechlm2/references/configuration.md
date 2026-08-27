# SpeechLM2 Configuration

SpeechLM2 configs are Hydra/OmegaConf YAMLs with top-level `model`, `trainer`, `data`, and `exp_manager` sections. Evidence comes from SpeechLM2 docs, example configs, source model constructors, and tests.

## Safe Editing Process

1. Classify the model family: SALM, SALMAutomodel, duplex STT, duplex S2S, Duplex EAR-TTS, Nemotron VoiceChat, or voice-agent.
2. Copy the user's config into a user-owned working file before large edits.
3. Run `../scripts/check_speechlm2_config.py CONFIG.yaml` to catch obvious missing fields and risky combinations before launching GPU jobs.
4. Use Hydra overrides for short experiments; prefer committed YAML edits for durable training/evaluation recipes.
5. Keep dataset/checkpoint/cache paths user-owned and relative to the user's environment; do not bake private machine paths into reusable configs.

## SALM Config Essentials

A minimal SALM config needs:

```yaml
model:
  pretrained_llm: Qwen/Qwen3-1.7B
  pretrained_asr: nvidia/canary-1b-flash
  pretrained_weights: true
  prompt_format: qwen
  audio_locator_tag: "<|audioplaceholder|>"
  encoder_chunk_size_seconds: null
  perception:
    target: nemo.collections.speechlm2.modules.perception.AudioPerceptionModule
    output_dim: 2048
    modality_adapter:
      _target_: nemo.collections.speechlm2.modules.perception.IdentityConnector
      d_model: 1024
trainer:
  accelerator: gpu
  precision: bf16-true
data:
  train_ds:
    input_cfg:
      - type: lhotse_as_conversation
        cuts_path: TRAIN_CUTS.jsonl.gz
        audio_locator_tag: ${model.audio_locator_tag}
        tags:
          context: "Transcribe the following audio:"
```

Common knobs:

- `model.pretrained_llm`: HF model id or local HF directory for the LLM backbone.
- `model.pretrained_asr`: NeMo ASR checkpoint/model name or local checkpoint used by the perception module.
- `model.pretrained_weights`: `true` to initialize from pretrained LLM/ASR; `false` for architecture-only/random init.
- `model.init_from_checkpoint`: fine-tune from model weights only; accepts distributed checkpoint directories, HF directories with `model.safetensors`, and single-file `.ckpt`/`.pt` checkpoints.
- `model.audio_locator_tag`: placeholder token that is inserted in prompts and replaced by audio embeddings.
- `model.freeze_params` and `model.prevent_freeze_params`: regexes controlling trainable modules.
- `model.lora`: HuggingFace PEFT LoRA for classic `SALM` with keys such as `task_type`, `r`, `lora_alpha`, and `lora_dropout`.
- `model.encoder_chunk_size_seconds`: split long audio before the speech encoder; leave `null` unless long-audio memory requires chunking.

## SALMAutomodel Config Essentials

Use SALMAutomodel for NeMo Automodel backends, MoE, and advanced distributed training/inference.

```yaml
model:
  use_nemo_automodel: true
  pretrained_llm: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
  pretrained_asr: nvidia/canary-1b-v2
  pretrained_weights: true
  prompt_format: nemotron-nano-v3
  audio_locator_tag: "<|audio|>"
  encoder_chunk_size_seconds: 30.0
  aux_loss_coeff: 0.0
  train_gate: false
  moe_metrics:
    enabled: true
    mode: brief
    top_k_experts: 5
trainer:
  devices: 8
  accelerator: gpu
  precision: bf16-flash
  strategy:
    _target_: nemo.collections.speechlm2.parts.parallel.AutomodelParallelStrategy
    dp_size: null
    dp_replicate_size: 1
    tp_size: 1
    pp_size: 1
    cp_size: 1
    ep_size: 8
    activation_checkpointing_llm: false
    activation_checkpointing_perception: false
```

SALMAutomodel differences from SALM:

- `model.use_nemo_automodel: true` selects `SALMAutomodel` in training/generation recipes.
- LoRA uses Automodel-native keys: `dim`, `alpha`, `dropout`, `target_modules`, optional `match_all_linear`, `exclude_modules`, `use_dora`, `dropout_position`, and initialization/backend flags.
- Embeddings stay inside the LLM; do not use classic SALM's separate `embed_tokens` assumptions for freeze patterns.
- `trainer.strategy._target_` should be `nemo.collections.speechlm2.parts.parallel.AutomodelParallelStrategy` for Automodel distributed workflows.
- `ep_size` controls expert parallelism for MoE layers on the FSDP data-parallel axis; it is not an extra independent world-size dimension.
- `automodel_backend` can pin attention/linear/norm/MoE kernels and dispatchers; defaults auto-select optional compiled backends when installed.

Optional backend block:

```yaml
model:
  automodel_backend:
    attn: te          # "te" | "sdpa" | "flex"
    linear: te        # "torch" | "te"
    rms_norm: torch_fp32
    rope_fusion: true
    experts: torch_mm # "torch" | "te" | "gmm" | "torch_mm"
    dispatcher: deepep
  sdpa_method: null
```

Document optional compiled prerequisites generically: TransformerEngine/TE, flash-attn, DeepEP, grouped GEMM, UCCL-EP, and NeMo Automodel must match the user's GPU architecture, CUDA, PyTorch, and installed package set.

## Parallelism and Packed Sequences

Rules from the SpeechLM2 parallelism implementation and tests:

- `cp_size > 1` with `model.packed_sequences: false` is invalid for SALMAutomodel training; use `model.packed_sequences: true`.
- `model.packed_sequences: true` requires `model.automodel_backend.attn: te` because the THD path depends on TE varlen attention.
- With packed sequences and TE attention, set launcher environment `NVTE_FUSED_ATTN=0` on Blackwell `sm_120` and consider it as a safe workaround elsewhere when THD gradients become unstable; this forces FlashAttention dispatch and requires compatible `flash-attn`.
- Context parallelism rounds each utterance length to a multiple of `2 * cp_size`; batch/token limits should leave headroom for this padding.
- Inference/generation uses BSHD, not the training packed-sequence path.

## Duplex STT/S2S Data Config

Duplex datasets use Lhotse CutSets with timed supervisions and speaker roles. Typical top-level data fields:

```yaml
data:
  frame_length: 0.08
  source_sample_rate: 16000
  target_sample_rate: 22050
  input_roles: ["user", "User"]
  output_roles: ["agent", "Assistant"]
  train_ds:
    sample_rate: ${data.source_sample_rate}
    input_cfg:
      - type: lhotse_shar
        shar_path: TRAIN_SHAR_DIR
    seed: 42
    shard_seed: randomized
    batch_size: 4
  validation_ds:
    datasets:
      val_set_0:
        shar_path: VAL_SHAR_DIR
    sample_rate: ${data.source_sample_rate}
    batch_size: 1
```

For S2S speech generation, `target_sample_rate` is typically 22050 Hz and target audio may be stored under a Lhotse custom `target_audio` recording. For STT-only duplex tasks, generated output is text, but the conversation roles and turn timing still matter.

Role mapping rules:

- `input_roles` identify user/input turns consumed by the model.
- `output_roles` identify assistant/agent turns the model predicts.
- Match capitalization and labels in the actual manifests. Common pairs are `user`/`agent` and `User`/`Assistant`.
- If output text is missing or roles are swapped, training silently targets the wrong turns or produces empty labels.

## SALM Data Config

SALM uses `SALMDataset` and may read regular ASR/Lhotse data through `lhotse_as_conversation`.

```yaml
data:
  train_ds:
    prompt_format: ${model.prompt_format}
    token_equivalent_duration: 0.08
    input_cfg:
      - type: lhotse_as_conversation
        cuts_path: TRAIN.jsonl.gz
        audio_locator_tag: ${model.audio_locator_tag}
        tags:
          context: "Transcribe the following audio:"
          # system_prompt: "You are a careful speech transcription assistant."
```

`lhotse_as_conversation` creates a user turn containing context text plus audio and an assistant turn containing the supervision text. `token_equivalent_duration` controls how audio duration contributes to token budgets for sampling and bucketing.

Supported input styles include:

- `cuts_path` for Lhotse JSONL/JSONL.GZ.
- `manifest_filepath` plus `tarred_audio_filepaths` for tarred NeMo manifests.
- `shar_path` for Lhotse SHAR.
- nested `input_cfg` pointing at another YAML dataset composition.
- AIStore GetBatch for tarred multimodal conversation manifests when `USE_AIS_GET_BATCH=true` is set in the environment.

## Bucketing and Batching

SpeechLM2 uses Lhotse dynamic batching. For variable-length speech, prefer duration/token batching over fixed `batch_size` once the recipe is stable.

Common fields:

```yaml
data:
  train_ds:
    batch_size: null
    batch_duration: 100
    use_bucketing: true
    num_buckets: 5
    bucket_buffer_size: 5000
    bucket_duration_bins: [8.0, 12.0, 20.0, 40.0]
```

For SALM multimodal sampling, `batch_tokens`, `max_tokens`, `bucket_duration_bins`, and `measure_total_length` represent combined text tokens plus audio-frame-equivalent tokens.

## Experiment Manager

`exp_manager` handles logs and checkpoint callbacks. Distinguish:

- `exp_manager.resume_from_checkpoint`: resume the full training state, including optimizer, scheduler, and step counter.
- `model.init_from_checkpoint`: initialize model weights only and start a fresh optimizer/scheduler.

For reproducibility, save the resolved config at run start. NeMo example recipes save `exp_config.yaml` in the experiment log directory.

## Hydra Override Patterns

Hydra overrides are useful for one-off runs:

```bash
python user_salm_train.py --config-name=salm \
  model.pretrained_llm=Qwen/Qwen3-1.7B \
  data.train_ds.input_cfg.0.cuts_path=TRAIN.jsonl.gz \
  trainer.max_steps=1000
```

Use `++key=value` only when the key does not already exist in the config. Use ordinary `key=value` when overriding existing fields. Missing `++` for a new key and unnecessary `++` for an existing key are common sources of confusing Hydra errors.

## Nemotron VoiceChat Config

`NemotronVoiceChat` evaluation combines STT and speech generation configs:

```yaml
checkpoint_path: VOICECHAT_HF_DIR
model:
  scoring_asr: stt_en_fastconformer_transducer_large
  inference_speaker_reference: null
  inference_speaker_name: Megan
  stt:
    model:
      eval_text_turn_taking: true
  speech_generation:
    model:
      inference_guidance_scale: 0.2
      inference_noise_scale: 0.001
      inference_top_p_or_k: 0.95
      inference_guidance_enabled: true
      inference_force_speech_silence_on_eos: true
data:
  frame_length: 0.08
  source_sample_rate: 16000
  target_sample_rate: 22050
  input_roles: ["user", "User"]
  output_roles: ["agent", "Assistant", "assistant", "Agent"]
  validation_ds:
    datasets:
      evaluation_set:
        shar_path: VAL_SHAR_DIR
    batch_size: 4
```

Do not train `NemotronVoiceChat` directly. Train `DuplexSTTModel` and `DuplexEARTTS` separately; then export the joint model as described in `checkpoints-and-export.md`.

## Voice-Agent Config

The local voice-agent stack is broader than SpeechLM2 model configs. Its server YAML controls component models, hardware placement, WebSocket behavior, vLLM/HF selection, prompts, turn-taking, and tool calling.

Important fields:

- `llm.type`: `auto`, `hf`, or `vllm`.
- `llm.model`: HF model id or local model directory.
- `llm.system_prompt` or prompt file content; keep spoken responses concise and punctuation-friendly for TTS.
- `llm.vllm_server_params`: vLLM command-line parameter string; include tensor parallelism, model length, trust remote code, tool parsers, and reasoning parser flags when needed.
- `llm.start_vllm_on_init`: whether the server should spawn vLLM or expect a manually started vLLM server.
- `tts.think_tokens`: token pair to filter reasoning text from speech when thinking mode is enabled.
- `turn_taking.backchannel_phrases`: list/file/null; `null` disables backchannel ignore behavior.
- `diar.enabled`: disable when diarization is noisy or misassigning speakers.

Voice-agent browser/client setup also requires Node/npm, microphone permissions, a reachable WebSocket URL, and browser permission workarounds for non-HTTPS origins.
