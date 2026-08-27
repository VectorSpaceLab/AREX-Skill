# Training launch patterns

Use this reference after the manifest is validated and, when needed, preprocessed into `audio_codes`. The generated skill does **not** bundle full SFT trainers or launchers because they are GPU/model-download training programs; use these option contracts with the matching SFT entry point in the user's active MOSS-TTS training checkout or an equivalent trainer.

## Entry-point selection

| Family / task | SFT entry point to choose in the user's training checkout | Launcher style | Notes |
|---|---|---|---|
| Delay / MOSS-TTS v1.5, TTSD, SoundEffect v1, VoiceGenerator | Delay-family SFT trainer | direct `accelerate launch` or environment-variable launcher | For 8B models prefer FSDP or DeepSpeed ZeRO-3 over naive single-card training. |
| Local Transformer legacy | Local-family SFT trainer | direct `accelerate launch` or env launcher | 1.7B-scale configs use smaller sharding profiles than Delay 8B. |
| Local Transformer v1.5 | Local v1.5 SFT trainer | direct `accelerate launch` or env launcher | Fixed RVQ depth is normally 12; use codec v2 in preprocessing. |
| Realtime | Realtime SFT trainer | direct `accelerate launch` or env launcher | Use conversation-turn JSONL from `references/data-formats.md`. |

If the user asks to run an exact repository launcher, treat that as a task against their active checkout. This skill supplies the checked option set, schema rules, and failure recovery; it intentionally does not copy the full trainer implementation.

## Validate before training

Run the bundled validator from this sub-skill on the prepared manifest or representative shard:

```bash
# From this sub-skill directory, or replace <this sub-skill> with its installed path.
python scripts/validate_training_jsonl.py prepared/train_with_codes.jsonl \
  --task moss-tts \
  --mode prepared
```

For TTSD v1.0 rows, use:

```bash
python scripts/validate_training_jsonl.py prepared/dialog.rank00000-of-00008.jsonl \
  --task ttsd \
  --mode prepared
```

## Single-GPU baseline

Use this only for small checkpoints, debugging, or a tiny dataset. For 8B Delay-family checkpoints it is usually a smoke path, not the production route.

```bash
accelerate launch <sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --train-jsonl prepared/train_with_codes.jsonl \
  --output-dir output/moss_tts_sft \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 1e-5 \
  --warmup-ratio 0.03 \
  --num-epochs 3 \
  --mixed-precision bf16 \
  --channelwise-loss-weight 1,32 \
  --gradient-checkpointing
```

## Delay-family 8B distributed patterns

### Data parallel

```bash
accelerate launch \
  --config_file <accelerate-ddp-config> \
  <sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --train-jsonl 'prepared/train_with_codes.rank*.jsonl' \
  --output-dir output/moss_tts_sft_ddp \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 4 \
  --mixed-precision bf16 \
  --channelwise-loss-weight 1,32 \
  --gradient-checkpointing
```

### FSDP

```bash
accelerate launch \
  --config_file <accelerate-fsdp-config> \
  <sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --train-jsonl 'prepared/train_with_codes.rank*.jsonl' \
  --output-dir output/moss_tts_sft_fsdp \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 4 \
  --mixed-precision bf16 \
  --channelwise-loss-weight 1,32 \
  --gradient-checkpointing
```

### DeepSpeed ZeRO-3

```bash
accelerate launch \
  --config_file <accelerate-zero3-config> \
  <sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --train-jsonl 'prepared/train_with_codes.rank*.jsonl' \
  --output-dir output/moss_tts_sft_zero3 \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 4 \
  --mixed-precision bf16 \
  --channelwise-loss-weight 1,32 \
  --gradient-checkpointing
```

Use ZeRO-3 only after the `finetune-deepspeed` dependency group is installed. FSDP/DDP do not require DeepSpeed.

## Local and Realtime training options

Local legacy and Local v1.5 use the same high-level SFT flags as Delay, but choose the correct model and RVQ depth:

```bash
accelerate launch <local-v15-sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5 \
  --train-jsonl prepared/local_v15.rank*.jsonl \
  --output-dir output/moss_tts_local_v1_5_sft \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 4 \
  --mixed-precision bf16 \
  --gradient-checkpointing
```

Realtime training uses conversation JSONL. Keep generated checkpoints aligned with the realtime streaming/inference code path:

```bash
accelerate launch <realtime-sft-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-Realtime \
  --train-jsonl prepared/realtime_with_codes.jsonl \
  --output-dir output/moss_tts_realtime_sft \
  --per-device-batch-size 1 \
  --gradient-accumulation-steps 4 \
  --mixed-precision bf16 \
  --gradient-checkpointing
```

## Common tunable hyperparameters

- Optimizer: `--learning-rate`, `--weight-decay`, `--adam-beta1`, `--adam-beta2`, `--adam-eps`.
- LR schedule: `--lr-scheduler-type`, `--warmup-steps`, `--warmup-ratio`.
- Stability: `--max-grad-norm`, `--gradient-checkpointing`, `--mixed-precision`.
- RVQ loss: `--channelwise-loss-weight`.

`--channelwise-loss-weight` accepts either:

- `n_vq + 1` values: `text_head,vq0,...,vqN`, or
- two values: `text_weight,total_audio_weight`.

The common default `1,32` means the text head and individual audio heads receive comparable total weight.

## Environment-variable launcher pattern

The repository launchers use environment variables equivalent to these names. If the user uses a wrapper, set them explicitly rather than editing the wrapper body:

| Variable | Purpose |
|---|---|
| `RAW_JSONL` | Raw manifest before codec preprocessing. |
| `PREPARED_JSONL` | Output path for preprocessed codes. |
| `TRAIN_JSONL` | Optional training input; may be a file, directory, glob, or comma-separated list. |
| `OUTPUT_DIR` | Checkpoint and log directory. |
| `ACCELERATE_CONFIG_FILE` | DDP/FSDP/ZeRO config path for the user's training host. |
| `SKIP_PREPARE=1` | Skip preprocessing and train from existing prepared rows. |
| `PREP_EXTRA_ARGS_STR` | Extra preprocessing options, such as `--n-vq 16` for TTSD. |
| `PREP_ACCELERATE_ARGS_STR` | Extra Accelerate options for preprocessing. |
| `TRAIN_EXTRA_ARGS_STR` | Extra SFT options, such as batch/precision/loss weights. |

Example variable set for ZeRO-3-style Delay-family training:

```bash
RAW_JSONL=train_raw.jsonl \
PREPARED_JSONL=prepared/train_with_codes.jsonl \
OUTPUT_DIR=output/moss_tts_sft_zero3 \
ACCELERATE_CONFIG_FILE=<accelerate-zero3-config> \
PREP_ACCELERATE_ARGS_STR='--config_file <accelerate-ddp-config>' \
PREP_EXTRA_ARGS_STR='' \
TRAIN_EXTRA_ARGS_STR='--per-device-batch-size 1 --gradient-accumulation-steps 4 --num-epochs 3 --warmup-ratio 0.03 --mixed-precision bf16 --channelwise-loss-weight 1,32 --gradient-checkpointing' \
<run the user-checkout launcher>
```

## Post-training quick check

After a checkpoint is written, run a tiny generation check with the owning inference route:

- Delay / MOSS-TTS v1.5 / TTSD / VoiceGenerator / SoundEffect v1: read `../hf-family-workflows/SKILL.md`.
- Local v1.5: read `../local-v15-streaming/SKILL.md`.
- Realtime: read `../realtime-voice-agent/SKILL.md`.

The quick check should use a short prompt/reference, `torch_dtype` suited to the device, and the same code/prompt-template family used during training. If a TTSD checkpoint was trained with `n_vq=16`, the inference processor/model code must also be TTSD-compatible.

## Stop conditions

Stop before launching or continuing training when:

- JSONL validation fails on any representative shard.
- TTSD rows have mixed or unexpected audio-code depth.
- The selected checkpoint family does not match the code/prompt templates.
- Required codec/model downloads are blocked.
- GPU memory is insufficient even with gradient checkpointing and sharding.
- DeepSpeed is requested but the `finetune-deepspeed` dependency group is absent.
