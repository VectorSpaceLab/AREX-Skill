# Training workflows

This reference distills the repository's public training commands and the launch behavior confirmed from the training entry points. Use `scripts/build_training_command.py` for command construction and preflight checks; the original `train_*.py` launchers remain in the user's checkout and should be invoked through the helper.

## Stage selection table

| User goal | Helper stage | Default config | Emitted training command | Required before `--run` | Main outputs |
| --- | --- | --- | --- | --- | --- |
| Pretrain acoustic/style components from prepared data | `first` | `Configs/config.yml` | `accelerate launch train_first.py --config_path Configs/config.yml` | CUDA environment; valid train/val/OOD lists; 24 kHz audio root; ASR, F0/JDC, and PL-BERT assets; WavLM availability/cache | `log_dir/train.log`, `log_dir/tensorboard/`, periodic `epoch_1st_*.pth`, final `log_dir/<first_stage_path>` |
| Continue into StyleTTS2 diffusion/adversarial second stage | `second` | `Configs/config.yml` | `python train_second.py --config_path Configs/config.yml` | CUDA; first-stage checkpoint at `log_dir/<first_stage_path>` unless using a full pretrained second-stage checkpoint | `log_dir/train.log`, `log_dir/tensorboard/`, periodic `epoch_2nd_*.pth` |
| Fine-tune a multispeaker/pretrained model on a new speaker or smaller dataset | `finetune` | `Configs/config_ft.yml` | `python train_finetune.py --config_path Configs/config_ft.yml` | CUDA; new speaker train/val lists and OOD texts; pretrained LibriTTS-style second-stage checkpoint named by `pretrained_model` | Fine-tuned `epoch_2nd_*.pth`, logs, copied config under `log_dir` |
| Fine-tune on one GPU with reduced VRAM pressure | `finetune-accelerate` | `Configs/config_ft.yml` | `accelerate launch --mixed_precision fp16 --num_processes 1 train_finetune_accelerate.py --config_path Configs/config_ft.yml` | One CUDA GPU; same data/assets/checkpoint as `finetune`; enough cache/storage for WavLM and logs | Same fine-tuning checkpoint/log pattern as `finetune` |

## First-stage workflow

Use first stage when the user is training from scratch or preparing the prerequisite checkpoint for second-stage training.

Dry-run from the skill directory:

```bash
python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage first --config Configs/config.yml
```

Run only after preflight passes and the user explicitly approves a long training job:

```bash
python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage first --config Configs/config.yml --run
```

Important behavior:

- The launcher uses Accelerate and creates TensorBoard logs only on the main process.
- The config's `log_dir` is created if absent; the config file is copied there and `train.log` is written there.
- Periodic checkpoints are named `epoch_1st_%05d.pth`; after training, a final checkpoint is saved at `log_dir/<first_stage_path>` where the default config key is `first_stage.pth`.
- The stage loads ASR/text-aligner, F0/JDC, and PL-BERT assets from config fields, builds all model modules, and constructs a `WavLMLoss` from the configured SLM model.
- Do not add mixed precision to the first-stage command unless the user accepts the NaN risk; the repository troubleshooting notes specifically warn against mixed precision for first stage.

## Second-stage workflow

Use second stage after first stage finishes, or when the user has a compatible full second-stage pretrained checkpoint.

```bash
python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage second --config Configs/config.yml
```

Important behavior:

- Use the plain Python command. The repository documents the DDP/Accelerate version as not working for `train_second.py`; the current source wraps most modules in DataParallel instead.
- If `pretrained_model` is empty or `second_stage_load_pretrained` is false, the launcher expects the first-stage checkpoint at `log_dir/<first_stage_path>` and raises an error if `first_stage_path` is empty.
- If `pretrained_model` is set and `second_stage_load_pretrained: true`, the launcher loads that checkpoint directly and bypasses `first_stage_path`.
- The stage starts diffusion/adversarial components according to `loss_params.diff_epoch` and `loss_params.joint_epoch`. The SLM adversarial path uses WavLM and can materially increase VRAM use after `joint_epoch`.
- Periodic checkpoints are named `epoch_2nd_%05d.pth`. There is no separate final alias in the source second-stage launcher, so keep the latest/best periodic checkpoint intentionally.

## Fine-tuning workflow

Use fine-tuning when the user wants to adapt a pretrained multispeaker model, commonly a LibriTTS second-stage checkpoint, to new speaker data.

```bash
python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage finetune --config Configs/config_ft.yml
```

Important behavior:

- The default fine-tune config is built around `epochs`, not `epochs_1st`/`epochs_2nd`.
- It defaults to `second_stage_load_pretrained: true` and `load_only_params: true`, so it loads model weights from `pretrained_model` while resetting optimizer/epoch counters.
- It still needs data preparation: train/val lists, OOD text, 24 kHz audio, speaker ids, and config edits belong to the [data-and-config sub-skill](../../data-and-config/SKILL.md).
- The public fine-tune recipe is a smaller LJSpeech-style run from a LibriTTS checkpoint; do not treat it as a from-scratch substitute unless the user intentionally changes checkpoint fields and model configuration.

## One-GPU accelerate fine-tuning

Use this variant when the user has one CUDA GPU or wants the documented memory-saving path:

```bash
python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage finetune-accelerate --config Configs/config_ft.yml
```

Defaults emitted by the helper match the public recipe:

- `--mixed_precision fp16`
- `--num_processes 1`
- `train_finetune_accelerate.py`

You may override process count or mixed precision with the helper flags, but keep one process for the documented one-GPU path. If quality or stability degrades, compare against the non-accelerate fine-tuning route before changing data/config assumptions.

## Preflight checklist before any real run

- Activate an environment with CUDA-enabled PyTorch, `accelerate`, `transformers`, `torchaudio`, and the repository requirements plus missing runtime imports (`pandas` and `tensorboard`).
- Use a source checkout as `--repo-root`; the repository has no packaging metadata and should not be treated as `pip install -e .` installable.
- Prepare data/config with the [data-and-config sub-skill](../../data-and-config/SKILL.md): 24 kHz audio, `filename.wav|transcription|speaker` lists, OOD text, `data_params.root_path`, `max_len`, `batch_size`, and `slmadv_params.batch_percentage`.
- Ensure ASR, F0/JDC, and PL-BERT paths in the config exist.
- Ensure WavLM can be loaded by Transformers: either allow the first real run to download/cache the configured model, or pre-populate the model cache for offline training.
- Confirm checkpoint intent with [checkpoints-and-resume.md](checkpoints-and-resume.md) before setting `first_stage_path`, `pretrained_model`, `second_stage_load_pretrained`, or `load_only_params`.
