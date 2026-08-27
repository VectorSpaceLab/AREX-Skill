# Package and Component Overview

## Purpose

Read this when you need a quick map of ClearerVoice-Studio's public components before choosing a sub-skill.

## Components

| Component | Primary use | Runtime shape | Owning sub-skill |
| --- | --- | --- | --- |
| ClearVoice | Pretrained speech enhancement, separation, super-resolution, and audio-visual target-speaker extraction inference | Installable Python distribution `clearvoice`; public class `ClearVoice` | `clearvoice-inference` |
| SpeechScore | Objective speech quality scoring with intrusive and non-intrusive metrics | Source-layout component; import works when the SpeechScore component directory is importable | `speechscore-metrics` |
| Train | Training/fine-tuning, training-side inference launchers, target speaker extraction, and data generation | Repository scripts/configs with datasets, checkpoints, GPUs, and output mutation | `training-and-data-prep` |

## Verified package facts

- The installable distribution is `clearvoice` and exposes `from clearvoice import ClearVoice`.
- The distribution metadata version inspected for this snapshot is `0.1.2`; the package source `__version__` string is `0.1.0`, so treat the distribution metadata as the packaging version and the source string as an internal stale value.
- `ClearVoice(task, model_names)` accepts a task string and a list of model names.
- `ClearVoice.__call__(input_path, online_write=False, output_path=None)` dispatches either file/directory/list input mode for string inputs or tensor-to-tensor mode for NumPy/Torch inputs.
- `ClearVoice.write(results, output_path)` writes results from a previous non-`online_write` call.
- SpeechScore exposes `SpeechScore(scores='')`; the returned object is called as `scorer(test_path, reference_path, window=None, score_rate=None, return_mean=False)`.

## Operational prerequisites

- ClearVoice model instantiation may download model checkpoints from a model hub if the checkpoint directory is absent.
- Non-WAV ClearVoice input/output uses FFmpeg-compatible media tooling through audio/video libraries.
- Real training and evaluation workflows usually require CUDA-capable PyTorch, datasets, checkpoints, and deliberate output directories.
- SpeechScore full metric support requires the repository runtime metric dependencies; deep non-intrusive metrics can additionally require model assets.

## Route selection

1. If the user wants to process audio/video with pretrained ClearVoice models, load `sub-skills/clearvoice-inference/SKILL.md`.
2. If the user wants PESQ/STOI/SI-SDR/SNR/DNSMOS/NISQA/DISTILL_MOS or other quality scores, load `sub-skills/speechscore-metrics/SKILL.md`.
3. If the user wants to train, fine-tune, prepare data lists, edit configs, run training-side inference, or generate noisy/reverb training data, load `sub-skills/training-and-data-prep/SKILL.md`.
