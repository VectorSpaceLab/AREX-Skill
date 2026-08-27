# RAG-Retrieval Troubleshooting

## Install And Import

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: rag_retrieval` | Package is not installed in the active environment. | Install the package for inference, or use bundled training snapshots plus training dependencies for training workflows. |
| `Reranker` import works but training modules do not | The installed distribution only declares the inference package surface. | Route to the relevant training sub-skill and use its bundled `training_bundle/` scripts or an explicit current checkout. |
| `pip check` reports torch/setuptools or transformer conflicts | Backend dependencies were installed from incompatible indexes or Python versions. | Use a Python version supported by torch/transformers, avoid Python 3.13 for older ML stacks, and reinstall with a consistent wheel/index strategy. |
| No console command is found | The package declares no console scripts. | Use Python APIs and bundled training command builders instead of expecting a CLI. |

## Model Loading And Downloads

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Model load starts a large network download | `model_name` is a Hugging Face model id and no local cache/path is available. | Ask whether downloads are allowed; otherwise use a local model path. |
| CPU/GPU mismatch or slow inference | Device auto-selection picked an undesired backend or dtype. | Pass `device` and `dtype` explicitly, such as `device="cpu"` for no-GPU checks or `dtype="fp16"` only on compatible GPUs. |
| `trust_remote_code` concerns for LLM rankers | LLM ranker tokenizer/model loading enables remote code. | Confirm the model source and use pinned/local checkpoints when security matters. |
| `cutoff_layers` has no effect | The LLM ranker only applies layerwise cutoff behavior to model names containing `layerwise`. | Use it for layerwise MiniCPM-style rankers; omit it for ordinary LLM rankers. |

## Inference Routing

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Reranker(..., model_type="colbert")` returns `None` or fails | Current installed registry lacks a working `ColBERTRanker`. | Use `sub-skills/colbert-training/SKILL.md` for bundled ColBERT training/scoring guidance or implement/register a ranker before using package inference. |
| Unknown model defaults to cross-encoder | Auto-mapping did not recognize the model name. | Pass `model_type="cross-encoder"` or `model_type="llm"` explicitly based on architecture. |
| Empty `rerank` output is a dict, not `RankedResults` | Empty query or docs triggers legacy return behavior. | Validate inputs before reranking or handle both dict and `RankedResults` in downstream code. |
| `AssertionError: Your query is too long` | Cross-encoder long-doc chunking leaves too few document tokens. | Shorten the query or increase `max_length` if the model supports it. |

## Training Config And Data

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Training crashes before model load due YAML/data fields | Config and JSONL schema do not match the selected workflow. | Run the owning validator script before launch. |
| Embedding pair-score data is rejected | Raw rows should have `scores`, but code expands them into singular `score` internally. | Validate score length equals `pos` length and keep raw input as `scores`. |
| Distillation memmap shape mismatch | Text JSONL row count times `teacher_embedding_dim` does not match float32 array size. | Recompute row count/dimensions or merge teacher arrays with explicit dimensions. |
| Reranker grouped training skips many samples | Groups have fewer than `train_group_size` hits or all labels are equal. | Reduce `train_group_size`, collect more candidates, fix labels, or use pointwise training. |
| ColBERT training gives dimension/model mismatch | `colbert_dim` does not match the intended backbone projection convention. | Use `1024` for BGE-M3-style ColBERT unless intentionally training a new projection size; use compatible FSDP wrapping. |

## Distributed And Hardware Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Accelerate process count differs from visible GPUs | `num_processes` in config and `CUDA_VISIBLE_DEVICES` do not match. | Update one or the other before launch. |
| FSDP wrapping errors | Transformer layer class in config does not match the backbone family. | Use `BertLayer` for BERT-style models and `XLMRobertaLayer` for XLM-R/BGE-M3-style models. |
| DeepSpeed ZeRO-3 save failure in reranker LLM training | Upstream docs call out save-time incompatibility for that flow. | Use ZeRO-1 or ZeRO-2 unless the current source has fixed the save path. |
| Out-of-memory during training | Batch size, sequence length, group size, or gradient accumulation is too large. | Lower batch/group/length values, enable gradient checkpointing when supported, use bf16/fp16 on compatible hardware, or choose a smaller model. |

## Research And Benchmark Scripts

MyopicTrap and synthetic data examples are useful evidence but are not safe default smoke checks. They may require external datasets, API keys, FAISS/BM25/FlagEmbedding/FlashRAG, model downloads, or long benchmark runs. Treat them as opt-in research workflows and record skipped checks explicitly during verification.
