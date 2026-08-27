---
name: pipeline-basics
description: "Install/import OpenPrompt, inspect the public pipeline APIs, and
  build the minimal PromptDataLoader/PromptForClassification/PromptForGeneration
  flow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Basics

Use this sub-skill for the OpenPrompt package-usage surface: install checks, public exports, `InputExample` / `InputFeatures`, `PromptDataLoader`, `PromptForClassification`, `PromptForGeneration`, and `load_plm`.

Start here:

- `references/api-reference.md` for verified signatures and return contracts.
- `references/workflows.md` for the minimal classification/generation quickstart and the no-download smoke.
- `references/troubleshooting.md` for dependency and wrapper failures.
- `scripts/check_openprompt_install.py` for the canonical import/API smoke.

Operating rules:

1. Keep to the basic pipeline. Do not expand into prompt-template grammar, prompt-asset curation, dataset acquisition, or training-loop tuning.
2. Prefer the smoke script before deeper debugging. It runs from a temporary working directory, imports the installed `openprompt` package, avoids downloads, and checks the fake-wrapper loader path.
3. `PromptDataLoader` accepts either a ready wrapper object or a wrapper class plus tokenizer; the wrapper class must expose the constructor kwargs filtered by the loader.
4. Route template/verbalizer design to `../template-verbalizer-design/`, data/config work to `../data-and-config-workflows/`, and training/runtime issues to `../training-and-generation/`.
