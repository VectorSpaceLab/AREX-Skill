---
name: models-and-embeddings
description: "Guides Semantra embedding model selection, OpenAI and Hugging Face
  backends, pooling options, and backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Semantra Models and Embeddings

Use this sub-skill when the task is to choose, inspect, or troubleshoot the
embedding model Semantra uses while indexing documents and running semantic
queries.

## Read first

- [model-selection.md](references/model-selection.md) for preset model choices,
  custom Hugging Face commands, OpenAI privacy/cost tradeoffs, CUDA expectations,
  and pooling knobs.
- [api-reference.md](references/api-reference.md) for verified Semantra model
  classes, registry defaults, and embedding helper methods.
- [troubleshooting.md](references/troubleshooting.md) for OpenAI credentials and
  SDK compatibility, Hugging Face downloads, CUDA/memory, SGPT/SVM, and pooling
  failures.
- Run [inspect_model_registry.py](scripts/inspect_model_registry.py) when you
  need to inspect the installed Semantra preset registry without instantiating
  models or downloading weights.

## Route here when

- The user asks which `--model` value to use: `mpnet`, `minilm`, `sgpt`,
  `sgpt-1.3B`, or `openai`.
- The user wants a custom Hugging Face transformer with `--transformer-model`.
- The user asks whether Semantra can use a GPU or why it is slow on CPU.
- The user needs OpenAI setup, cost/privacy guidance, or an `OPENAI_API_KEY`
  diagnosis.
- The user is tuning `--pool-size`, `--pool-count`, document/query special
  tokens, or SGPT-style asymmetric query/document tokens.
- The user sees errors from `torch`, `transformers`, `tiktoken`, `openai`, or
  missing `scikit-learn` while using model-related options.

Route file preprocessing, cache artifacts, `--windows`, and `--semantra-dir` to
[document-indexing](../document-indexing/SKILL.md). Route query arithmetic,
result tags, and local web UI behavior to
[interactive-search](../interactive-search/SKILL.md).

## Default decision flow

1. For private local search, start with a local transformer model. The default
   `mpnet` is the documented quality-oriented default. Use `minilm` when speed
   and small memory footprint matter more than accuracy.
2. For larger or more accurate local models, consider `sgpt` or `sgpt-1.3B`.
   SGPT presets are asymmetric: queries and documents are wrapped in different
   special tokens. Do not combine asymmetric models with `--svm`.
3. For non-English or specialized domains, use a custom Hugging Face model:

   ```sh
   semantra --transformer-model intfloat/multilingual-e5-base <files>
   ```

   Add `--query-token-pre`, `--query-token-post`, `--doc-token-pre`, and
   `--doc-token-post` only when the model documentation requires those tokens.
4. Use `--model openai` only after the user accepts the privacy, network, API
   key, and cost implications. Semantra sends document windows and queries to
   OpenAI in that mode.
5. Confirm the installed registry before a risky run:

   ```sh
   python path/to/inspect_model_registry.py
   semantra --list-models
   ```

## Backend expectations

Semantra's transformer backend asks PyTorch whether CUDA is available. If it is,
`TransformerModel(..., cuda=None)` moves the model and token tensors to CUDA;
otherwise CPU execution is used. CUDA is an acceleration path, not a requirement
for core Semantra behavior.

The first transformer run may download tokenizer/model files from Hugging Face
unless they are already cached. Plan disk, network, and privacy constraints
before indexing a large or sensitive corpus.

## Known compatibility edges

- Semantra 0.1.12 imports `pkg_resources`. Some modern Setuptools environments
  no longer provide it; see the root troubleshooting reference for the
  `setuptools<81` workaround or code-update option.
- Semantra 0.1.12 calls the legacy `openai.Embedding.create` API. If a current
  OpenAI SDK reports an `APIRemovedInV1Proxy` or similar error, use a compatible
  `openai<1` environment or update Semantra's OpenAI integration before relying
  on `--model openai`.
- `--svm` lazily imports `sklearn.svm`, but `scikit-learn` is not declared in
  Semantra's package dependencies. Install it explicitly if that route is
  selected.

## Validation signals

A model-selection answer should include:

- the exact command flags;
- whether model weights or API calls will cross the network;
- whether input text leaves the user's machine;
- expected memory/runtime tradeoffs;
- a safe check such as `semantra --list-models` or
  `inspect_model_registry.py --json` before a costly indexing run.
