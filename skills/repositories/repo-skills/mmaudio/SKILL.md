---
name: mmaudio
description: "Route MMAudio video-to-audio, text-to-audio, data preparation,
  CUDA training, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MMAudio

Use this repo skill when a task involves **MMAudio**, the PyTorch project for
synchronized audio generation from video and/or text. It is an operating guide
for future agents: it distills the repository's install, model assets, CLI/API,
training, data-preparation, and evaluation behavior without requiring the agent
to reopen the original source tree for normal use.

## First checks

1. Confirm the task is about MMAudio-style audio generation, video-to-audio,
   text-to-audio, the MMAudio model variants, training feature memmaps, or the
   repo's batch-evaluation/onset tooling.
2. Check whether the user needs a real model run. Real inference may download
   multi-GB model assets and is GPU/MPS-preferred; training/evaluation paths are
   CUDA/DDP-oriented.
3. If a checkout or package install is present, run
   [`scripts/check_mmaudio_env.py`](scripts/check_mmaudio_env.py) for a safe
   import/backend/config sanity check. It does not download weights or run a
   model.
4. Read [`references/repo-provenance.md`](references/repo-provenance.md) before
   deciding whether this skill is stale for a newer checkout.

## Route map

| User intent | Read this |
| --- | --- |
| Generate audio for one prompt/video, build a `demo.py` command, use Gradio, or call `mmaudio.eval_utils.generate` | [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) |
| Partition audio, validate captions/clip manifests, plan CLIP/Synchformer/VAE feature extraction, or inspect TensorDict memmap schemas | [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) |
| Launch or debug DDP training, bounded smoke runs, checkpoint/weights resume, EMA synthesis, or Hydra training overrides | [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md) |
| Run batched generation for AudioCaps/VGGSound/MovieGen-style evaluation data or compute onset metrics | [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md) |

## Shared references

- [`references/model-assets.md`](references/model-assets.md) lists MMAudio model
  variants, required checkpoint filenames, download/checksum behavior, sample
  rates, and license caveats.
- [`references/configuration.md`](references/configuration.md) summarizes shared
  Hydra conventions, sequence-length facts, default paths, and override style.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers
  cross-cutting install/import, CUDA, download, media, and dependency failures.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  is structured metadata for managed repo-skill routing.

## Installation and environment baseline

MMAudio is a Python package named `mmaudio` and requires Python 3.9+. The
repository documentation recommends a Miniforge/Conda-style environment on
Ubuntu. Install a CUDA-capable PyTorch stack first when GPU workflows are in
scope, then install the package in editable mode:

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --upgrade
python -m pip install -e <MMAudio checkout>
```

The package metadata declares dependencies such as `torchcodec`,
`huggingface_hub`, `hydra-core`, `gradio`, `open_clip_torch`, `av`, `timm`,
`tensordict`, `librosa`, `torchdiffeq`, and `nitrous-ema`. Training and the
built-in metric/sample path also depend on the external `av_bench` package from
the MMAudio authors' av-benchmark project.

## Model families at a glance

| Variant | Mode | Typical use |
| --- | --- | --- |
| `small_16k` | 16 kHz | Lower sample rate, smaller network, training/evaluation examples. |
| `small_44k` | 44.1 kHz | Smaller high-sample-rate generation. |
| `medium_44k` | 44.1 kHz | Larger high-sample-rate model. |
| `large_44k` | 44.1 kHz | Heavy high-sample-rate model. |
| `large_44k_v2` | 44.1 kHz | Recommended default for general inference. |

Every inference/evaluation variant needs a flow-prediction checkpoint, a VAE,
and the Synchformer checkpoint; 16 kHz additionally uses the BigVGAN vocoder
file. See the model-assets reference before downloading or debugging weights.

## Boundaries and cautions

- This skill is for operating MMAudio, not for general audio ML, TTS, ASR, or
  unrelated diffusion models.
- Full generation, training, and batch evaluation can be expensive and may
  download large files. Use the bundled command builders and schema checks
  before launching CUDA work.
- Do not treat CPU import success as proof that CUDA training, feature
  extraction, or batch evaluation will work. Those code paths use CUDA/NCCL.
- The generated helper scripts print or validate commands by default; they do
  not modify model weights, launch servers, download checkpoints, or start
  training unless a user separately runs the printed project command.
