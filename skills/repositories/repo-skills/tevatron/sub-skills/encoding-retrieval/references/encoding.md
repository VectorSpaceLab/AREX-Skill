# Encoding Reference

Tevatron encoding turns prepared query or corpus records into pickle files for FAISS search. The standard path is the PyTorch driver `tevatron.retriever.driver.encode`; vLLM encoding is optional and should be used only when the target environment and model support embedding mode.

## Embedding Pickle Contract

Every Tevatron encoder writes a pickle containing:

```python
(encoded, lookup_indices)
```

- `encoded`: a two-dimensional NumPy-compatible array shaped `(rows, embedding_dim)`.
- `lookup_indices`: row-aligned query IDs or document IDs.
- Query and passage arrays must share the same `embedding_dim` before search.
- The text ranking writer converts lookup IDs to strings, so preserve external IDs exactly in input data.

Probe custom or transferred embedding files before search:

```bash
python - <<'PY'
import pickle
for path in ['embeddings/query.pkl', 'embeddings/corpus.00.pkl']:
    with open(path, 'rb') as handle:
        reps, lookup = pickle.load(handle)
    print(path, getattr(reps, 'shape', None), len(lookup), lookup[:3])
    assert len(reps) == len(lookup)
    assert len(getattr(reps, 'shape', ())) == 2
PY
```

## Standard Encoder Driver

Use the standard text encoder for most dense retrieval workflows:

```bash
python -m tevatron.retriever.driver.encode \
  --output_dir temp \
  --model_name_or_path MODEL_OR_CHECKPOINT \
  --tokenizer_name TOKENIZER_OR_MODEL \
  --fp16 \
  --pooling eos \
  --normalize \
  --query_prefix "Query: " \
  --passage_prefix "Passage: " \
  --per_device_eval_batch_size 128 \
  --query_max_len 32 \
  --passage_max_len 156 \
  --dataset_name DATASET_NAME \
  --dataset_split SPLIT \
  --encode_is_query \
  --encode_output_path embeddings/query.pkl
```

The driver loads `DenseModel`, tokenizes with `AutoTokenizer`, iterates `EncodeDataset` through `EncodeCollator`, and writes query representations when `--encode_is_query` is present or passage representations otherwise. It rejects distributed/multi-GPU evaluation through a local-rank guard, so shard large corpora across separate single-device processes.

## Query vs Corpus Fields

The encoder reads Hugging Face datasets or local JSON/JSONL through `datasets.load_dataset`.

For query encoding with `--encode_is_query`, each record should have:

- `query_id`: ID saved in `lookup_indices`.
- `query_text` or legacy `query`: text to encode.
- Optional multimodal fields such as `query_image`, `query_video`, or `query_audio` for multimodal drivers.

For corpus encoding without `--encode_is_query`, each record should have:

- `docid`: ID saved in `lookup_indices`.
- `text`: passage body.
- Optional `title`: prepended to `text` with a space.
- Optional multimodal fields such as `image`, `video`, or `audio` for multimodal drivers.

Use the data-preparation sibling sub-skill when fields need conversion, validation, or qrels/ranking construction before encoding.

## Corpus Encoding

```bash
python -m tevatron.retriever.driver.encode \
  --output_dir temp \
  --model_name_or_path MODEL_OR_CHECKPOINT \
  --tokenizer_name TOKENIZER_OR_MODEL \
  --fp16 \
  --pooling eos \
  --normalize \
  --passage_prefix "Passage: " \
  --per_device_eval_batch_size 128 \
  --passage_max_len 156 \
  --dataset_name CORPUS_DATASET_NAME \
  --encode_output_path embeddings/corpus.00.pkl
```

For local files, use `--dataset_name json` and set `--dataset_path` to the JSON/JSONL file or files. Keep `--dataset_split` consistent with how Hugging Face `datasets` exposes the loaded data.

## Sharded Corpus Encoding

Use Hugging Face dataset sharding for large corpora or multi-device fan-out:

```bash
mkdir -p embeddings
for shard in $(seq -f "%02g" 0 19); do
  CUDA_VISIBLE_DEVICES=0 python -m tevatron.retriever.driver.encode \
    --output_dir temp \
    --model_name_or_path MODEL_OR_CHECKPOINT \
    --fp16 \
    --per_device_eval_batch_size 156 \
    --passage_max_len 128 \
    --dataset_name CORPUS_DATASET_NAME \
    --dataset_number_of_shards 20 \
    --dataset_shard_index "${shard}" \
    --encode_output_path "embeddings/corpus.${shard}.pkl"
done
```

When launching shards in parallel, assign each process an intended device and a unique `--encode_output_path`. Shard indices are zero-based and must be less than `--dataset_number_of_shards`.

## Query Encoding

```bash
python -m tevatron.retriever.driver.encode \
  --output_dir temp \
  --model_name_or_path MODEL_OR_CHECKPOINT \
  --tokenizer_name TOKENIZER_OR_MODEL \
  --fp16 \
  --pooling eos \
  --normalize \
  --query_prefix "Query: " \
  --per_device_eval_batch_size 128 \
  --query_max_len 32 \
  --dataset_name QUERY_DATASET_NAME \
  --dataset_split dev \
  --encode_is_query \
  --encode_output_path embeddings/query-dev.pkl
```

Use the same trained retrieval recipe as corpus encoding: checkpoints, tokenizer, pooling, normalization, LoRA adapter, instruction prefixes, `--append_eos_token`, and padding side should match unless you are intentionally testing a mismatch.

## Important Flags

- `--encode_is_query`: switches from passage fields to query fields and writes query representations.
- `--encode_output_path`: output pickle path; create parent directories before launch if needed.
- `--dataset_name`, `--dataset_config`, `--dataset_path`, `--dataset_split`: select Hugging Face, local JSON/JSONL, or configured benchmark inputs.
- `--dataset_number_of_shards`, `--dataset_shard_index`: split the loaded encode dataset before iteration.
- `--query_prefix`, `--passage_prefix`: prepend instruction text before tokenization.
- `--query_max_len`, `--passage_max_len`: truncation lengths; the active side depends on `--encode_is_query`.
- `--pooling`, `--normalize`, `--append_eos_token`, `--padding_side`: representation behavior that must align with model training or inference docs.
- `--lora`, `--lora_name_or_path`: load a trained LoRA adapter when the retrieval recipe used one.
- `--fp16`, `--bf16`: request reduced precision in the standard encoder; omit for float32 diagnostics.
- `--per_device_eval_batch_size`: primary memory knob for encoding.

## Optional vLLM Encoding

Use `tevatron.retriever.driver.vllm_encode` only when `vllm` is installed, the model supports `LLM(task="embed")`, and the runtime can satisfy model/CUDA requirements:

```bash
python -m tevatron.retriever.driver.vllm_encode \
  --output_dir temp \
  --model_name_or_path MODEL_OR_CHECKPOINT \
  --tokenizer_name TOKENIZER_OR_MODEL \
  --bf16 \
  --pooling eos \
  --normalize \
  --per_device_eval_batch_size 64 \
  --dataset_name Tevatron/beir \
  --dataset_config scifact \
  --dataset_split test \
  --query_max_len 512 \
  --encode_is_query \
  --encode_output_path embeddings/query-scifact.pkl
```

The vLLM path builds a `PoolerConfig`, calls `LLM(..., task="embed")`, optionally passes a LoRA request when `--lora_name_or_path` is set, and writes float16 arrays. It forces right padding in the text path. If vLLM fails due missing packages, unsupported embedding mode, LoRA rank, dtype, or remote model code, fall back to the standard encoder for text retrieval.
