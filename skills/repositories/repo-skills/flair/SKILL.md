---
name: flair
description: "Use Flair for NLP annotation, embeddings, text/sequence model
  prediction, corpus loading, training/fine-tuning, HunFlair biomedical
  NER/linking, and production troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Flair

Use this skill when a task names the public `flair` Python package or asks for Flair-specific NLP workflows: `Sentence` annotations, pretrained taggers/classifiers, token/document embeddings, custom corpora, model training/fine-tuning, HunFlair/HunFlair2 biomedical NER/linking, or Flair cache/device troubleshooting.

## Install and baseline check

Flair 0.15.1 requires Python 3.9+ and PyTorch. A normal package-user starting point is:

```bash
pip install flair
python - <<'PY'
import flair
print(flair.__version__)
print(flair.device)
print(flair.cache_root)
PY
```

Set runtime policy before importing `flair`:

```bash
export FLAIR_DEVICE=cpu                 # verified baseline for this skill
export FLAIR_CACHE_ROOT="./flair-cache" # optional deliberate cache location
```

Named pretrained models, embeddings, datasets, and biomedical dictionaries may download public resources if they are not already cached. CUDA, multi-GPU, ONNX/provider runtimes, SciSpaCy, pyab3p, OCR/layout inputs, and large model downloads are optional paths unless the active environment verifies them.

For a safe package diagnostic that avoids model/data downloads, run [`scripts/collect_env.py`](scripts/collect_env.py) with `--json` or `--check-imports`.

## Route by task

- **Annotations, tokenization, prediction outputs, regex tagging, serialization, or visualization**: use [`tagging-and-annotations`](sub-skills/tagging-and-annotations/SKILL.md) for `Sentence`, `Token`, `Span`, `Relation`, `Label`, `DataPair`, `Classifier.load(...)`, label layers, tokenizers, splitters, `RegexpTagger`, `Sentence.to_dict()`, and NER HTML rendering.
- **Embedding choice, vector extraction, language-model embeddings, cache/device behavior, long-sentence/context, or optional ONNX/JIT optimization**: use [`embeddings-and-optimization`](sub-skills/embeddings-and-optimization/SKILL.md) for `Transformer*Embeddings`, `WordEmbeddings`, `FlairEmbeddings`, `StackedEmbeddings`, `DocumentPool/RNN/CNNEmbeddings`, `LanguageModel`, and tensor shape checks.
- **Custom corpora, label dictionaries, model construction, training/fine-tuning, checkpoints, TARS, multitask, relation/span training, or optional multi-GPU**: use [`training-and-datasets`](sub-skills/training-and-datasets/SKILL.md) for `ColumnCorpus`, `ClassificationCorpus`, `CSVClassificationCorpus`, JSONL, CoNLL-U, `MultiCorpus`, `ModelTrainer.train`, `ModelTrainer.fine_tune`, and the bundled NER helper.
- **Biomedical NER/linking**: use [`biomedical-nlp`](sub-skills/biomedical-nlp/SKILL.md) for HunFlair/HunFlair2, `EntityMentionLinker`, biomedical dictionaries, SciSpaCy tokenization, pyab3p abbreviation behavior, biomedical corpus offsets, and NER-vs-linking layer separation.

## Common starting points

- For first-time Flair prediction: create `Sentence(...)`, load a model with `Classifier.load(model_id)` only when downloads/cache are allowed, call `predict`, then read the exact layer with `sentence.get_labels("layer")` or `sentence.get_spans("layer")`.
- For a no-download annotation check: run `sub-skills/tagging-and-annotations/scripts/annotation_smoke.py --json`.
- For a no-download embedding check: run `sub-skills/embeddings-and-optimization/scripts/embedding_smoke.py --json`.
- For corpus/training planning: run `sub-skills/training-and-datasets/scripts/fine_tune_ner.py --help`, `--list-datasets`, or `--dry-run` before training.
- For biomedical linking without downloads: run `sub-skills/biomedical-nlp/scripts/biomedical_smoke.py --run-local-linker --json`.

## Shared references

- [`references/api-overview.md`](references/api-overview.md): verified package identity, key APIs/signatures, import caveats, and cross-cutting data/model objects.
- [`references/model-selection.md`](references/model-selection.md): task-to-model and embedding selection guide, including pretrained model IDs and when to use `Classifier.load`.
- [`references/troubleshooting.md`](references/troubleshooting.md): install/import, cache, device, download, optional dependency, and cross-sub-skill failure recovery.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot, package version, evidence paths, and staleness checks.

## Boundaries

This skill is a runtime package-use guide, not a maintainer release or CI guide. It does not cover website generation, release publishing, broad lint/type-check stacks, private datasets, long benchmark training, or quality claims for unrun optional backends. If a current checkout or installed Flair version differs materially from the provenance snapshot, refresh the skill before relying on exact API details.
