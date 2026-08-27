# CoRAG workflow reference

CoRAG is the Chain-of-Retrieval Augmented Generation workflow in LMOps. It combines a dense E5 retriever over KILT-style Wikipedia passages with an OpenAI-compatible vLLM server hosting a CoRAG-tuned Llama model. Use it for multihop QA scenarios where the model repeatedly creates subqueries, retrieves supporting passages, answers intermediate subquestions, and then produces a final answer.

This reference is self-contained. For runnable planning, call `scripts/corag_service_plan.py`; do not run long-lived services or downloads until the generated checklist is reviewed.

## Public resources and roles

| Resource | Public identifier | Role |
| --- | --- | --- |
| Multihop QA data | `corag/multihopqa` | Evaluation examples for `2wikimultihopqa`, `bamboogle`, `hotpotqa`, and `musique`. |
| Retrieval corpus | `corag/kilt-corpus` | KILT-version Wikipedia passages loaded by the retriever and final-answer formatter. |
| Precomputed E5 embeddings | `corag/kilt-corpus-embeddings` | Forty `e5-large-shard-*.pt` shards used by the E5 search server. |
| Retriever encoder | `intfloat/e5-large-v2` | Query encoder for the search server; uses E5 query/passsage prefixes. |
| CoRAG generator | `corag/CoRAG-Llama3.1-8B-MultihopQA` | vLLM-served model fine-tuned for multihop QA. |

## Service order

CoRAG evaluation depends on two running services and staged embeddings. Keep this order:

1. **Stage embeddings**: ensure an embedding directory contains all forty shard files named like `e5-large-shard-0.pt` through `e5-large-shard-39.pt`.
2. **Start E5 search server**: runs an HTTP service on port `8090` by default and writes `e5_server.log`. It loads the embeddings, the E5 model, and the corpus. Environment knobs used by the service are `INDEX_DIR`, `E5_MODEL_NAME_OR_PATH`, and `TOP_K`.
3. **Start vLLM server**: runs an OpenAI-compatible service on port `8000` by default and writes `vllm_server.log`. The CoRAG client discovers the served model id through the `/v1/models` endpoint and uses API key `token-123` by default.
4. **Run inference/evaluation**: launches a single-process torchrun job per task. The default public workflow evaluates `2wikimultihopqa`, `bamboogle`, `hotpotqa`, and `musique` sequentially.

Use the bundled planner to produce a checklist for this order:

```bash
python scripts/corag_service_plan.py --tasks all --max-path-length 6 --gpu-count 8 --format markdown
```

The planner prints command concepts only. It does not check ports, start services, download files, or run evaluation.

## Evaluation tasks and splits

| Task config | Default split | Notes |
| --- | --- | --- |
| `2wikimultihopqa` | `validation` | Multihop QA evaluation. |
| `bamboogle` | `test` | Small dataset; reported scores can vary more noticeably. |
| `hotpotqa` | `validation` | Multihop QA evaluation. |
| `musique` | `validation` | Multihop QA evaluation often used in example metrics. |

For a new multihop QA dataset, the implementation expects each example to provide at least:

- `query`: question text.
- `query_id`: stable identifier.
- `answers`: list of acceptable answer strings.
- `context_doc_ids`: ranked corpus document ids for final-answer context.
- `context_doc_scores`: retrieval scores aligned with `context_doc_ids`.

During inference, the workflow adds `task_desc`, `prediction`, `subqueries`, `subanswers`, and path document ids/titles when corpus titles are available.

## Important inference settings

| Setting | Default or common value | Meaning and operating guidance |
| --- | --- | --- |
| `max_len` | `3072` | Maximum tokenized message length before truncation. Long messages may be truncated from the middle. |
| `num_contexts` | `20` | Number of retrieved context passages used for final answer generation. |
| `context_placement` | `backward` | Passage placement strategy: `forward`, `backward`, or `random`. Retrieved contexts are score-sorted before placement. |
| `num_threads` | `32` | Thread pool size for parallel example generation and retriever/model calls. Too high can overload services. |
| `max_path_length` | config default `3`, public eval recipe `6` | Maximum number of CoRAG subquery/subanswer retrieval hops. Larger values increase calls and token usage. |
| `decode_strategy` | `greedy` | Available strategies are `greedy`, `tree_search`, and `best_of_n`. `tree_search` and `best_of_n` are more expensive. |
| `sample_temperature` | `0.7` | Sampling temperature for non-greedy path search. Greedy uses zero temperature for subquery path sampling. |
| `best_n` | `4` | Number of sampled paths for `best_of_n`. |
| `eval_metrics` | `em_and_f1` | Computes normalized exact match and F1. `kilt` is recognized as requiring separate handling. |
| `dry_run` | `False` | When enabled, limits evaluation to a small subset for debugging. |

If `max_path_length` is below `1`, the workflow falls back to greedy behavior without a retrieval chain.

## Output and metrics

A run writes predictions and metric JSON files under the selected output directory. Expected file names follow this shape:

- `preds_{decode_strategy}_{eval_task}_{eval_split}.jsonl`
- `metrics_{eval_task}_{eval_split}_{decode_strategy}.json`

Default metric JSON fields include:

- `em`: normalized exact-match score, rounded to three decimals.
- `f1`: normalized token-level F1 score, rounded to three decimals.
- `num_samples`, `eval_task`, `eval_split`, `max_path_length`, `decode_strategy`.
- `token_consumed`: total vLLM API token usage counted by the client.
- `average_token_consumed_per_sample`.

Some public examples include an `accuracy` field. In the inspected implementation, the default `em_and_f1` metric path guarantees EM/F1 and bookkeeping fields; treat extra fields as version- or metric-specific rather than universal.

## Hardware and runtime boundary

The public CoRAG recipe was tested on a machine with eight NVIDIA A100 40GB GPUs. The vLLM launch concept sets tensor parallelism to the detected GPU count, uses an 8192-token model length, enables chunked prefill, and uses `gpu_memory_utilization` around `0.5`. The E5 searcher also assumes CUDA devices because it moves model and embedding shards onto GPUs.

Creation-time checks for this skill did not run CoRAG end-to-end. Any future run should first use `scripts/corag_service_plan.py`, verify the model/data license and cache situation, inspect available GPUs, and confirm that ports `8090` and `8000` are free or intentionally occupied by the expected services.
