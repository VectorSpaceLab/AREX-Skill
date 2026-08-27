---
name: synonyms
description: "Chinese synonyms, word/vector similarity, segmentation, keyword
  extraction, and model troubleshooting workflows for the chatopera/Synonyms
  package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Synonyms Repo Skill

Use this skill when a task involves the `synonyms` Python package (Chatopera Synonyms), Chinese synonym lookup, Chinese sentence/word similarity, jieba-backed segmentation, keyword extraction, or troubleshooting the package's licensed word2vec model loading.

## First checks

1. Read [references/model-and-environment.md](references/model-and-environment.md) before importing the package. `import synonyms` immediately initializes jieba and loads a word2vec model.
2. If the task depends on real semantic neighbors or production similarity scores, require a real compatible model: either let Synonyms download its licensed model via `SYNONYMS_DL_LICENSE`, or set `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN` to an existing binary word2vec `.gz` model.
3. For install/API mechanics only, run the bundled smoke probe with a tiny generated fixture:

```bash
python scripts/synonyms_smoke_probe.py --use-tiny-fixture --word 人脸
```

That fixture is not a semantic-quality substitute for the full Synonyms model.

## Routes

| User intent | Read/use |
| --- | --- |
| Install Synonyms, choose a model path, configure license/model/debug/dictionary environment variables, or avoid import-time downloads. | [references/model-and-environment.md](references/model-and-environment.md) |
| Use `nearby`, `display`, `compare`, `v`, `sv`, `bow`, `seg`, `keywords`, or `describe` correctly. | [references/api-reference.md](references/api-reference.md) |
| Build common workflows: synonym lookup, sentence similarity, segmentation, keyword extraction, vector probing, quick smoke checks, evaluation/benchmark interpretation. | [references/workflows.md](references/workflows.md) |
| Diagnose missing model/license, bad model path/format, OOV behavior, noisy import output, vector dimensionality, package dependency, or API misuse failures. | [references/troubleshooting.md](references/troubleshooting.md) |
| Verify an installed package without relying on the original source checkout. | [scripts/synonyms_smoke_probe.py](scripts/synonyms_smoke_probe.py) |
| Check whether this skill is stale for a repository checkout. | [references/repo-provenance.md](references/repo-provenance.md) |

## Minimal real-model smoke pattern

```bash
# Option A: allow the package to download its licensed model on first import.
export SYNONYMS_DL_LICENSE="<license-id>"
python -c "import synonyms; print(synonyms.describe())"

# Option B: use an existing compatible binary word2vec model.
export SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN="/path/to/words.vector.gz"
python scripts/synonyms_smoke_probe.py --model-path "$SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN" --word 飞机
```

Use `nearby`/`compare` scores only after a real model is loaded. Use `--use-tiny-fixture` only to verify that the installed package and API routes execute.

## Boundaries

- This skill covers package usage and package-specific troubleshooting, not retraining the Synonyms model or modifying its vocabulary. The public FAQ says adding words to the Synonyms vocabulary is not supported.
- The original repository's maintainer release/upload scripts are intentionally not part of this runtime skill.
- Do not tell future agents to run repository-local `demo.py`, `benchmark.py`, or `scripts/test.sh`; their useful behavior is distilled into the bundled smoke probe and references.
