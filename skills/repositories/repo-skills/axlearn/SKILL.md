---
name: axlearn
description: "Routes AXLearn training, language-model, vision, audio/ASR, and
  GCP CLI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AXLearn

AXLearn is a JAX-based deep learning library with a config system, trainer runtime,
vision/audio experiment catalogs, and a GCP launcher/ops CLI.

Use this skill when the user asks about:

- `axlearn.common` configs, modules, trainers, inputs, learners, checkpointers, or launchers.
- `axlearn` CLI commands such as `gcp config`, `gcp bundle`, `gcp launch`, `gcp vm`, `gcp bastion`, `gcp dataflow`, `gcp logs`, or `gcp auth`.
- Vision workflows such as ImageNet, ResNet, CLIP, or other image-classification configs.
- Audio/ASR workflows such as Conformer, LibriSpeech, feature extraction, or WER evaluation.
- GPT / language-model trainer catalogs, tokenizers, MoE configs, or flash-attention paths.

## Start here

1. Read `references/repo-provenance.md` if you need to check whether this skill is current for the checkout.
2. Read `references/troubleshooting.md` when installation, import, or optional dependency checks fail.
3. Use `scripts/check_install.py` for a safe import/version smoke check.
4. Route to the matching sub-skill:
   - `sub-skills/training-core/` for trainer configs, fake-data smoke checks, and tokenizer setup.
   - `sub-skills/language-models/` for GPT, MoE, flash-attention, and tokenizer catalog workflows.
   - `sub-skills/cli-cloud/` for GCP config, bundle, launch, VM, bastion, Dataflow, logs, and auth.
   - `sub-skills/vision-workflows/` for ResNet/ImageNet and other vision model recipes.
   - `sub-skills/audio-asr/` for Conformer, LibriSpeech, and ASR workflows.

## Installation and smoke check

For local inspection, install the editable package with the extras that match the workflow.
Start with the base package, then add only the extras you need:

```bash
python -m pip install -e .
python -m pip install -e .[core,dev]
```

Common add-ons:

- `audio` for ASR workflows.
- `gcp` for cloud CLI workflows.
- `orbax` when checkpoint utilities are needed.
- `dev` only if you plan to run repo tests.

Minimal smoke checks:

```bash
python -I -c "import axlearn; print(axlearn.__file__)"
axlearn --help
```

If you are using the cloud CLI routes, also check:

```bash
axlearn gcp --help
```

## Routing guidance

- Use `training-core` for local config construction, `SpmdTrainer`, `launch_trainer_main`, fake inputs, and short tutorial-style probes.
- Use `language-models` when the task names Fuji, Gala, Honeycrisp, Qwen, C4, Pajama, MoE, or flash attention.
- Use `cli-cloud` when the task names GCP activation, bundling, launching, bastion, Dataflow, logs, or auth.
- Use `vision-workflows` when the task names ImageNet, ResNet, image classification, or CLIP-like vision recipes.
- Use `audio-asr` when the task names LibriSpeech, Conformer, speech features, ASR, or WER.

If the task spans trainer config mechanics plus a domain family, start in `training-core` and then jump to the domain sub-skill.
