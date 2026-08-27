# TTS Training Workflow Patterns

Default behavior for this sub-skill is to validate and build a training plan, not to launch training. Full TTS training is expensive and dataset-specific.

## Standard workflow

1. **Choose a model family.** Start with a well-supported config such as GlowTTS or Tacotron/Tacotron2 for experimentation. If attention alignment is difficult, consider AlignTTS or GlowTTS. For faster forward models, review their alignment/duration prerequisites.
2. **Format the dataset.** Prefer LJSpeech-style metadata for a single-speaker custom dataset. See [data-formats.md](data-formats.md).
3. **Create a Coqpit config.** Set `model`, `output_path`, `run_name`, `datasets`, `audio`, text cleaner, tokenizer/phonemizer, batch size, and eval split fields. See [configuration.md](configuration.md).
4. **Validate without training.** Run `scripts/validate_tts_config.py` and `scripts/find_unique_symbols.py`.
5. **Only then construct a training command.** Use the installed training module with `--config_path`; add restore/continue/distributed flags only when the user explicitly wants a run.
6. **Monitor outputs.** Use the training log and dashboard outputs to watch loss curves, spectrograms, attention maps, and generated test sentences.
7. **Route trained-checkpoint inference elsewhere.** Testing a trained checkpoint through Python API or CLI belongs to [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md) or [../../server-and-cli/SKILL.md](../../server-and-cli/SKILL.md).

## Safe pre-training commands

From this sub-skill directory:

```bash
python scripts/validate_tts_config.py --config-path config.json --load-samples --sample-preview 5
python scripts/find_unique_symbols.py --config-path config.json --mode chars
```

If the dataset is only a few rows, add `--no-eval-split` to the validation command while checking paths.

Optional phoneme inventory:

```bash
python scripts/find_unique_symbols.py --config-path config.json --mode phonemes
```

## Training command template

Use module execution rather than repository file paths:

```bash
CUDA_VISIBLE_DEVICES=0 python -m TTS.bin.train_tts --config_path config.json
```

Important Trainer arguments verified from the installed training parser:

| Flag | Use |
| --- | --- |
| `--config_path` | Start training from a config file. |
| `--continue_path` | Continue a previous experiment directory; loads its `config.json`. |
| `--restore_path` | Initialize model weights from a checkpoint while using the current config. Common for fine-tuning. |
| `--use_ddp` | Use distributed data parallel support when launching with distributed tooling. |
| `--use_accelerate` | Use Accelerate integration when configured. |
| `--grad_accum_steps` | Accumulate gradients to simulate a larger effective batch. Useful under VRAM limits and for XTTS GPT fine-tuning. |
| `--small_run` | Trainer smoke/debug mode; useful only for bounded checks, not quality training. |
| `--gpu` | Trainer GPU selection flag exposed by the parser. Prefer explicit `CUDA_VISIBLE_DEVICES` when constructing reproducible commands. |

Coqpit overrides can be passed after the known Trainer flags, for example:

```bash
CUDA_VISIBLE_DEVICES=0 python -m TTS.bin.train_tts \
  --config_path config.json \
  --restore_path checkpoints/base_model.pth \
  --coqpit.output_path runs/finetune \
  --coqpit.lr 0.00001
```

## Recipe patterns distilled

A recipe-style Python training script usually performs these steps:

1. Create one or more `BaseDatasetConfig` objects.
2. Instantiate a model-specific config such as `GlowTTSConfig` with dataset, tokenizer/phonemizer, audio, batch, logging, and output settings.
3. Create an `AudioProcessor` from the config.
4. Initialize `TTSTokenizer` from the config.
5. Load train/eval samples with `load_tts_samples()`.
6. Instantiate the model from the config, audio processor, tokenizer, and optional speaker manager.
7. Create `Trainer(TrainerArgs(), config, output_path, model=..., train_samples=..., eval_samples=...)`.
8. Call `trainer.fit()`.

Do not copy recipe dataset paths or launch recipe scripts directly. Adapt the pattern to the user's dataset and config.

## Multi-GPU and slow hardware notes

- For single GPU, set `CUDA_VISIBLE_DEVICES=0` and run the training module.
- For multi-GPU, use the Trainer distributed launcher or the parser's DDP/Accelerate flags only after confirming the environment.
- CPU training is usually too slow for real TTS. It can be acceptable for parser/config validation and tiny smoke checks only.
- If VRAM is limited, reduce `batch_size`, `eval_batch_size`, `max_audio_len`, `max_text_len`, loader workers, or precision choices; consider `--grad_accum_steps` to preserve effective batch size.

## Speaker embeddings and d-vectors

For multi-speaker TTS:

- Learned speaker embeddings require consistent `speaker_name` values in formatter output.
- Precomputed d-vectors require an encoder checkpoint/config plus a dataset; use `scripts/compute_speaker_embeddings.py --help` and dry-run first.
- Store generated `speakers.pth` or equivalent maps outside this skill tree.
- When appending to an old speaker file, confirm that `dataset_name` and relative audio paths still produce the same `audio_unique_name` keys.

## Native verification candidates for later integration

After the whole repo skill is integrated, suitable native candidates for this sub-skill include:

- Dataset formatter unit behavior for Common Voice-style rows.
- Tiny unique-character extraction against a fixture config.
- Optional tokenizer/phoneme cases when the phonemizer backend is installed.
- Tiny TTS train tests only when explicitly selected; skip by default because training is expensive.

