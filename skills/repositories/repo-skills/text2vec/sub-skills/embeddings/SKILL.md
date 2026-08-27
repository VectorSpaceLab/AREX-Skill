---
name: embeddings
description: "SentenceModel, SBert, Word2Vec, EncoderType, batch embedding CLI,
  device selection, and multi-process encoding workflows for text2vec."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# embeddings

Use this sub-skill when you need to turn text into vectors with text2vec.

## Covers
- SentenceModel / SBert inference
- EncoderType selection and sentence embedding dimension lookup
- batch encoding with the public text2vec CLI or the bundled helper script
- Word2Vec local-file and built-in Tencent lightweight model workflows
- stopwords, local cache behavior, and offline tiny fixtures
- multi-process encoding lifecycle for large SentenceModel jobs
- reference-only NGram / KenLM caveat
- short fallback notes for raw Transformers or sentence-transformers pooling

## Not covered
- Pairwise similarity, dense search, or BM25 retrieval: use the sibling similarity-search sub-skill.
- Training, fine-tuning, or dataset schema work: use training-finetuning.
- Benchmark/model-choice interpretation: use evaluation-benchmarks.
- HTTP, Jina, or Gradio deployment: use serving-deployment.

## Start here
- `references/api-reference.md` for signatures, return shapes, and supported encoder values.
- `references/workflows.md` for local-model, CSV/JSONL, and multi-process recipes.
- `references/word2vec-and-ngram.md` for Word2Vec cache/download behavior and the NGram warning.
- `references/troubleshooting.md` for install, download, device, and CLI failure modes.

## Bundled scripts
- `scripts/encode_texts.py`: read one sentence per line and write JSONL or CSV embeddings.
- `scripts/make_tiny_word2vec_fixture.py`: generate a tiny local word2vec-format file for offline smoke tests.

## Practical rule
- Use SentenceModel / SBert for general embedding generation.
- Use Word2Vec when you explicitly want word-level or cold-start lexical vectors.
- If you need scoring or search over embeddings, switch to the sibling similarity-search sub-skill.
