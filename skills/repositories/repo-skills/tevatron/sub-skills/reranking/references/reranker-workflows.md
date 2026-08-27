# Reranker Workflows

Tevatron rerankers are cross-encoders built around `AutoModelForSequenceClassification`. They score one concatenated query-document string per candidate. Training groups one positive and `train_group_size - 1` negatives per query, applies cross entropy over grouped logits, and treats index `0` as the target. Inference scores every pair independently, sorts candidates for each query by descending score, and writes a tab-separated run file.

## Train a Cross-Encoder Reranker

Use `tevatron.reranker.driver.train` for current reranker training. The training dataset must expose one JSON object per query group:

- `query`: query text.
- `positive_passages`: list of passage objects with `title` and `text`.
- `negative_passages`: list of passage objects with `title` and `text`.

Minimal BERT-like local JSONL command plan:

```bash
python -m tevatron.reranker.driver.train \
  --output_dir reranker-output \
  --model_name_or_path bert-base-uncased \
  --dataset_name json \
  --dataset_path train-reranker.jsonl \
  --dataset_split train \
  --do_train \
  --per_device_train_batch_size 8 \
  --train_group_size 8 \
  --learning_rate 5e-6 \
  --rerank_max_len 256 \
  --num_train_epochs 3 \
  --save_steps 20000 \
  --logging_steps 500 \
  --overwrite_output_dir
```

For Hugging Face-hosted Tevatron datasets, replace `--dataset_name json --dataset_path train-reranker.jsonl` with the dataset name/config when the environment is allowed to download data.

### Training Pair Formatting

`RerankerTrainDataset` formats each query-passage candidate as one string:

```text
<query_prefix> <query> <passage_prefix> <title-with-hyphens-replaced> <passage text>
```

The collator tokenizes the flattened strings, truncates to `--rerank_max_len` or `--rerank_max_len - 1` when `--append_eos_token` is enabled, optionally appends EOS, and pads to `--pad_to_multiple_of`.

### Grouped Loss Semantics

For each query group, the dataset emits exactly `train_group_size` pair strings: one positive first, then negatives. The model receives flattened logits and reshapes them as:

```text
(per_device_train_batch_size, inferred_group_size)
```

It then applies cross entropy with target label `0` for every query. Practical implications:

- The positive passage must be first in every training group.
- `train_group_size` should equal one positive plus the intended number of negatives.
- If there are fewer negatives than required, Tevatron samples negatives with replacement.
- Change `--gradient_accumulation_steps` for effective batch size; do not change `train_group_size` to solve memory pressure unless you also change the intended negatives per query.

## Train with LoRA

Use LoRA for large sequence-classification rerankers or RankLLaMA-style training. Tevatron implements LoRA through `peft` with `TaskType.SEQ_CLS`.

```bash
python -m tevatron.reranker.driver.train \
  --output_dir reranker-lora \
  --model_name_or_path mistralai/Mistral-7B-v0.1 \
  --lora \
  --lora_target_modules q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj \
  --dataset_name json \
  --dataset_path train-reranker.jsonl \
  --dataset_split train \
  --do_train \
  --query_prefix "query: " \
  --passage_prefix "document: " \
  --bf16 \
  --per_device_train_batch_size 16 \
  --gradient_checkpointing \
  --train_group_size 16 \
  --learning_rate 1e-4 \
  --rerank_max_len 196 \
  --num_train_epochs 1 \
  --gradient_accumulation_steps 4
```

For new adapters, pass `--lora`. For inference with an existing adapter, pass a compatible base model with `--model_name_or_path` and the adapter path or Hub id with `--lora_name_or_path`. If the checkpoint is already merged into a sequence-classification model, omit `--lora_name_or_path`.

## Prepare Pairwise Rerank Input

Reranker inference expects one JSONL row per query-document candidate. Required fields are:

- `query_id`
- `query`
- `docid`
- `title`
- `text`
- optional `score` from the first-stage retrieval run

Use the bundled helper for local fixtures or adapted first-stage outputs:

```bash
python scripts/prepare_rerank_input.py \
  --queries queries.jsonl \
  --corpus corpus.jsonl \
  --run first-stage.run \
  --output rerank-input.jsonl \
  --depth 100
```

Accepted query id fields are `query_id`, `qid`, or `id`; accepted query text fields are `query`, `text`, or `contents`. Accepted corpus id fields are `docid`, `doc_id`, `pid`, or `id`; accepted corpus text fields are `text`, `contents`, or `body`; missing titles are written as an empty string.

The helper accepts common whitespace-separated run formats:

```text
qid docid score
qid docid rank score
qid Q0 docid rank score tag
```

By default it skips missing query/doc ids and reports counts to stderr. Add `--strict` to fail on the first missing id.

## Run Reranker Inference

Use `tevatron.reranker.driver.rerank` for current inference:

```bash
python -m tevatron.reranker.driver.rerank \
  --output_dir temp-rerank \
  --model_name_or_path reranker-output \
  --tokenizer_name bert-base-uncased \
  --dataset_name json \
  --dataset_path rerank-input.jsonl \
  --dataset_split train \
  --per_device_eval_batch_size 128 \
  --rerank_max_len 256 \
  --rerank_output_path rerank-output.tsv
```

Important constraints:

- The driver rejects multi-GPU inference (`n_gpu > 1` or `local_rank > 0`). Shard input manually or use `--dataset_number_of_shards` and `--dataset_shard_index` across independent single-device jobs.
- `--output_dir` is still required by Hugging Face `TrainingArguments`, even for scoring.
- Use `--fp16` or `--bf16` only when the selected model, device, and runtime support that precision.
- The first-stage retrieval `score` in the input JSONL is preserved for auditing but ignored by the reranker model.

## RankLLaMA-Style Reranking and Training

RankLLaMA recipes use instruction-like prefixes and a longer max sequence length. The RankLLaMA example uses `query: ` and `document: ` and computes `rerank_max_len` as query plus passage budget.

Adapter-style inference command plan:

```bash
python -m tevatron.reranker.driver.rerank \
  --output_dir temp-rankllama \
  --model_name_or_path meta-llama/Llama-2-7b-hf \
  --lora_name_or_path castorini/rankllama-v1-7b-lora-passage \
  --tokenizer_name meta-llama/Llama-2-7b-hf \
  --dataset_name json \
  --dataset_path rerank-input.jsonl \
  --dataset_split train \
  --query_prefix "query: " \
  --passage_prefix "document: " \
  --fp16 \
  --per_device_eval_batch_size 64 \
  --rerank_max_len 196 \
  --rerank_output_path rankllama-output.tsv
```

Merged-checkpoint inference differs only by using the merged checkpoint as `--model_name_or_path` and omitting `--lora_name_or_path`.

DeepSpeed LoRA training follows the same reranker train module and adds a launcher plus a DeepSpeed config:

```bash
deepspeed --num_nodes 1 --num_gpus 1 --module tevatron.reranker.driver.train \
  --deepspeed deepspeed-config.json \
  --output_dir model-rankllama \
  --model_name_or_path mistralai/Mistral-7B-v0.1 \
  --lora \
  --lora_target_modules q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj \
  --dataset_name json \
  --dataset_path train-reranker.jsonl \
  --query_prefix "query: " \
  --passage_prefix "document: " \
  --bf16 \
  --per_device_train_batch_size 16 \
  --gradient_checkpointing \
  --train_group_size 16 \
  --learning_rate 1e-4 \
  --rerank_max_len 196 \
  --num_train_epochs 1 \
  --gradient_accumulation_steps 4
```

For broader LLM retriever/ranker hardware and dependency triage, cross-check [multimodal-llm](../../multimodal-llm/SKILL.md). For base retriever RepLLaMA training/encoding, use [training](../../training/SKILL.md) and [encoding-retrieval](../../encoding-retrieval/SKILL.md).

## Interpret Reranker Output

The rerank driver writes:

```text
query_id<TAB>docid<TAB>score
```

Rows are sorted by descending score within each query. Scores are raw sequence-classification logits, not calibrated probabilities. Compare scores within the same query, not across unrelated queries. Convert to TREC or MS MARCO evaluator formats with the generated data-preparation converters when needed.

## Source Example Status

The repository includes MSMARCO and RankLLaMA example scripts. Treat them as reference recipes, not runtime dependencies, because they require model/dataset downloads, optional GPU packages, external evaluation tools, and in some older examples use paths or argument names that differ from the current `tevatron.reranker.driver.*` modules. This sub-skill’s command templates use the current package entry points and argument names verified from the installed dataclass signatures.
