---
name: install-and-inspect
description: "Install and inspect spaCy environments with import, version,
  blank-pipeline, CLI, model-package, and optional backend probes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# install-and-inspect

Use this sub-skill when the task is to install the public `spacy` package, prove that it imports, inspect `spacy.__version__`, validate a blank English pipeline, check the `python -m spacy` CLI entry point, load an already-installed pipeline package/path, or probe optional extras/backends without downloading pretrained models by default.

## Fast route

1. Read [references/install-and-inspect.md](references/install-and-inspect.md) when choosing pip, conda, or source-install patterns and when running base import, blank tokenizer, model-load, `info`, `validate`, or CLI-help checks.
2. Read [references/optional-dependencies-and-backends.md](references/optional-dependencies-and-backends.md) when the user asks about `lookups`, `transformers`, CUDA/CuPy variants, Apple acceleration, or Japanese/Korean/Thai tokenizer extras.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when imports fail, compiled extensions mismatch, `spacy.load()` cannot find a model, `validate` reports stale pipelines, optional extras are missing, GPU selection is unclear, or the `spacy` console command is not on `PATH`.
4. Run [scripts/spacy_healthcheck.py](scripts/spacy_healthcheck.py) for a safe installed-package smoke check from any current working directory; use `--model`, `--prefer-gpu`, `--require-gpu`, or `--run-validate` only when those checks are explicitly needed.

## Minimal default procedure

Use `python -m spacy` instead of a bare `spacy` shell command when the active Python environment is uncertain.

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U spacy
python -m spacy --help
python -m spacy info --silent
python scripts/spacy_healthcheck.py
```

For a no-download API smoke, prefer `spacy.blank("en")` over `spacy.load("en_core_web_sm")`. Use `spacy.load()` only after a trained pipeline package or local pipeline directory exists.

## Boundaries and routes

- Full training, config lifecycle, `spacy train`, `spacy debug`, `spacy evaluate`, and `spacy package` belong to the `training-and-cli` sub-skill.
- `Doc`, `Token`, `Span`, tokenizer customization, matchers/rulers, serialization, scoring, and displaCy belong to the `documents-and-visualization` sub-skill.
- Custom components, factories, pipeline assembly/order, registry wiring, and pipe analysis belong to the `pipeline-components` sub-skill.
- `spacy project` templates, assets, run/dry-run, remotes, and DVC workflows belong to the `project-workflows` sub-skill.
- Maintainer release/version shell scripts are excluded from runtime use; inspect the installed public package instead.

## Evidence basis

This sub-skill is distilled from the package README, packaging metadata, public top-level APIs, CLI documentation/source, installed-package inspection, backend verification planning, native candidate mapping, and source-script inventory for the spaCy checkout. Runtime instructions are self-contained and do not require reopening the source checkout.
