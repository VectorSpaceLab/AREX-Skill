---
name: audio-clap
description: "Use and troubleshoot OpenCLIP CLAP and NaFlexClap audio models,
  audio transforms/data loaders, Hugging Face audio zero-shot evaluation, and HF
  CLAP checkpoint conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Audio CLAP

Use this sub-skill when working with OpenCLIP audio-text models: `CLAP-HTSAT-*`, `CLAP-Whisper-*`, and `naflexclap_*`. It covers model/config selection, audio preprocessing contracts, `webdataset-audio`/`synthetic-audio` data flows, Hugging Face audio zero-shot evaluation, and Transformers CLAP checkpoint conversion.

## Route First

- Use this sub-skill for CLAP/NaFlexClap audio tower setup, audio batch dicts, `CLIPAudioCfg`, `AudioAugmentationCfg`, `AUDIO_AVAILABLE`, audio WebDataset loaders, audio zero-shot flags, and HF CLAP state-dict conversion.
- Route dense image/text inference and ordinary CLIP image preprocessing to `../model-inference/SKILL.md`.
- Route generic training launch mechanics, optimizer/checkpoint resume, FSDP, logging, and distributed details to `../training/SKILL.md`.
- Route GenLAP and general NaFlex token-budget/generative mechanics to `../naflex-generative/SKILL.md`.
- Route cross-family evaluation/export summaries outside audio-specific zero-shot or conversion to `../evaluation-conversion/SKILL.md`.

## Quick Start

1. Confirm optional audio support before building audio transforms:

   ```bash
   python sub-skills/audio-clap/scripts/audio_config_report.py --model CLAP-HTSAT-tiny-Roberta-base-fused
   ```

2. For HF audio zero-shot, plan the exact command without downloading data or loading checkpoints:

   ```bash
   python sub-skills/audio-clap/scripts/clap_zero_shot_args.py \
     --model CLAP-HTSAT-tiny-Roberta-base-fused \
     --pretrained laion \
     --audio-zeroshot-dataset ashraq/esc50 \
     --audio-zeroshot-split train \
     --audio-zeroshot-class-key category \
     --audio-zeroshot-target-key target \
     --batch-size 16 --device cuda --precision amp_bf16
   ```

3. Run real HF audio zero-shot only after the plan is acceptable and the environment has checkpoints or pretrained weights plus `datasets[audio]`, `torchaudio`, `torchlibrosa`, and model-specific extras. Prefer the installed training CLI path:

   ```bash
   python -m open_clip_train.main --model CLAP-HTSAT-tiny-Roberta-base-fused --pretrained laion --audio-zeroshot-dataset ashraq/esc50 --audio-zeroshot-split train --batch-size 64 --device cuda --zeroshot-frequency 1
   ```

## Key Contracts

- Optional dependencies are reported by `open_clip.audio.AUDIO_AVAILABLE`; call `open_clip.audio.require_audio()` when you need an explicit failure with missing package names.
- Default `CLIPAudioCfg` fields are `model_type="HTSAT"`, `model_name="tiny"`, `audio_length=1024`, `clip_samples=480000`, `sample_rate=48000`, `mel_bins=64`, `window_size=1024`, `hop_size=480`, `fmin=50`, `fmax=14000`, `class_num=527`, `enable_fusion=False`, and `fusion_type="aff_2d"`.
- Default audio augmentation uses `data_fill="repeatpad"` and `data_trunc="rand_trunc"`; eval forces deterministic truncation unless fusion is enabled.
- Standard CLAP batches use `batch["audio"] = {"waveform": Tensor[B, clip_samples], "longer": BoolTensor[B]}` and optionally `"mel_fusion": Tensor[B, 4, frames, mel_bins]`.
- NaFlexClap batches use `batch["audio"] = {"patches": Tensor[B, N, patch_dim], "patch_coord": LongTensor[B, N, 2], "patch_valid": BoolTensor[B, N]}`; do not feed waveform dicts to `model_type="naflexvit"` towers.
- Audio training/eval data loaders emit dict batches with `"audio"` and `"text"` keys, not image/text tuples.

## References

- `references/audio-api.md` — model families, config fields, transforms, dependency checks, and batch shapes.
- `references/data-and-eval.md` — `webdataset-audio`, `synthetic-audio`, NaFlexClap loaders, and HF audio zero-shot flags.
- `references/checkpoints-conversion.md` — pretrained audio encoder loading and Transformers CLAP conversion APIs.
- `references/troubleshooting.md` — common optional dependency, dataset, transform, worker, and conversion failures.

## Safe Helpers

- `scripts/audio_config_report.py` imports audio/config APIs, reports dependency availability, and prints `CLIPAudioCfg`/model audio config fields without downloading weights.
- `scripts/clap_zero_shot_args.py` validates audio zero-shot arguments and prints a data/model-dependent command plan without loading checkpoints, downloading datasets, or running evaluation.
