---
name: training-and-data-prep
description: "Guide safe Stanza training, evaluation, and dataset preparation
  across model families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Data Prep

Use this sub-skill when you need to prepare corpora or build training and evaluation command plans for Stanza model families.

It covers:
- tokenizer, MWT, POS, lemma, dependency parsing, NER, constituency, charlm, classifier, lang_identifier, and wl_coref workflows;
- wrapper scripts under `stanza.utils.training`;
- dataset preparation helpers under `stanza.utils.datasets`;
- safe command templates that avoid accidental downloads, wandb side effects, or save-dir collisions.

These details were distilled from installed Stanza 1.14.0 training/data utilities, selected tests, CI setup, and command help.

## Start here
1. Read `references/cli-reference.md` to choose the right entry point.
2. Run `scripts/build_training_command.py --help` or `scripts/build_training_command.py <task> <name> --mode train` to print a safe command template.
3. Copy or source `scripts/config_template.sh` to set local data roots and output directories.
4. Read `references/data-preparation.md` before moving any corpus files.
5. Use `references/training-workflows.md` for direct-module versus wrapper choices.
6. Use `references/troubleshooting.md` when a corpus, schema, pretrain, charlm, GPU, or logging step fails.

## Boundaries
- Route pipeline inference and resource loading to `pipelines-and-resources`.
- Route raw `Document`/CoNLL-U manipulation to `documents-and-conllu`.
- Route demos and browser-facing rendering to `visualization-and-demos`.
- Do not start training or large downloads from this sub-skill.

## Bundled helpers
- `scripts/build_training_command.py` prints representative `python -m` command templates, validates task names, and never launches a job.
- `scripts/config_template.sh` mirrors the common training environment variables with safe defaults and placeholders.
