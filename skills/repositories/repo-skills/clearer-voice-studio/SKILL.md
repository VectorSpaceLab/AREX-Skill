---
name: clearer-voice-studio
description: "Route ClearerVoice-Studio tasks for ClearVoice inference,
  SpeechScore metrics, and speech-model training or data-preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearerVoice-Studio

Use this repo skill when a task involves ClearerVoice-Studio, the `clearvoice` package, ClearVoice pretrained speech processing models, SpeechScore quality metrics, or the repository's training and data-preparation workflows.

## Fast route map

| User task | Read |
| --- | --- |
| Use pretrained models for speech enhancement, speech separation, speech super-resolution, or audio-visual target speaker extraction | [sub-skills/clearvoice-inference/SKILL.md](sub-skills/clearvoice-inference/SKILL.md) |
| Choose `task`/`model_names`, validate file/directory/`.scp` inputs, handle NumPy/Tensor inference, or debug checkpoint/media issues | [sub-skills/clearvoice-inference/SKILL.md](sub-skills/clearvoice-inference/SKILL.md) |
| Compute PESQ, STOI, SI-SDR, SNR, DNSMOS, NISQA, DISTILL_MOS, or other SpeechScore metrics | [sub-skills/speechscore-metrics/SKILL.md](sub-skills/speechscore-metrics/SKILL.md) |
| Score matched directories, decide whether a clean reference is required, or troubleshoot metric dependencies | [sub-skills/speechscore-metrics/SKILL.md](sub-skills/speechscore-metrics/SKILL.md) |
| Train, fine-tune, resume, run training-side inference, prepare `.scp`/CSV data lists, or generate noisy/reverb training data | [sub-skills/training-and-data-prep/SKILL.md](sub-skills/training-and-data-prep/SKILL.md) |
| Check whether a local environment is ready without downloading weights or launching training | [scripts/check_clearer_voice_environment.py](scripts/check_clearer_voice_environment.py) |

## Component overview

Read [references/package-and-component-overview.md](references/package-and-component-overview.md) when you need the repository component map, verified public signatures, package/source layout notes, or high-level prerequisites.

Key facts:

- `clearvoice` is the installable package for ClearVoice inference: `from clearvoice import ClearVoice`.
- The public ClearVoice constructor is `ClearVoice(task, model_names)`.
- Calling a `ClearVoice` instance with a string path uses file/directory/`.scp` I/O mode; calling with a NumPy array or Torch tensor uses tensor-to-tensor mode.
- SpeechScore is a source-layout component in this snapshot; use its helper or source-layout notes when importing it outside its component directory.
- Training workflows are script/config based and should be treated as templates that require user-owned datasets, checkpoints, GPUs, and explicit output paths.

## Safe first checks

Before running expensive or mutating workflows:

1. Run `python scripts/check_clearer_voice_environment.py` to check `clearvoice`, Torch/CUDA visibility, and FFmpeg presence without loading model weights.
2. For SpeechScore source-layout checks, pass the user's SpeechScore component directory to `--speechscore-dir`.
3. Use each sub-skill's dry-run helper before real model inference, metric scoring, or training launch preparation.
4. Ask before starting model downloads, distributed training/evaluation, data generation, checkpoint overwrites, or package backend changes in a user-owned environment.

## Installation guidance

For pretrained ClearVoice package use:

```bash
pip install clearvoice
python - <<'PY'
from clearvoice import ClearVoice
print(ClearVoice)
PY
```

For full repository workflows such as SpeechScore metrics and training scripts, install the repository's documented runtime requirements in an isolated environment. Do not modify a user's existing working environment without approval.

## Troubleshooting

- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, CUDA, FFmpeg, model-download, and component-routing failures.
- Use sub-skill troubleshooting references for workflow-specific symptoms and recovery steps.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a different checkout or package version.

## Boundaries

Use this skill to operate the package/repository workflows, not to modify the ClearerVoice-Studio source code. If the user asks for generic speech recognition, TTS, diarization, or unrelated PyTorch training, route to a more specific skill. If the user asks to edit this repository's source, treat it as a repository-maintenance task and inspect the current checkout directly.
