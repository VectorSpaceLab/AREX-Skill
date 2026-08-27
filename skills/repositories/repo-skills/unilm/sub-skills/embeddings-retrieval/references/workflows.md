# E5 and SimLM Retrieval Workflows

Use this reference to assemble commands and plans. Commands shown here are patterns derived from the UniLM E5 and SimLM scripts; evaluate safety, network access, GPU availability, and data readiness before running them.

## E5 BEIR Evaluation

Prefer the bundled command builder for planning:

```bash
python scripts/build_e5_eval_command.py beir --model intfloat/e5-small-v2 --output-dir ./outputs/e5-beir --dry-run
```

A full BEIR command has this shape:

```bash
python -u mteb_beir_eval.py \
  --model-name-or-path intfloat/e5-small-v2 \
  --output-dir ./outputs/e5-beir
```

Important behavior:

- Model basename selects the pool type and prefix type automatically when it is one of the known E5 checkpoints.
- BEIR retrieval uses `query: ` and `passage: ` prefixes for standard E5 models.
- Instruct models use task definitions converted to `Instruct: ...\nQuery: ` for queries and no passage prefix for corpus documents.
- Quora retrieval is symmetric; the source evaluator sets `--doc-as-query` internally for `QuoraRetrieval` when the model uses `query_or_passage` prefixes.
- `--dry-run` still imports models and benchmark libraries if executed; it only narrows task selection.

## E5 Non-Retrieval MTEB Evaluation

Plan a non-retrieval MTEB command with:

```bash
python scripts/build_e5_eval_command.py mteb \
  --model intfloat/multilingual-e5-base \
  --multilingual \
  --task-types STS Reranking Clustering \
  --output-dir ./outputs/e5-mteb
```

A direct command has this shape:

```bash
python -u mteb_except_retrieval_eval.py \
  --model-name-or-path intfloat/e5-small-v2 \
  --task-types STS Summarization PairClassification Classification Reranking Clustering BitextMining \
  --output-dir ./outputs/e5-mteb
```

Use `--multilingual` for multilingual E5 models when the intended benchmark should not be restricted to English tasks. Do not add `--multilingual` for English-only models unless the user intentionally wants broad multilingual MTEB tasks with an English model.

## Choosing E5 Prefixes and Pooling

1. Identify the model basename after the last slash, such as `e5-large-v2`.
2. If it is `e5-mistral-7b-instruct`, use last-token pooling and instruction prompts.
3. If it is `multilingual-e5-large-instruct`, use average pooling and instruction prompts.
4. For all other known E5 models, use average pooling and `query_or_passage` prefixes.
5. For non-retrieval MTEB classification tasks, expect L2 normalization to be disabled by the source evaluator.

## SimLM MS MARCO Dense Retrieval Inference

The released biencoder flow is: encode the corpus once, then search each query split.

```bash
export DATA_DIR=./data/msmarco_bm25_official
export OUTPUT_DIR=./outputs/simlm-msmarco

PYTHONPATH=src python -u src/inference/encode_main.py \
  --model_name_or_path intfloat/simlm-base-msmarco-finetuned \
  --do_encode --fp16 \
  --encode_in_path "$DATA_DIR/passages.jsonl.gz" \
  --encode_save_dir "$OUTPUT_DIR" \
  --encode_batch_size 512 \
  --p_max_len 144 \
  --add_pooler False \
  --output_dir "$OUTPUT_DIR" \
  --data_dir "$DATA_DIR" \
  --report_to none

PYTHONPATH=src python -u src/inference/search_main.py \
  --model_name_or_path intfloat/simlm-base-msmarco-finetuned \
  --do_search \
  --search_split dev \
  --search_batch_size 128 \
  --search_topk 1000 \
  --search_out_dir "$OUTPUT_DIR" \
  --encode_save_dir "$OUTPUT_DIR" \
  --q_max_len 32 \
  --add_pooler False \
  --output_dir ./tmp-search \
  --data_dir "$DATA_DIR" \
  --report_to none
```

For `train` search, the upstream shell uses top-200 by default because train predictions are intended as mined hard negatives. For dev/TREC/test, top-1000 is the default.

## SimLM Cross-Encoder Reranking

Use reranking when you already have a candidate file, typically `<split>.msmarco.txt` from biencoder search or BM25. A reranker does not produce reusable corpus embeddings.

```bash
export DATA_DIR=./data/msmarco_reranker
export OUTPUT_DIR=./outputs/simlm-rerank

PYTHONPATH=src python -u src/inference/rerank_main.py \
  --model_name_or_path intfloat/simlm-msmarco-reranker \
  --do_rerank --fp16 \
  --rerank_in_path "$DATA_DIR/dev.msmarco.txt" \
  --rerank_out_path "$OUTPUT_DIR/rerank.dev.msmarco.txt" \
  --rerank_batch_size 256 \
  --rerank_max_length 192 \
  --rerank_split dev \
  --rerank_depth 200 \
  --output_dir ./tmp-rerank \
  --data_dir "$DATA_DIR" \
  --report_to none
```

The reranker scores `(query, passage)` pairs with a sequence-classification head, sorts by cross-encoder score, preserves unre-ranked tail candidates after `rerank_depth`, and computes metrics only if qrels exist.

## SimLM Hard-Negative Mining Plan

1. Start from a biencoder checkpoint and a corpus with `passages.jsonl.gz`.
2. Encode the corpus into `shard_<gpu>_<shard>` files under an output directory.
3. Search the `train` split with top-200, producing `train.msmarco.txt`.
4. Convert the mined candidate list into training JSONL where each query has positives and mined `negatives.doc_id` values. The repository scripts assume preprocessed downloads already contain this JSONL; they do not include a generic converter for arbitrary corpora.
5. If using KD, run teacher-score generation with a cross-encoder reranker so positives/negatives receive `score` arrays, then train with `--do_kd_biencoder`.

## SimLM Teacher-Score Generation

Teacher scoring reads `<split>.jsonl` from `--data_dir`, scores positives plus the first `--kd_gen_score_n_neg` negatives, and writes `kd_<split>.jsonl` next to the source file.

```bash
PYTHONPATH=src python -u src/inference/gen_teacher_scores.py \
  --model_name_or_path intfloat/simlm-msmarco-reranker \
  --do_kd_gen_score --fp16 \
  --data_dir ./data/msmarco_distillation \
  --kd_gen_score_split train \
  --kd_gen_score_batch_size 256 \
  --kd_gen_score_n_neg 1000 \
  --rerank_max_length 192 \
  --output_dir ./tmp-teacher \
  --report_to none
```

Check that `<split>.jsonl`, `<split>_queries.tsv`, and `passages.jsonl.gz` are all present before launching.

## SimLM Training Workflows

Training scripts are reference-only because they are GPU-, download-, and time-heavy. The commands below show the core arguments to preserve when adapting.

### MS MARCO biencoder with BM25 hard negatives

- Base model: `intfloat/simlm-base-msmarco`.
- Data root: `msmarco_bm25_official` with `train.jsonl` and `dev.jsonl`.
- Important flags: `--do_train`, `--fp16`, `--q_max_len 32`, `--p_max_len 144`, `--train_n_passages 16`, `--t 0.02`, `--use_scaled_loss True`, `--share_encoder True`, `--learning_rate 2e-5`, `--num_train_epochs 3`.
- Launcher: DeepSpeed with `ds_config.json`, ZeRO stage 2, automatic optimizer/scheduler batch settings.

### MS MARCO KD biencoder

- Base model: `intfloat/simlm-base-msmarco`.
- Data root: `msmarco_distillation` with `kd_train.jsonl` and `kd_dev.jsonl`.
- Important flags: `--do_kd_biencoder`, `--kd_mask_hn False`, `--kd_cont_loss_weight 0.2`, `--train_n_passages 24`, `--learning_rate 3e-5`, `--num_train_epochs 6`.
- Source code asserts that scaled loss with KD requires `--kd_mask_hn False`.

### MS MARCO cross-encoder reranker

- Base model: `google/electra-base-discriminator`.
- Data root: `msmarco_reranker` with `train.jsonl` and `dev.jsonl`.
- Important flags: `--rerank_max_length 192`, `--rerank_use_rdrop True`, `--train_n_passages 64`, `--rerank_forward_factor 4`, `--learning_rate 3e-5`, `--metric_for_best_model acc`.
- The README notes that learning rates above `1e-5` are empirically unstable for Electra-large variants.

### Replaced language modeling pretraining

- Base encoder: `bert-base-uncased`; generator: `google/electra-base-generator`.
- Data root: usually a target passage corpus such as MS MARCO BM25 official data.
- Important flags: `--do_train --do_eval`, `--train_file passages.jsonl.gz`, `--rlm_max_length 144`, `--rlm_encoder_mask_prob 0.3`, `--rlm_decoder_mask_prob 0.5`, `--rlm_generator_mlm_weight 0.2`, `--all_use_mask_token True`, `--max_steps 80000`, `--learning_rate 3e-4`.

## DPR/NQ Variants

DPR scripts reuse the same SimLM code with `--task_type qa`, `intfloat/simlm-base-wiki100w`, and longer passage/pair lengths.

- Encode Wikipedia: `--encode_in_path "$DATA_DIR/passages.jsonl.gz"`, `--p_max_len 192`, `--l2_normalize True`.
- Search NQ: `--search_split nq_dev`, `--search_topk 100`, then format/evaluate with DPR output JSON.
- Train NQ biencoder: `--train_file "$DATA_DIR/nq_train.jsonl,$DATA_DIR/nq_hard_train.jsonl"`, `--validation_file "$DATA_DIR/nq_dev.jsonl"`, `--use_first_positive True`, `--loss_scale 1`, `--max_steps 20000`.
- Train NQ reranker: pair length 224, `--train_n_passages 32`, `--rerank_forward_factor 2`, `--max_steps 20000`.
- Generate NQ teacher scores: `--task_type qa`, `--kd_gen_score_split nq_dev`, `--rerank_max_length 224`, `--kd_gen_score_n_neg 1000`.

## Preflight Checklist Before Native Runs

- Confirm the user authorized network downloads if using Hugging Face models, MTEB/BEIR datasets, or SimLM preprocessed data.
- Confirm CUDA GPUs are visible; most SimLM paths exit early or assert if CUDA is unavailable.
- Confirm `DATA_DIR` has the exact files for the chosen phase; search additionally requires existing embedding shards.
- Confirm output directories have enough storage for corpus embeddings and top-k prediction files.
- Reduce batch sizes before retrying OOM; for E5 this may require editing copied commands because upstream scripts hard-code batch size from GPU count.
- Use `--dry_run True` for SimLM parser-supported debug runs, but still expect CUDA assertions and model/data reads.
