# Runtime overview

## When to read

Read this before installing dependencies, checking imports, choosing CPU/CUDA behavior, or deciding which StyleTTS2 files matter for a task.

## Repository layout

| Area | Operational role |
| --- | --- |
| `train_first.py` | First-stage training launcher; uses Accelerate and saves `epoch_1st_*.pth` plus final `first_stage_path`. |
| `train_second.py` | Second-stage joint/diffusion/adversarial launcher; uses DataParallel rather than DDP. |
| `train_finetune.py` | Fine-tunes from a pretrained multispeaker/LibriTTS-style checkpoint. |
| `train_finetune_accelerate.py` | One-GPU/mixed-precision fine-tuning variant. |
| `Configs/` | Public YAML profiles for LJSpeech, LibriTTS, and fine-tuning. |
| `Data/` | Example train/validation/OOD text list formats. |
| `models.py` | Helper loaders, `build_model`, checkpoint loading, and core model assembly. |
| `meldataset.py` | Training-list parsing, reference sample selection, mel preprocessing, collater, dataloader construction. |
| `Modules/` | Diffusion sampler, discriminators, vocoders, and SLM-adversarial loss. |
| `Utils/ASR`, `Utils/JDC`, `Utils/PLBERT` | Helper model code/configs and bundled pretrained alignment/F0/PL-BERT assets. |
| `Demo/` and `Colab/` | Notebook evidence for pretrained inference and fine-tuning recipes; distilled in the inference/training sub-skills. |

## Source-checkout execution

The repository has no `pyproject.toml`, `setup.py`, or `setup.cfg`. Treat it as source-checkout code:

- Run commands from the checkout root or use helpers that accept `--repo-root`.
- Do not rely on distribution metadata or console entry points.
- For custom Python snippets, add the checkout root to `sys.path` before importing `models`, `meldataset`, or `Modules.*`.
- Use this skill's bundled helper scripts rather than requiring future agents to open original notebooks or copy source launchers.

## Dependency set

Documented requirements include Torch/Torchaudio, SoundFile, Munch, Pydub, PyYAML, Librosa, NLTK, Matplotlib, Accelerate, Transformers, Einops, tqdm, typing-extensions, and `monotonic_align` from GitHub.

Source inspection also found required runtime imports that are not listed in the requirements file:

- `pandas` for `meldataset.py`.
- `tensorboard` for `torch.utils.tensorboard.SummaryWriter` in training launchers.
- `phonemizer` for inference demos.
- A host `espeak-ng` or `espeak` binary for the phonemizer backend used by notebooks.

## Backend expectations

- Training and fine-tuning are CUDA workflows. The source launchers move tensors to CUDA and there is no truthful CPU substitute for native training behavior.
- Pretrained inference can select CPU or CUDA with `torch.cuda.is_available()`. CPU is slower but can avoid the older-GPU high-pitched-noise issue noted by the README.
- WavLM is loaded through Transformers during training; a real run may need network or a pre-populated model cache.
- Full native training and notebook execution are expensive or network/model-download dependent. Use helper dry-runs and asset checks before starting them.

## Verified source facts

The generated skill was built after checking these live facts in an isolated inspection environment:

- Python 3.11 with CUDA-enabled PyTorch/Torchaudio successfully imported the StyleTTS2 source modules.
- `train_first.py`, `train_second.py`, `train_finetune.py`, and `train_finetune_accelerate.py` expose Click `--config_path` and `--help`.
- `load_ASR_models`, `load_F0_models`, `load_plbert`, and `build_model` loaded/build the default helper model graph from bundled assets.
- CUDA tensor allocation passed on NVIDIA A100 hardware during preparation.

Important inspected signatures:

```text
models.load_F0_models(path)
models.load_ASR_models(ASR_MODEL_PATH, ASR_MODEL_CONFIG)
models.build_model(args, text_aligner, pitch_extractor, bert)
models.load_checkpoint(model, optimizer, path, load_only_params=True, ignore_modules=[])
meldataset.FilePathDataset(data_list, root_path, sr=24000, data_augmentation=False, validation=False, OOD_data='Data/OOD_texts.txt', min_length=50)
meldataset.build_dataloader(path_list, root_path, validation=False, OOD_data='Data/OOD_texts.txt', min_length=50, batch_size=4, num_workers=1, device='cpu', collate_config={}, dataset_config={})
DiffusionSampler(diffusion, *, sampler, sigma_schedule, num_steps=None, clamp=True)
```

## Bundled helper scripts

- [../scripts/check_runtime.py](../scripts/check_runtime.py): cross-cutting import/backend/source-checkout smoke check.
- [../sub-skills/data-and-config/scripts/validate_data_lists.py](../sub-skills/data-and-config/scripts/validate_data_lists.py): list/OOD validator.
- [../sub-skills/data-and-config/scripts/inspect_config.py](../sub-skills/data-and-config/scripts/inspect_config.py): config summary and warning helper.
- [../sub-skills/training/scripts/build_training_command.py](../sub-skills/training/scripts/build_training_command.py): dry-run training command/preflight helper.
- [../sub-skills/inference/scripts/check_inference_assets.py](../sub-skills/inference/scripts/check_inference_assets.py): pretrained asset and phonemizer readiness checker.
