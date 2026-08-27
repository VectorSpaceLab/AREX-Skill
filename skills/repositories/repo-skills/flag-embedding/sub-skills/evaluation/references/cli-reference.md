# CLI Reference

This reference covers the evaluation module commands and argument surfaces used by FlagEmbedding evaluation. The local custom path is the safe default for user-owned data. Official benchmarks can download datasets, load external benchmark packages, and require substantial model inference.

## Module Commands

Use these module entry points:

- `python -m FlagEmbedding.evaluation.custom`
- `python -m FlagEmbedding.evaluation.mteb`
- `python -m FlagEmbedding.evaluation.beir`
- `python -m FlagEmbedding.evaluation.msmarco`
- `python -m FlagEmbedding.evaluation.miracl`
- `python -m FlagEmbedding.evaluation.mldr`
- `python -m FlagEmbedding.evaluation.mkqa`
- `python -m FlagEmbedding.evaluation.air_bench`
- `python -m FlagEmbedding.evaluation.bright`

Run `--help` on the exact module in the target environment before executing long jobs. `custom --help` was verified after installing the focused evaluation dependencies `faiss-cpu` and `pytrec_eval`.

## Shared Evaluation Arguments

These flags are shared by the base evaluation runner used by `custom`, `beir`, `msmarco`, `miracl`, `mldr`, `mkqa`, and `bright`. MTEB uses several of them plus its own task selectors. AIR-Bench uses an external eval-argument class; see its section.

- `--eval_name`: label stored in result metadata and output summaries.
- `--dataset_dir`: local dataset directory or directory where a benchmark loader saves downloaded data.
- `--force_redownload`: force remote loaders to redownload data.
- `--dataset_names`: benchmark dataset names or languages. Do not use this with `custom`; run one custom command per local dataset directory.
- `--splits`: one or more split names such as `test`, `dev`, `dl19`, or benchmark-specific split names.
- `--corpus_embd_save_dir`: directory for reusable `doc.npy` corpus embeddings; omit to avoid saving embeddings.
- `--output_dir`: directory for raw search results and per-run `EVAL/eval_results.json` files.
- `--search_top_k`: initial dense retrieval cutoff.
- `--rerank_top_k`: number of retrieved documents passed to the reranker.
- `--cache_path`: dataset cache directory.
- `--token`: Hugging Face token for private or gated resources; defaults from `HF_TOKEN` when unset.
- `--overwrite`: recompute existing search/eval results.
- `--ignore_identical_ids`: drop hits where query id equals document id.
- `--k_values`: cutoffs used for metric computation.
- `--eval_output_method`: aggregate output format, `json` or `markdown`.
- `--eval_output_path`: aggregate evaluation output file.
- `--eval_metrics`: metrics to display in the aggregate file, such as `ndcg_at_10`, `recall_at_100`, `mrr_at_10`, `map_at_10`, `precision_at_10`, or `qa_recall_at_20` for MKQA.

Boolean flags are parsed by the Hugging Face argument parser. For flags whose default is true, such as `normalize_embeddings` and `use_fp16`, the installed help exposes `--no_normalize_embeddings` and `--no_use_fp16` aliases.

## Shared Model Arguments

These flags configure the embedder and optional reranker for base evaluation modules:

- `--embedder_name_or_path`: required model id or local checkpoint path for the embedder.
- `--embedder_model_class`: explicit embedder class for custom or unmapped checkpoints. Supported values include `encoder-only-base`, `encoder-only-m3`, `decoder-only-base`, `decoder-only-icl`, and `decoder-only-pseudo_moe`.
- `--normalize_embeddings`: normalize dense embeddings before search; enabled by default.
- `--pooling_method`: embedder pooling strategy, commonly needed for decoder-only checkpoints.
- `--use_fp16`: use fp16 inference when supported; disable on CPU-only or unsupported hardware.
- `--devices`: one or more devices, such as `cpu`, `cuda:0`, or multiple CUDA devices.
- `--query_instruction_for_retrieval`: instruction text prepended/formatted for retrieval queries.
- `--query_instruction_format_for_retrieval`: format string for retrieval instructions; the code converts literal `\n` to newlines.
- `--examples_for_task`: examples consumed by ICL-style embedders.
- `--examples_instruction_format`: format string for examples; literal `\n` is converted to newlines.
- `--trust_remote_code`: allow remote model code only after user approval.
- `--reranker_name_or_path`: optional reranker model id or local checkpoint path.
- `--reranker_model_class`: explicit reranker class for custom or unmapped checkpoints. Supported values include `encoder-only-base`, `decoder-only-base`, `decoder-only-layerwise`, and `decoder-only-lightweight`.
- `--reranker_peft_path`: optional PEFT adapter path for the reranker.
- `--use_bf16`: use bf16 inference when supported.
- `--query_instruction_for_rerank` and `--query_instruction_format_for_rerank`: reranker query instruction and format.
- `--passage_instruction_for_rerank` and `--passage_instruction_format_for_rerank`: reranker passage instruction and format.
- `--cache_dir`: model cache directory for most modules.
- `--domain_for_pseudo_moe`: domain selector for `decoder-only-pseudo_moe`, such as `general`, `coding`, or `reasoning`.
- `--embedder_batch_size`, `--reranker_batch_size`: inference batch sizes.
- `--embedder_query_max_length`, `--embedder_passage_max_length`: embedder sequence length limits.
- `--reranker_query_max_length`, `--reranker_max_length`: reranker sequence length limits.
- `--truncate_dim`: truncate embedding dimensions for Matryoshka-style models.
- `--normalize`: normalize reranker scores.
- `--prompt`: reranker prompt text.
- `--cutoff_layers`: output layers for layerwise or lightweight rerankers.
- `--compress_ratio`: compression ratio for lightweight rerankers.
- `--compress_layers`: compression layers for lightweight rerankers.

For low-level class behavior, output shapes, and manual inference calls, use sibling `inference`.

## Custom Evaluation

Use `custom` for user-owned retrieval data:

```shell
python -m FlagEmbedding.evaluation.custom \
  --eval_name my_retrieval_eval \
  --dataset_dir ./data/my_retrieval \
  --splits test \
  --corpus_embd_save_dir ./runs/my_retrieval/corpus_embd \
  --output_dir ./runs/my_retrieval/search_results \
  --search_top_k 100 \
  --rerank_top_k 20 \
  --cache_path ./cache/data \
  --overwrite False \
  --k_values 1 5 10 100 \
  --eval_output_method markdown \
  --eval_output_path ./runs/my_retrieval/eval_results.md \
  --eval_metrics ndcg_at_10 recall_at_100 \
  --embedder_name_or_path BAAI/bge-m3 \
  --devices cpu \
  --cache_dir ./cache/model
```

Add a reranker by adding `--reranker_name_or_path`, optional `--reranker_model_class`, reranker lengths, and a `--rerank_top_k` value that is less than or equal to `--search_top_k`.

The custom loader has no dataset names and only the `test` split by default. If local data has multiple dataset subdirectories, run one command per subdirectory. Do not pass those subdirectory names through `--dataset_names` to the custom module.

## MTEB

Command: `python -m FlagEmbedding.evaluation.mteb`

Use MTEB when the user asks for official MTEB tasks, languages, or task types. It relies on the external MTEB package and may download task data. Its main evaluation path is embedder-focused, and the aggregate output is JSON.

Additional eval flags:

- `--languages`: language selectors such as `eng`.
- `--tasks`: MTEB task names.
- `--task_types`: task categories.
- `--use_special_instructions`: use bundled task instructions when available.
- `--examples_path`: directory of task example JSON files for ICL-style setups.

Keep MTEB runs explicit by passing `--tasks` or `--task_types`; otherwise the selected task set can become broad.

## BEIR

Command: `python -m FlagEmbedding.evaluation.beir`

Supported dataset names include `arguana`, `climate-fever`, `cqadupstack`, `dbpedia-entity`, `fever`, `fiqa`, `hotpotqa`, `msmarco`, `nfcorpus`, `nq`, `quora`, `scidocs`, `scifact`, `trec-covid`, and `webis-touche2020`. `msmarco` uses split `dev`; other BEIR datasets usually use `test`. `cqadupstack` expands into multiple subdatasets internally.

Additional eval flag:

- `--use_special_instructions`: use benchmark-specific retrieval query instructions.

BEIR uses external dataset/package downloads unless data is already local under the expected layout.

## MSMARCO

Command: `python -m FlagEmbedding.evaluation.msmarco`

Supported dataset names are `passage` and `document`. Supported splits are `dev`, `dl19`, and `dl20`. Remote loaders can pull data from dataset hubs and TREC/MSMARCO-hosted qrels, so network approval is required unless all files are prepared locally.

## MIRACL

Command: `python -m FlagEmbedding.evaluation.miracl`

Supported language dataset names are `ar`, `bn`, `en`, `es`, `fa`, `fi`, `fr`, `hi`, `id`, `ja`, `ko`, `ru`, `sw`, `te`, `th`, `zh`, `de`, and `yo`. For `de` and `yo`, the available split is `dev`; other languages use `train` and `dev`.

The dense searcher warns that MIRACL should not use `--ignore_identical_ids True`; leave it false unless there is separate dataset-specific evidence.

## MLDR

Command: `python -m FlagEmbedding.evaluation.mldr`

Supported language dataset names are `ar`, `de`, `en`, `es`, `fr`, `hi`, `it`, `ja`, `ko`, `pt`, `ru`, `th`, and `zh`. Supported splits are `train`, `dev`, and `test`. It uses hosted dataset loading for official runs.

## MKQA

Command: `python -m FlagEmbedding.evaluation.mkqa`

Supported language dataset names are `en`, `ar`, `fi`, `ja`, `ko`, `ru`, `es`, `sv`, `he`, `th`, `da`, `de`, `fr`, `it`, `nl`, `pl`, `pt`, `hu`, `vi`, `ms`, `km`, `no`, `tr`, `zh_cn`, `zh_hk`, and `zh_tw`. The supported split is `test`.

MKQA computes QA recall metrics such as `qa_recall_at_20`. Its official/local qrels format contains answer strings rather than generic `docid` relevance entries, so use `custom` for ordinary retrieval qrels.

## AIR-Bench

Command: `python -m FlagEmbedding.evaluation.air_bench`

AIR-Bench imports `air_benchmark` and uses that package's `EvalArgs`. Common flags include `--benchmark_version`, `--task_types`, `--domains`, `--languages`, `--splits`, `--output_dir`, `--search_top_k`, `--rerank_top_k`, `--cache_dir`, and `--overwrite`.

AIR-Bench model args mostly mirror the shared model args, but the model cache flag is `--model_cache_dir` instead of `--cache_dir`. The module generates search results and prints that metric computation follows the official AIR-Bench workflow. Treat this as network and compute dependent.

## BRIGHT

Command: `python -m FlagEmbedding.evaluation.bright`

Additional eval flags:

- `--task_type`: `short` or `long`; default is `short`.
- `--use_special_instructions`: defaults to true and applies benchmark-specific instructions.

Short task dataset names include `biology`, `earth_science`, `economics`, `psychology`, `robotics`, `stackoverflow`, `sustainable_living`, `leetcode`, `pony`, `aops`, `theoremqa_questions`, and `theoremqa_theorems`. Long tasks include `biology`, `earth_science`, `economics`, `psychology`, `robotics`, `stackoverflow`, `sustainable_living`, and `pony`.

Supported splits include `examples`, `Gemini-1.0_reason`, `claude-3-opus_reason`, `gpt4_reason`, `grit_reason`, and `llama3-70b_reason`. Prefer one split per run so `--output_dir` and `--eval_output_path` remain unambiguous.

## Source Shell Script Handling

The original benchmark shell recipes were adapted into the command patterns above. Do not copy or execute those raw scripts as defaults: they assume large datasets, network access, model downloads, GPU devices, and local output conventions.
