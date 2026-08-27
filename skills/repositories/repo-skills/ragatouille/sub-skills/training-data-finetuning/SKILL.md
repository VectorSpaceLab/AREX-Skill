---
name: training-data-finetuning
description: "Prepare RAGatouille ColBERT training data and run RAGTrainer
  fine-tuning safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training Data and Fine-Tuning

Use this sub-skill when the task is to prepare ColBERT training files, validate retrieval training examples, mine or sample negatives, split corpora into passages, or launch RAGatouille `RAGTrainer` training/fine-tuning.

## Scope

This sub-skill covers:
- `RAGTrainer.__init__`, `add_documents`, `prepare_training_data`, `export_training_data`, and `train`.
- `TrainingDataProcessor.process_raw_data` for direct offline conversion when a trainer/model should not be initialized.
- `CorpusProcessor.process_corpus` and `llama_index_sentence_splitter` for turning raw documents into `{document_id, content}` chunks.
- `SimpleMiner` hard-negative mining, model sizes, language routing, and safe fallbacks.
- Raw-data modes: pairs, labeled pairs, triplets, `all_documents`, `data_out_path`, labels, and generated ColBERT files.

Route other work elsewhere:
- Persisted indexes, loading trained checkpoints for search, index CRUD, and post-training retrieval: `../pretrained-indexing-search/SKILL.md`.
- In-memory reranking without building an index: `../index-free-reranking/SKILL.md`.
- LangChain/LlamaIndex integration wrappers and model export: `../integrations-export/SKILL.md`.

## Fast Start

1. Identify exactly one raw-data mode per `prepare_training_data` call: `pairs`, `labeled_pairs`, or `triplets`; do not mix modes in one list.
2. From this sub-skill directory, validate a JSON sample offline before initializing `RAGTrainer`:
   ```bash
   python scripts/validate_training_data.py examples.json --mode auto
   ```
3. For safe local conversion without downloads, use `TrainingDataProcessor` with `mine_hard_negatives=False`; use `RAGTrainer` only when model initialization and possible downloads are acceptable.
4. Export training data to a versioned directory containing `corpus.train.colbert.tsv`, `queries.train.colbert.tsv`, and `triples.train.colbert.jsonl`.
5. Treat `train()` as expensive GPU/model work; run it only after data files exist and the runtime has the requested base checkpoint and suitable hardware.

## Read Next

- API signatures and defaults: `references/api-reference.md`.
- Raw input shapes and ColBERT output files: `references/data-formats.md`.
- Preparation, hard-negative, and training recipes: `references/workflows.md`.
- Failure modes and recovery choices: `references/troubleshooting.md`.
