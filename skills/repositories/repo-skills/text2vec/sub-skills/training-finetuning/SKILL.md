---
name: training-finetuning
description: "Route supervised and contrastive fine-tuning for CoSENT,
  Sentence-BERT, BERT-match, and BGE, including dataset schemas, validation
  helpers, command construction, and GPU/multi-card boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Fine-tuning

Use this sub-skill for text-matching and retrieval fine-tuning workflows:
- CoSENT
- Sentence-BERT
- BERT-match
- BGE

Use the bundled validators before training custom data.

## Route away
- embeddings-only inference → embeddings
- benchmark reporting or model choice → evaluation-benchmarks
- serving or deployment → serving-deployment

## Read in order
1. `references/data-formats.md`
2. `references/api-reference.md`
3. `references/training-workflows.md`
4. `references/troubleshooting.md`

## Bundled scripts
- `scripts/validate_text_matching_data.py`
- `scripts/validate_bge_jsonl.py`

## Operating notes
- Full training may need network access, GPU hardware, bf16 support, or Hugging Face dataset cache.
- Keep `output_dir` dedicated to one experiment; it is the reload path for prediction.
- Do not assume field names are uniform: the loaders accept either `sentence1`/`sentence2` or `text1`/`text2`.
