# E5 and SimLM Troubleshooting

## E5 Prefix and Prompt Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Retrieval quality is far below expected for standard E5 models | Queries/passages were embedded without `query: ` and `passage: ` prefixes | Add `query: ` to user queries and `passage: ` to corpus/title+text inputs, or use the bundled command builder to confirm prefix mode. |
| Instruct model answers look generic or weak | Missing `Instruct: <task>\nQuery: ` prompt | Use task-specific instructions for `multilingual-e5-large-instruct` and `e5-mistral-7b-instruct`; do not add `passage:` to corpus documents for the upstream BEIR instruct path. |
| Quora or duplicate-question retrieval behaves oddly | Symmetric retrieval needs query formatting for documents | Use the upstream `--doc-as-query` behavior for Quora-style symmetric tasks. |
| Classification MTEB scores differ from expected | Normalization was applied to classification embeddings | The upstream non-retrieval MTEB evaluator disables L2 normalization for `Classification` tasks. |

## E5 Model/Benchmark Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Mistral E5 fails to load | `transformers` is older than the Mistral-supported release | Install or select an environment with `transformers>=4.34` for `intfloat/e5-mistral-7b-instruct`. |
| `--multilingual` gives unexpected task mix | Multilingual flag removes the English-only task filter | Use `--multilingual` for multilingual E5 models and multilingual benchmark intent; omit it for English-only comparisons. |
| Evaluation appears stuck for hours | BEIR/MTEB corpus download or corpus embedding is long-running | Confirm network/storage/GPU authorization; start with `--dry-run` or a small task subset when possible. |
| CUDA OOM during E5 encoding | Batch size is too high, especially with large/mistral models | Reduce batch size in a copied evaluator, limit visible GPUs if DataParallel causes imbalance, use a smaller model, or move to larger-memory GPUs. |
| Benchmark import errors | E5 dependencies are not installed together | Use an environment with `beir`, `mteb==1.0.2`, compatible `torch`, and compatible `transformers`. |

## SimLM Data Layout Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `assert os.path.exists(self.data_dir)` | `--data_dir` missing or wrong | Point `--data_dir` at the prepared data root for the selected phase. |
| Search fails before scoring | No `shard_<gpu>_<shard>` passage embeddings in `--encode_save_dir` | Run corpus encoding first with the same output directory, or point to the directory containing existing shards. |
| Rerank asserts missing input | `--rerank_in_path` does not exist | Provide a candidate `.msmarco.txt` file from biencoder search, BM25, or another retriever. |
| Teacher scoring fails for split | Missing `<split>.jsonl` in `--data_dir` | Generate or place the training JSONL before running `gen_teacher_scores.py`; also check `<split>_queries.tsv` and `passages.jsonl.gz`. |
| Metrics are skipped | `<split>_qrels.txt` is absent | This is expected for some test splits; predictions still write, but metrics require qrels. |
| Passage IDs do not match text | `doc_id` values do not correspond to row indices in `passages.jsonl.gz` | Rebuild training/candidate files so `doc_id` is the zero-based row index expected by SimLM loaders. |

## SimLM Reranker vs Biencoder Confusion

| Need | Use | Output |
| --- | --- | --- |
| Build reusable passage vectors | Biencoder `encode_main.py` | `shard_<gpu>_<shard>` tensors. |
| Retrieve top-k from a corpus | Biencoder `search_main.py` after encoding | `<split>.msmarco.txt` plus metrics when qrels exist. |
| Re-score candidate query-document pairs | Cross-encoder `rerank_main.py` | `rerank.<split>.msmarco.txt` plus optional rerank metrics. |
| Create KD scores for positives/negatives | Cross-encoder `gen_teacher_scores.py` | `kd_<split>.jsonl` with positive/negative `score` arrays. |
| Train a retriever from positives/negatives | Biencoder `train_biencoder.py` | Dense retriever checkpoint. |
| Train a reranker from candidates | Cross-encoder `train_cross_encoder.py` | Sequence-classification reranker checkpoint. |

A reranker is usually more accurate but much slower because it runs a transformer over every query-passage pair. A biencoder is required for large-corpus retrieval because it encodes passages once and uses dot products for search.

## SimLM Hard Negatives and KD

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training examples have only positives | `train_n_passages` or negative list is invalid | Ensure each example has positives and enough negatives for `train_n_passages - positives_used`. |
| KD training assertion mentions scaled loss and masked hard negatives | `--use_scaled_loss True` with `--kd_mask_hn True` | Set `--kd_mask_hn False` when using scaled loss, matching the KD script. |
| KD labels missing | Positives/negatives lack `score` arrays | Run teacher-score generation or provide scored KD JSONL before `--do_kd_biencoder`. |
| Mined negatives are too easy or duplicate positives | Candidate conversion did not filter qrels/positives | When converting search output to JSONL, filter known positives and keep high-ranking non-relevant docs as negatives. |

## GPU, DeepSpeed, and Environment Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Only support running on GPUs` | SimLM argument validation requires CUDA | Do not run native SimLM training/inference on CPU; switch to planning mode or provision CUDA GPUs. |
| `nvidia-smi` not found in shell scripts | GPU utilities are missing from PATH or no NVIDIA driver | Avoid native scripts until the GPU environment is fixed; direct Python entry points still require CUDA. |
| DeepSpeed launch/config errors | Pinned `deepspeed==0.6.0` or ZeRO config mismatch with installed stack | Use the pinned environment when reproducing; otherwise adapt launcher carefully and keep optimizer/scheduler `auto` settings aligned with Hugging Face TrainingArguments. |
| OOM in SimLM training | `train_n_passages`, pair length, or per-device batch is too high | Lower `per_device_train_batch_size`, `train_n_passages`, `rerank_depth`, `encode_batch_size`, or max lengths; increase gradient accumulation to preserve effective batch size. |
| Electra-large reranker becomes unstable | Learning rate too high | Follow the source note that Electra-large variants may need learning rates no greater than `1e-5`. |
| Package conflicts | SimLM pins old Transformers/Datasets/DeepSpeed while E5 uses different benchmark packages | Use separate environments for E5 and SimLM when reproducing native runs. |

## Download and Storage Safety

- `download_msmarco_data.sh` downloads multiple archives from a Hugging Face dataset and unzips them; ask for network and disk authorization first.
- E5 evaluation can download Hugging Face model weights and benchmark corpora automatically through Transformers/MTEB/BEIR.
- SimLM passage embeddings for large corpora are tensor shard files and can be large; verify free space before encoding.
- Do not run long training scripts in shared or unknown environments without explicit user approval for GPUs, wall time, and output location.
