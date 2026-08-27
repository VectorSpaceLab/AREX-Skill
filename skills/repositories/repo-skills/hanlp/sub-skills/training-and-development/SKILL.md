---
name: training-and-development
description: "Guides HanLP training, fine-tuning, editable source installs,
  focused tests, optional backend choices, and safe inspection of training APIs
  without launching expensive jobs by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training And Development

Use this sub-skill when the user wants to train or fine-tune HanLP components, inspect `fit`/`evaluate` APIs, maintain a source checkout, run focused tests, choose optional extras, or adapt training demos safely.

## Read First

- Read `references/training-recipes.md` for source-backed tokenizer/classifier training recipes and safety boundaries.
- Read `references/development-guide.md` for editable install order, CI-style tests, and maintainer workflow guidance.
- Read `references/troubleshooting.md` for dataset/cache/device/training failures.
- Run `scripts/inspect_training_api.py --json` to inspect training signatures without downloads or training.

## Minimal Maintainer Setup

```bash
python -m pip install -e plugins/hanlp_trie
python -m pip install -e plugins/hanlp_common
python -m pip install -e plugins/hanlp_restful
python -m pip install -e .
python -m pip install pytest
```

Run bundled source-free helper checks for the affected area from the generated skill root before any expensive validation:

```bash
python scripts/check_hanlp_environment.py --json
python sub-skills/rules-and-trie/scripts/rules_smoke.py
python sub-skills/rules-and-trie/scripts/trie_smoke.py
python sub-skills/native-workflows/scripts/pipeline_smoke.py
python sub-skills/training-and-development/scripts/inspect_training_api.py --json
```

For source-maintainer work, choose private native tests from the checkout only after deciding the edited area and avoiding live RESTful, model-download, or training-scale jobs by default. Training scripts may download datasets/models, write model artifacts, and require GPU/time.
