---
name: pipelines-cli
description: "Use Fengshen public pipeline APIs and the fengshen-pipeline
  console command for safe prediction/training orchestration, fixtures, and
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Fengshen Pipelines and CLI

Use this sub-skill when the task is to run, adapt, inspect, or troubleshoot Fengshen public pipeline surfaces or the `fengshen-pipeline` console command.

## Start here

1. Read [references/cli-reference.md](references/cli-reference.md) before using `fengshen-pipeline`; the console command is generic, but not every pipeline class is console-compatible.
2. For classification prediction/training data, read [references/text-classification.md](references/text-classification.md) and generate a tiny local fixture with [scripts/make_classification_fixture.py](scripts/make_classification_fixture.py).
3. For NER/sequence tagging, read [references/sequence-tagging.md](references/sequence-tagging.md) and generate the expected `labels.txt` plus `*.all.bmes` layout with [scripts/make_sequence_tagging_fixture.py](scripts/make_sequence_tagging_fixture.py).
4. For UniMC, UniEX, and Ubert programmatic routes, read [references/unimc-uniex-ubert.md](references/unimc-uniex-ubert.md).
5. For TCBert prompt classification, read [references/tcbert.md](references/tcbert.md).
6. When behavior is surprising, use [references/troubleshooting.md](references/troubleshooting.md) before assuming the installed package is broken.

## Safe checks first

These checks do not download models, start training, or mutate checkpoints:

```bash
python scripts/inspect_pipeline_cli.py --pipeline text_classification --pipeline sequence_tagging
python scripts/inspect_pipeline_cli.py --pipeline unknown_name
python scripts/make_classification_fixture.py --out-dir ./fengshen-classification-fixture
python scripts/make_sequence_tagging_fixture.py --out-dir ./fengshen-sequence-tagging-fixture
```

Use `fengshen-pipeline text_classification predict --help` only as a help/import check. Real `predict` and `train` calls may download model weights or datasets unless all paths are local and cached.

## Route boundaries

- Model class selection, custom configs, tokenizers, and `fengshen_model_type` mapping belong to `model-zoo`.
- `UniversalDataModule`, checkpoints, optimizers, PyTorch Lightning Trainer flags, Deepspeed, CUDA, and low-level dataloaders belong to `data-training`.
- Large example command families, CLUE recipes, Stable Diffusion, Ziya, and checkpoint conversion planning belong to `examples-conversion`.
- This sub-skill owns pipeline entry points, parser shapes, task data schemas, safe fixtures, and CLI misuse diagnosis.

## Do not do these from this sub-skill

- Do not run original repository tests or example shell scripts as a smoke check; several have hard-coded local paths or GPU assumptions.
- Do not treat `--help` success as proof that model downloads, CUDA execution, Deepspeed training, or checkpoint loading are verified.
- Do not use unsupported pipeline names or programmatic-only classes through `fengshen-pipeline` without first checking their route in [references/cli-reference.md](references/cli-reference.md).
