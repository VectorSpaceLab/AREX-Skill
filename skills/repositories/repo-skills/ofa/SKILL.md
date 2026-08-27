---
name: ofa
description: "Routes OFA workflows for multimodal pretraining, captioning, VQA,
  RefCOCO, OCR, ImageNet, image generation, Gigaword, GLUE, and MMSpeech, with
  safe setup and validation helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OFA

OFA is a unified sequence-to-sequence repository for vision-language, text, image generation, language understanding, and speech workflows.

Use this skill when a user wants to:

- run or adapt OFA training or evaluation commands,
- validate OFA TSV / manifest layouts before a long GPU job,
- reproduce caption, VQA, RefCOCO, OCR, ImageNet, Gigaword, GLUE, or MMSpeech workflows,
- inspect OFA model, task, or criterion registration,
- understand prompt tuning, adapters, bitfit, or encouraging loss,
- or reason about the repo's bundled Fairseq fork and command-line entry points.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) if you need to know whether this skill matches the current checkout.
2. Run [scripts/check_ofa_environment.py](scripts/check_ofa_environment.py) with `--check-clis` to confirm the repo import path, CUDA availability, and CLI help surface.
3. Use [scripts/render_ofa_command.py](scripts/render_ofa_command.py) when you need a copyable launch command instead of hand-writing a long distributed invocation.

## Shared helpers

- [scripts/check_ofa_environment.py](scripts/check_ofa_environment.py) checks imports, package versions, CUDA readiness, and optional CLI help.
- [scripts/render_ofa_command.py](scripts/render_ofa_command.py) renders a safe OFA train/evaluate command without executing it.

## Router map

### [setup-and-command-building](sub-skills/setup-and-command-building/SKILL.md)
Use this for installation, `PYTHONPATH`, `--user-dir`, distributed launch shape, port selection, and command rendering. It is the first stop when a user says "how do I run OFA" or "why does `train.py` import fail?"

### [data-formats](sub-skills/data-formats/SKILL.md)
Use this for TSV rows, selected-column layouts, base64 image payloads, image-code sequences, COCO-style caption rows, VQA answer fields, RefCOCO boxes, OCR data, ImageNet label rows, Gigaword/GLUE tables, and MMSpeech manifests.

### [pretraining](sub-skills/pretraining/SKILL.md)
Use this for multimodal pretraining and continuous pretraining, including the `vision_language_examples.tsv`, `text_examples.tsv`, `image_examples.tsv`, `detection_examples.tsv`, and `negative_sample/` layout.

### [vision-language-tasks](sub-skills/vision-language-tasks/SKILL.md)
Use this for captioning, VQA, RefCOCO / RefCOCO+ / RefCOCOg, SNLI-VE, OCR, and ImageNet finetuning or evaluation.

### [image-generation](sub-skills/image-generation/SKILL.md)
Use this for text-to-image generation, VQGAN code conversion, CLIP ranking, and image-generation validation.

### [language-tasks](sub-skills/language-tasks/SKILL.md)
Use this for Gigaword summarization and GLUE-style text understanding tasks such as CoLA, MNLI, RTE, QNLI, QQP, MRPC, and SST-2.

### [mmspeech](sub-skills/mmspeech/SKILL.md)
Use this for MMSpeech staged ASR pretraining/evaluation, speech manifests, fbank configuration, and WER troubleshooting.

### [model-internals-and-extension](sub-skills/model-internals-and-extension/SKILL.md)
Use this for task/model/criterion registration, architecture inspection, prompt tuning, adapters, bitfit, encouraging loss, and adding new OFA extensions.

## Installation

From the repo root, install the public dependencies with:

```bash
pip install -r requirements.txt
```

## Public prerequisites

- The repo's Python requirements.
- A CUDA-capable environment for the task workflows; CPU is only a partial substitute for setup checks.
- Java 1.8 if you want full COCO caption evaluation with SPICE.
- External datasets and checkpoints for the actual task runs.

## Minimal verification

After install, run:

```bash
python scripts/check_ofa_environment.py --check-clis
```

A healthy result shows the repo imports, the bundled Fairseq fork is visible, CUDA is available when expected, and `train.py` / `evaluate.py` print help successfully.

## Read more

- [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, backend, Java, and dependency issues.
- [references/repo-provenance.md](references/repo-provenance.md) for the source commit, branch, and staleness baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) for router placement and scenario metadata.
