---
name: training
description: "Routes HiFi-GAN training, fine-tuning, dataset layout,
  checkpointing, validation, and distributed GPU training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training

Use this sub-skill when the user needs to train or fine-tune HiFi-GAN with the skill's self-contained bundled `train_hifigan.py` entrypoint, choose a V1/V2/V3 config, prepare LJSpeech-style filelists, manage checkpoints/logs, or debug CUDA/distributed training failures.

## Use this route for

- Launching bundled `scripts/train_hifigan.py` for full training with `v1`, `v2`, `v3`, or a custom JSON config.
- Preparing `LJSpeech-1.1/wavs`, `LJSpeech-1.1/training.txt`, and `LJSpeech-1.1/validation.txt` style inputs.
- Fine-tuning with teacher-forced mel `.npy` files in `ft_dataset` or a custom `--input_mels_dir`.
- Understanding checkpoint save/resume behavior under `--checkpoint_path`.
- Debugging validation/TensorBoard output and multi-GPU `torch.multiprocessing`/NCCL training.
- Running or adapting the bundled tiny-fixture smoke helpers before attempting an expensive run.
- Training without depending on an external HiFi-GAN checkout; the root skill bundles the needed source/config files under `../../scripts/hifigan_runtime/`.

## Do not use this route for

- Checkpoint-based waveform generation from wav inputs. Use the sibling `inference` sub-skill.
- Mel-to-wav or end-to-end synthesis from `.npy` mel files. Use the sibling `inference` sub-skill.
- Editing the HiFi-GAN model architecture beyond config-level training choices; use the root shared model/config references under `../../references/` when available.

## Read first

- `references/training-workflows.md` — training/fine-tuning commands, checkpoint/log behavior, validation, and distributed notes.
- `references/config-and-data.md` — V1/V2/V3 config differences, LJSpeech filelist schema, mel `.npy` layout, and environment facts.
- `references/troubleshooting.md` — concrete recovery guidance for missing wavs, sample-rate mismatches, fine-tuning mel errors, CUDA, TensorBoard, checkpoint collisions, and DDP mistakes.
- Root shared references under `../../references/` — model/config internals and provenance shared with other HiFi-GAN sub-skills.

## Skill-owned scripts

- `scripts/train_hifigan.py` — self-contained training/fine-tuning entrypoint that runs bundled HiFi-GAN source and resolves `--config v1|v2|v3` to bundled configs.
- `scripts/make_ljspeech_fixture.py` — creates a tiny LJSpeech-style wav/filelist fixture, optionally with mel `.npy` files or intentionally bad rows for negative tests.
- `scripts/smoke_train_tiny.py` — creates a temporary fixture and tiny config, then runs a short GPU training pass through `scripts/train_hifigan.py` with safe compatibility shims for modern PyTorch/librosa stacks.

## Fast command patterns

From this sub-skill's `scripts/` directory or by using the script path from anywhere with a CUDA-capable PyTorch environment:

```bash
python scripts/train_hifigan.py --config v1
python scripts/train_hifigan.py --config v2 --checkpoint_path cp_hifigan_v2
python scripts/train_hifigan.py --config v3 --checkpoint_path cp_hifigan_v3
```

For fine-tuning, provide basename-matched mel files and pass the flag exactly as a truthy value:

```bash
python scripts/train_hifigan.py --fine_tuning True --config v1 --input_mels_dir ft_dataset
```

For a cheap local sanity check before a real run:

```bash
python scripts/smoke_train_tiny.py --dry-run
python scripts/smoke_train_tiny.py
```

## Verified environment baseline

The inspection run verified that `torch 2.3.1+cu121` imports on an NVIDIA A100-SXM4-40GB host, CUDA is available, `torch.cuda.get_device_name(0)` works, `torch.utils.tensorboard` imports, and `librosa.util.normalize` is present in `librosa 0.10.2.post1`. The repository requirements are older; read `references/troubleshooting.md` before assuming modern library compatibility.

## Routing notes

- If the task says "train", "fine-tune", "resume", "checkpoint", "validation loss", "TensorBoard", "LJSpeech filelist", "config_v1/config_v2/config_v3", "train_hifigan.py", "multi-GPU", or "NCCL", stay here.
- If the task asks to synthesize wavs or run `inference.py` / `inference_e2e.py`, route to `inference` instead.
- If a workflow needs shared architecture facts, keep this route active for launch/debugging and use root shared references under `../../references/` only for model/config background.
