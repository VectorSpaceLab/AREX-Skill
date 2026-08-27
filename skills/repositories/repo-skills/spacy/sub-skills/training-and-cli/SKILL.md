---
name: training-and-cli
description: "Config-driven training, conversion, debugging, and packaging
  workflows for spaCy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-and-cli

Enable config-driven training, evaluation, packaging, and safe CLI/data-conversion workflows for spaCy without large training runs or downloads by default.

## Use this sub-skill for
- generating and completing training configs;
- validating config, data, and package compatibility;
- converting IOB, CoNLL, JSON, and tiny textcat JSONL data to `.spacy`;
- bounded CPU-first training and evaluation smoke checks.

## Read
- [`references/training-and-cli.md`](references/training-and-cli.md) for the command map and recommended order of operations.
- [`references/config-reference.md`](references/config-reference.md) for `[paths]`, `[system]`, `[nlp]`, `[components]`, `[corpora]`, `[training]`, `[initialize]`, and `[pretraining]`.
- [`references/data-formats-and-conversion.md`](references/data-formats-and-conversion.md) for `.spacy`, `DocBin`, `Corpus`, `Example`, and conversion recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) when config, data, threshold, package, or registry errors need triage.
- [`scripts/config_smoke.py`](scripts/config_smoke.py) to run a safe config round-trip and validation smoke.
- [`scripts/convert_textcat_jsonl_to_docbin.py`](scripts/convert_textcat_jsonl_to_docbin.py) to convert tiny textcat JSONL into `.spacy` without model downloads.

## Route out
- Project orchestration and `spacy project` commands go to `project-workflows`.
- Custom component and factory Python implementation goes to `pipeline-components`.
- `Doc`, `DocBin`, tokenizer, matcher, and visualization details go to `documents-and-visualization`.
- Installation, import, backend, and extra-dependency issues go to `install-and-inspect`.

## Safe default order
1. `init config` or `init fill-config`
2. `debug config`
3. `convert`
4. `debug data`
5. `train`
6. `evaluate`
7. `package`
8. `validate`

## Triage rule
- If `debug config` fails, fix config or registry references first.
- If `debug config` passes but `debug data` fails, inspect paths, corpus files, or annotations next.

Never run full training by default; keep training smoke tests tiny and CPU-first unless the environment explicitly proves otherwise.
