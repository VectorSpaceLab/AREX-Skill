# Fine-Tuning Workflows

Fine-tuning starts from a pretrained checkpoint and retrains on a new dataset. The safe default is to prepare the dataset/config/command and stop before running.

## Standard released-checkpoint fine-tuning

1. **Choose and inspect the released model.** Use the inference/model-zoo sub-skill for model names, metadata, licenses, and download behavior: [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md).
2. **Obtain checkpoint and config paths.** The installed `tts` command can download a model during inference, but a fine-tuning plan must make the resulting checkpoint/config paths explicit.
3. **Copy the config into the user's experiment area.** Change dataset fields, output path, run name, language, audio settings, and fine-tuning learning rate.
4. **Validate the edited config.** Run `scripts/validate_tts_config.py --config-path config.json --load-samples`.
5. **Use `--restore_path` for the pretrained weights.** Keep `--config_path` pointed at the edited config.

Template:

```bash
CUDA_VISIBLE_DEVICES=0 python -m TTS.bin.train_tts \
  --config_path config.json \
  --restore_path checkpoints/model_file.pth \
  --coqpit.output_path runs/my-finetune \
  --coqpit.run_name my-finetune \
  --coqpit.lr 0.00001
```

## Fields commonly changed for fine-tuning

| Field | Change |
| --- | --- |
| `datasets` | Replace all dataset path/metadata/language values with the target dataset. |
| `run_name` | Give the fine-tune run a distinct name. |
| `output_path` | Put outputs in a new run directory; avoid overwriting the base model cache. |
| `lr` | Usually lower than from-scratch training to avoid destroying pretrained features. |
| `audio` | Verify sample rate, mel settings, and silence trimming against the target dataset and checkpoint assumptions. |
| `characters` / `use_phonemes` / `phoneme_language` | Update only after checking unique symbols/phonemes and checkpoint compatibility. |
| `batch_size`, `eval_batch_size`, `grad_accum_steps` | Tune for available VRAM and desired effective batch. |

## Checkpoint/config compatibility

Fine-tuning can fail when the edited config no longer matches checkpoint dimensions. Be careful with:

- Changing model architecture fields.
- Changing tokenizer vocabulary, phoneme/grapheme mode, BOS/EOS/blank behavior, or character order.
- Changing speaker embedding/d-vector settings without updating speaker files.
- Changing audio mel dimensions that downstream vocoder/inference expects.

When a mismatch appears, either restore the original compatible fields or start from a checkpoint trained with the desired configuration.

## XTTS GPT fine-tuning caveats

XTTS GPT fine-tuning is not the same as ordinary `--restore_path` fine-tuning.

Distilled recipe behavior:

- It prepares a `BaseDatasetConfig` for the target dataset and language.
- It downloads or expects the XTTS vocabulary, XTTS checkpoint, DVAE checkpoint, and mel normalization file.
- It creates `GPTArgs` with paths such as tokenizer file, XTTS checkpoint, DVAE checkpoint, and mel norm file.
- It uses `XttsAudioConfig` with model-specific sample rates.
- It configures `GPTTrainerConfig` with small per-device batch size and large gradient accumulation.
- The effective batch recommendation from the recipe is approximately `batch_size * grad_accum_steps >= 252` for efficient training.
- It passes `TrainerArgs(restore_path=None, grad_accum_steps=...)` because the XTTS checkpoint path is supplied inside model args, not through the standard Trainer `restore_path` flag.

Operational warnings:

- Expect network downloads unless all XTTS files are already provided.
- GPU and substantial VRAM are expected; CPU is not a practical substitute for performance claims.
- Keep language and speaker reference wavs explicit in test sentences.
- Validate the dataset before any XTTS file downloads.
- Reduce batch size first when OOM occurs, then raise `grad_accum_steps` to preserve effective batch if training quality requires it.

## Synthetic fine-tuning planning case

A useful difficult case for verification is: given a released checkpoint/config pair plus a new LJSpeech-style dataset, produce an edited config and command that changes only `datasets`, `output_path`, `run_name`, and `lr`, validates paths, and does not start training. If the user also changes `characters` or audio mel settings, the skill should warn about checkpoint/config mismatch risk.

