# Stanza Package Overview

## Purpose

Stanza is a Python NLP library for many languages. Its public surfaces in this skill are:

- neural pipelines for tokenization, MWT, POS/morphology, lemma, dependency parsing, NER, sentiment, constituency, coref, language ID, and morph segmentation when resources exist;
- resource download/cache management for model packages and language bundles;
- CoNLL-U and `Document` data objects;
- a Python client for Java Stanford CoreNLP;
- training/data-preparation utilities for Stanza models;
- demos and visualization helpers.

## Install and dependencies

Typical install:

```bash
python -m pip install stanza
```

Source/development install:

```bash
python -m pip install -e .
```

Base runtime dependencies include PyTorch, NumPy, requests, protobuf, NetworkX, tqdm, Hugging Face Hub, platformdirs, emoji, and UD evaluation utilities. PyTorch may install CPU or CUDA-capable wheels depending on the environment and package index.

Optional extras exposed by package metadata include:

- `transformers`: transformer and PEFT-adjacent model support.
- `datasets`: dataset integration support.
- `tokenizers`: optional tokenizer variants such as Jieba, PyThaiNLP, python-crfsuite, spaCy, Sudachi.
- `visualization`: spaCy, Streamlit, and IPython-backed visualization.
- `matplotlib`: plot support.
- `morphseg`: morpheme segmentation dependency.
- `test` and `dev`: test/development utilities.

Install only the extra needed by the selected workflow.

## Model resources

Stanza model resources are versioned separately from the Python package. Important controls:

- `stanza.download(...)` stages resources explicitly.
- `Pipeline(..., download_method=...)` controls automatic resource checks/downloads.
- `DownloadMethod.NONE` forbids model/resource downloads and is best for offline validation.
- `DownloadMethod.REUSE_RESOURCES` reuses an existing `resources.json` and downloads missing models.
- `DownloadMethod.DOWNLOAD_RESOURCES` refreshes `resources.json` and downloads missing/outdated models.
- `STANZA_RESOURCES_DIR`, `STANZA_RESOURCES_URL`, `STANZA_RESOURCES_VERSION`, and `STANZA_MODEL_URL` can alter cache and URL behavior.

## CoreNLP external dependency

The Python package includes a CoreNLP client, but live annotation requires a Java runtime and a Stanford CoreNLP distribution/model jars. Treat CoreNLP installation and server startup as explicit side effects; use the `corenlp-client` sub-skill before starting servers or downloads.

## Training and data workflows

Stanza training utilities can train many model families, but full training is expensive and data-dependent. Treat training as a staged workflow:

1. validate corpus formats and splits;
2. build a dry command;
3. run help/parser checks;
4. run a tiny smoke;
5. only then run full training with approved compute, output paths, and logging.

## Verification basis

The generated skill targets Stanza 1.14.0 behavior, with installed-package signature inspection for `Pipeline`, `MultilingualPipeline`, `download`, `Document`, `CoNLL`, `CoreNLPClient`, and resource listing helpers. Check `repo-provenance.md` before using the skill against another version.
