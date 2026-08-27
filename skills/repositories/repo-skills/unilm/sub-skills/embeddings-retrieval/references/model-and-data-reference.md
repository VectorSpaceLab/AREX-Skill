# E5 and SimLM Model/Data Reference

This reference distills the UniLM E5 and SimLM retrieval code into self-contained model, prefix, dependency, and file-layout guidance.

## E5 Model Families

| Family | Example model | Pooling | Prefix mode | Use when |
| --- | --- | --- | --- | --- |
| English v2 | `intfloat/e5-small-v2`, `intfloat/e5-base-v2`, `intfloat/e5-large-v2` | average | `query_or_passage` | Default English BEIR/MTEB embedding evaluation. |
| English v1 | `intfloat/e5-small`, `intfloat/e5-base`, `intfloat/e5-large` | average | `query_or_passage` | Reproducing older E5 checkpoints. |
| English unsupervised | `intfloat/e5-small-unsupervised`, `intfloat/e5-base-unsupervised`, `intfloat/e5-large-unsupervised` | average | `query_or_passage` | Comparing weakly supervised vs unlabeled pretraining. |
| Multilingual | `intfloat/multilingual-e5-small`, `intfloat/multilingual-e5-base`, `intfloat/multilingual-e5-large` | average | `query_or_passage` | Multilingual or cross-lingual embeddings without instruct prompts. |
| Instruct multilingual | `intfloat/multilingual-e5-large-instruct` | average | `instruction` | Retrieval or MTEB tasks where query instructions should be task-specific. |
| LLM instruct | `intfloat/e5-mistral-7b-instruct` | last-token | `instruction` | Highest-capacity instruct embedding, but heavier and requires newer Transformers. |

E5 requirements are `torch>=1.7`, `transformers>=4.15.0`, `tqdm`, `beir`, and `mteb==1.0.2`; `e5-mistral-7b-instruct` requires `transformers>=4.34` even though the base requirement is lower.

## E5 Prefix and Pooling Rules

- For `query_or_passage` models, retrieval queries must be prefixed as `query: ...` and corpus texts as `passage: ...`.
- For BEIR Quora-style symmetric retrieval, the upstream BEIR script sets `--doc-as-query` so passages also use the query path.
- For non-retrieval MTEB with `query_or_passage` models, the upstream script uses `query: ` as the prompt for every sentence pair/task input.
- For `instruction` models, queries use `Instruct: <task definition>\nQuery: `; corpus texts are not given a `passage:` prefix in BEIR retrieval.
- Pooling is model-dependent: most E5 checkpoints use average pooling, while `e5-mistral-7b-instruct` uses last-token pooling. All upstream E5 evaluation embeddings are L2-normalized except classification tasks in non-retrieval MTEB, where normalization is disabled.
- The E5 tokenizer truncates/pads batches to max length 512 and uses pad-to-multiple-of-8 batching.

## E5 Evaluation Tasks

- BEIR evaluation runs MTEB retrieval tasks in English and skips `MSMARCOv2`; standard eval split is `test`, except `MSMARCO` uses `dev`.
- Non-retrieval MTEB default task types are `STS`, `Summarization`, `PairClassification`, `Classification`, `Reranking`, `Clustering`, and `BitextMining`.
- Use `--multilingual` only for non-retrieval MTEB multilingual models/tasks; it removes the English-only task-language filter.
- The upstream E5 scripts support `--dry-run`; BEIR dry-run keeps only `SciFact` and `FiQA2018`, while non-retrieval dry-run keeps `Banking77Classification`, `ImdbClassification`, and `STS12`.

## SimLM Models and Roles

| Model | Role | Typical workflow |
| --- | --- | --- |
| `intfloat/simlm-base-msmarco` | MS MARCO SimLM pre-trained base | Fine-tune a biencoder or KD biencoder. |
| `intfloat/simlm-base-msmarco-finetuned` | Released dense retriever | Encode MS MARCO passages, search dev/TREC/test/train queries. |
| `intfloat/simlm-msmarco-reranker` | Released cross-encoder reranker | Rerank top-k MS MARCO candidate files. |
| `intfloat/simlm-base-wiki100w` | DPR/NQ SimLM base | Train/evaluate DPR-style QA retrieval. |
| `google/electra-base-discriminator` | Reranker base | Train a cross-encoder reranker. |
| `bert-base-uncased` + `google/electra-base-generator` | RLM pretraining stack | Pre-train SimLM with replaced language modeling. |

SimLM requirements are older and pinned: `transformers==4.15.0`, `datasets==2.0.0`, `deepspeed==0.6.0`, `pytrec_eval`, `ir_datasets==0.5.0`, `pyserini==0.15.0`, `torch>=1.7`, `tqdm`, and `numpy`.

## SimLM Data Layout

### Shared corpus and query files

| File | Format | Required by | Notes |
| --- | --- | --- | --- |
| `passages.jsonl.gz` or `passages.jsonl` | JSON lines with at least `contents`; optional `title`; document index position is used as `doc_id` | encoding, reranking, teacher scoring, training | Reranker prepends `title + ': '` when `title` exists. |
| `<split>_queries.tsv` | IR: `query_id<TAB>query`; QA: `question<TAB>answers` | search, rerank, DPR eval, teacher scoring | `--task_type qa` normalizes question text and uses it as the key. |
| `<split>_qrels.txt` | `qid<TAB>unused<TAB>pid<TAB>score` | metrics in search/rerank | Optional for test splits; if absent, predictions are still written and metrics are skipped. |
| `<split>.msmarco.txt` | `qid<TAB>pid<TAB>rank` or `qid<TAB>pid<TAB>rank<TAB>score` | reranking input, DPR formatting | Three-column files get score `1/rank`; four-column files preserve the score. |

### Training JSONL examples

- Biencoder and reranker train/eval files are JSONL files with `query_id`, `query`, `positives`, and `negatives` groups.
- `positives.doc_id` and `negatives.doc_id` refer to row indices in `passages.jsonl.gz`; KD variants also carry parallel `score` arrays under positives/negatives.
- `train_n_passages` is total passages per query, including one or more positives plus negatives; the code asserts more than one passage for reranker training.
- For MS MARCO BM25 hard-negative training, expected files include `train.jsonl`, `dev.jsonl`, `passages.jsonl.gz`, split query TSVs, and optional qrels.
- For KD biencoder training, expected files include `kd_train.jsonl`, `kd_dev.jsonl`, `passages.jsonl.gz`, split query TSVs, and optional qrels.
- For reranker training, expected files include `train.jsonl`, `dev.jsonl`, `passages.jsonl.gz`, split query TSVs, and candidate prediction files for evaluation/reranking.

### Encoded output and prediction files

- `encode_main.py` writes sharded passage embeddings named `shard_<gpu_idx>_<shard_idx>` under `--encode_save_dir`; search fails if no shard files exist.
- `search_main.py` writes worker top-k files, merges them into `<split>.msmarco.txt`, and optionally writes `metrics_<split>.json` when qrels exist.
- `rerank_main.py` reads a candidate `.txt`, scores query-document pairs with a cross-encoder, writes shard files, merges them into `rerank.<split>.msmarco.txt`, and optionally writes `metrics_rerank_<split>.json`.
- `gen_teacher_scores.py` reads `<split>.jsonl`, scores positives plus the first `--kd_gen_score_n_neg` negatives with a reranker, writes `kd_<split>.jsonl`, and also produces a readable JSON preview.

## Default Lengths and Batch Sizes

| Workflow | Query length | Passage/input length | Batch-size defaults |
| --- | --- | --- | --- |
| MS MARCO biencoder train | 32 | 144 | train 16/GPU, eval 32/GPU, `train_n_passages=16` |
| MS MARCO KD biencoder | 32 | 144 | train 16/GPU, eval 16/GPU, `train_n_passages=24` |
| MS MARCO reranker train | n/a | 192 pair length | train 8/GPU, eval 16/GPU, `train_n_passages=64`, `rerank_forward_factor=4` |
| MS MARCO encode/search | 32 | 144 | encode 512, search 128 |
| MS MARCO rerank inference | n/a | 192 pair length | rerank 256, top rerank depth 200 |
| DPR/NQ biencoder train | 32 | 192 | train 8/GPU, eval 32/GPU, `train_n_passages=16` |
| DPR/NQ reranker train | n/a | 224 pair length | train 4/GPU, eval 16/GPU, `train_n_passages=32`, `rerank_forward_factor=2` |

## Dependency and Hardware Implications

- SimLM `Arguments.__post_init__` asserts `torch.cuda.is_available()` and `os.path.exists(data_dir)` for core commands; CPU-only environments are unsuitable for native SimLM runs.
- Training scripts count GPUs with `nvidia-smi --list-gpus` and launch DeepSpeed by default. If DeepSpeed is not viable, the README documents switching to `python -m torch.distributed.launch` after editing the shell command.
- MS MARCO biencoder/KD training expects about 4 V100 32GB GPUs; MS MARCO reranker training expects about 8 V100 32GB GPUs; RLM pretraining expects about 8 V100-class GPUs.
- E5 BEIR evaluation uses all visible GPUs through `torch.cuda.device_count()` and batch size `64 * gpu_count`; reduce visible GPUs or batch size in copied commands if memory is limited.
