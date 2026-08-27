---
name: tencent-ml-images
description: "Guides Tencent ML-Images data preparation, TensorFlow 1.x ResNet
  training/finetuning, and checkpoint inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tencent ML-Images

Use this repo skill when the task mentions Tencent ML-Images, the ML-Images
multi-label dataset, the public ResNet-101 code, TFRecord preparation, ImageNet
finetuning, single-label classification, or feature extraction.

## Start here

- Read [references/setup-and-scope.md](references/setup-and-scope.md) for the
  supported runtime shape, verified smoke environment facts, and what is and is
  not bundled.
- Read [references/repo-provenance.md](references/repo-provenance.md) when you
  need to confirm whether this skill matches the current checkout.
- Run `scripts/check_legacy_env.py` for a fast TensorFlow/OpenCV/source smoke
  before deeper workflow work.
- Use the sub-skill map below to route the request to the narrowest workflow.

## Sub-skill map

### `data-preparation`
Use this for ML-Images/OpenImages URL lists, image lists, dictionary files,
semantic hierarchy files, TFRecord conversion, and downloader validation.
Read [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md).

### `resnet-training`
Use this for the ResNet graph, pretraining, finetuning, flags, training command
construction, and training troubleshooting.
Read [sub-skills/resnet-training/SKILL.md](sub-skills/resnet-training/SKILL.md).

### `checkpoint-inference`
Use this for checkpoint-backed top-k classification and feature extraction.
Read [sub-skills/checkpoint-inference/SKILL.md](sub-skills/checkpoint-inference/SKILL.md).

## Common route examples

- "I need to turn URLs and local images into TFRecords" → `data-preparation`.
- "I want a command for ML-Images pretraining or ImageNet finetuning" →
  `resnet-training`.
- "I have a checkpoint and want labels or features" → `checkpoint-inference`.
- "I need to know whether this checkout still matches the skill" → read
  `references/repo-provenance.md` first.

## Runtime expectations

- The public repository is a legacy TensorFlow 1.x project. The verified smoke
  used TensorFlow 1.6.0 and OpenCV 4.2 in a CPU inspection environment; a newer
  TensorFlow 1.15 stack can trip over legacy flag registration in `flags.py`.
- Do not assume TensorFlow 2-only behavior is compatible with the original
  model scripts, because the source uses `tf.app`, `tf.contrib`, `tf.gfile`, and
  `tf.python_io`-era APIs.
- The README mentions Python 2.7, but the generated skill is organized around
  the source workflow surface and the verified legacy TensorFlow smoke. Follow
  the sub-skill troubleshooting pages for the safest runtime choice.

## Safe first checks

1. `python scripts/check_legacy_env.py`
2. If you have a checkout path, rerun with `--repo-root <checkout>`.
3. Then move to the relevant sub-skill and its bundled helper scripts.

## Shared guardrails

- Do not start bulk downloads, long training runs, or checkpoint restores before
  validating the data layout and compatibility flags.
- Do not use the source checkout as a documentation dependency. The bundled
  references and scripts should be enough for future agents.
- Do not confuse the public README shell snippets with a safe smoke check. Use
  the bundled helpers first, then decide whether the actual workflow is worth
  running.
