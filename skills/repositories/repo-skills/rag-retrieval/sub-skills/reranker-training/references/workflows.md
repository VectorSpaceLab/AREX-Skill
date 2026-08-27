# Reranker Training Workflows

Use this sequence for both BERT encoder and LLM decoder rerankers:

1. Choose pointwise or grouped data.
2. Choose a compatible `loss_type`.
3. Validate the YAML and JSONL with the bundled helper.
4. Select an Accelerate distributed config for the model family.
5. Build a path-checked launch command with `scripts/build_reranker_training_command.py`.
6. Use the saved model directory with reranker inference guidance after training finishes.

## BERT Encoder Reranker

Use `model_type: bert_encoder` for BERT-like cross-encoders such as BGE, BCE, XLM-R, or a BERT sequence-classification backbone.

Typical config shape:

```yaml
model_name_or_path: "BAAI/bge-reranker-v2-m3"
model_type: "bert_encoder"
num_labels: 1
query_format: "{}"
document_format: "{}"
train_dataset_type: "grouped"
train_group_size: 10
loss_type: "pairwise_ranknet"
mixed_precision: fp16
```

Build a launch command after validation:

```bash
python skills/rag-retrieval/sub-skills/reranker-training/scripts/build_reranker_training_command.py \
  --config <training-bert.yaml> \
  --backend fsdp \
  --devices 0,1
```

For fine-tuning multilingual XLM-R-derived rerankers such as BGE/BCE rerankers, use an FSDP config whose transformer wrap class matches XLM-R. For a different BERT family, update the FSDP transformer layer class accordingly.

## LLM Decoder Reranker

Use `model_type: llm_decoder` for decoder-style sequence-classification models such as Qwen-based rerankers.

Typical config shape:

```yaml
model_name_or_path: "Qwen/Qwen2.5-1.5B"
model_type: "llm_decoder"
num_labels: 1
query_format: "query: {}"
document_format: "document: {}"
seq: "\n"
special_token: "\nrelevance"
train_dataset_type: "grouped"
train_group_size: 10
loss_type: "pairwise_ranknet"
mixed_precision: bf16
batch_size: 2
```

Build a launch command after validation:

```bash
python skills/rag-retrieval/sub-skills/reranker-training/scripts/build_reranker_training_command.py \
  --config <training-llm.yaml> \
  --backend deepspeed-zero1 \
  --devices 0,1
```

Prefer DeepSpeed ZeRO-1 or ZeRO-2 for LLM decoder reranker training. Avoid ZeRO-3 in this flow because the upstream docs call out a save-time incompatibility.

## Pointwise Launch Shape

Pointwise training is best for independent labels or teacher scores:

```yaml
train_dataset: "data/reranker-pointwise.jsonl"
train_dataset_type: "pointwise"
train_label_key: "label"
max_label: 2
min_label: 0
loss_type: "pointwise_bce"
```

Use `pointwise_mse` when labels are continuous teacher scores and the goal is score regression. Use `pointwise_bce` when labels are binary or scaled relevance values used as soft labels.

## Grouped Launch Shape

Grouped training is best when each query has enough candidates to compare within a group:

```yaml
train_dataset: "data/reranker-grouped.jsonl"
train_dataset_type: "grouped"
train_label_key: "label"
train_group_size: 8
loss_type: "pairwise_ranknet"
```

Use `pairwise_ranknet` for multi-level or continuous labels where relative ordering matters. Use `listwise_ce` only when each group is intended to have one positive document and the rest negatives; inspect warnings if groups have zero or multiple positive labels.

## Validation Sequence

Run validation before training:

```bash
python skills/rag-retrieval/sub-skills/reranker-training/scripts/validate_reranker_training_config.py \
  --config <training-config.yaml> \
  --data <train-data.jsonl>
```

Then check:

- `model_type` is one of `bert_encoder` or `llm_decoder`.
- `train_dataset_type` matches the JSONL shape.
- `loss_type` matches the dataset type.
- pointwise labels fit `[min_label, max_label]`.
- grouped data has enough surviving groups after `train_group_size` and identical-label skip rules.
- LLM formatting fields contain `{}` where raw query/document text must be inserted.

If validation reports skipped groups, shrink `train_group_size`, collect more hits per query, or switch to pointwise training.

## Saved Model Usage

At the end of training, `train_reranker.py` saves the final model and tokenizer under:

```text
<output_dir>/model
```

Epoch checkpoints, when enabled, are saved under the project runs/checkpoints structure below `output_dir`.

For inference, pass the saved model directory to the sibling reranker inference flow and choose the matching model class:

- BERT encoder checkpoints load with the cross-encoder reranker path.
- LLM decoder checkpoints load with the LLM decoder reranker path and must reuse compatible `query_format`, `document_format`, `seq`, and `special_token` values.

Do not mix a BERT checkpoint with LLM decoder formatting fields, or an LLM decoder checkpoint with BERT cross-encoder inference code.
