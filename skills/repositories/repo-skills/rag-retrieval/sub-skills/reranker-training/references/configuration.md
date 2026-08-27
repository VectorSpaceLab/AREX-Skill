# Reranker Training Configuration

Reranker training is controlled by a YAML file passed to `train_reranker.py --config`. This skill bundles the inspected training snapshot under `scripts/training_bundle/`. YAML values override parser defaults, so inspect the final config rather than relying on defaults.

## Core Model Fields

Required model fields:

- `model_name_or_path`: Hugging Face model id or a checkpoint directory available in the runtime environment.
- `model_type`: must be `bert_encoder` or `llm_decoder`.
- `num_labels`: usually `1`, because ranking losses operate on one scalar logit per query-document pair.
- `max_len`: tokenizer input limit used by the model-specific `preprocess` method.

`bert_encoder` uses the BERT-like `CrossEncoder` path. It tokenizes query/document pairs together with `add_special_tokens=True`, `padding="longest"`, and truncates only the document side.

`llm_decoder` uses the decoder-style `LLMDecoder` path. It manually concatenates formatted query tokens, separator tokens, formatted document tokens, and special-token tokens. The tokenizer pads on the right and uses the EOS token as padding when needed.

## Data Fields

Training dataset fields:

- `train_dataset`: JSONL file for training.
- `train_dataset_type`: `pointwise` or `grouped`.
- `train_label_key`: label field name; default behavior is `label`.
- `train_group_size`: required for grouped data and must be at least `2`.
- `shuffle_rate`: probability of text shuffling augmentation; must be between `0` and `1`.

Validation dataset fields:

- `val_dataset`: optional JSONL validation file; omit or set to null/empty when not validating.
- `val_dataset_type`: `pointwise` or `grouped`, matching the validation file shape.
- `val_label_key`: validation label field name.

Pointwise-only scaling fields:

- `min_label`: minimum allowed pointwise label; must be non-negative.
- `max_label`: maximum allowed pointwise label; must be greater than `min_label`.

Grouped labels are not scaled by these fields.

## Loss Compatibility

Use the dataset type and loss together:

| Dataset type | Compatible loss values |
| --- | --- |
| `pointwise` | `pointwise_bce`, `pointwise_mse` |
| `grouped` | `pairwise_ranknet`, `listwise_ce` |

Avoid legacy README names such as `point_ce`; the actual training code checks `pointwise_bce`, `pointwise_mse`, `pairwise_ranknet`, and `listwise_ce`.

`pairwise_ranknet` and `listwise_ce` reshape logits and labels by `train_group_size`, so grouped batches must be built by `GroupedRankerDataset`. Pointwise batches set `model.train_group_size = 1` and are not appropriate for ranking-list losses.

## LLM Formatting Fields

For `llm_decoder`, configure all formatting fields intentionally:

- `query_format`: template containing `{}` for the raw query, such as `query: {}`.
- `document_format`: template containing `{}` for the raw document, such as `document: {}`.
- `seq`: separator between query and document, commonly a newline or space.
- `special_token`: suffix after the document that cues scalar relevance scoring, such as a newline plus `relevance` or an EOS-like token.

The effective string is approximately:

```text
<query_format(query)><seq><document_format(document)><special_token>
```

A missing `{}` placeholder discards the raw query or document text. A too-long query and special token can leave little or no `document_max_len`; reduce prompt text or increase `max_len` if documents are truncated too aggressively.

## Distributed Config Choice

Use Accelerate config files according to model family:

- BERT/XLM-R rerankers: use an FSDP config shaped like `xlmroberta_default_config.yaml`, with `distributed_type: FSDP`, `num_processes` matching visible GPUs, and `fsdp_transformer_layer_cls_to_wrap` aligned with the model family.
- LLM decoder rerankers: use DeepSpeed ZeRO-1 or ZeRO-2 configs. ZeRO-3 is not recommended for this training flow because saving the final model is called out as incompatible.

Adjust the launch command and Accelerate config together:

- `CUDA_VISIBLE_DEVICES` controls which GPUs are visible.
- Accelerate `num_processes` should match the number of visible GPUs for normal multi-GPU runs.
- DeepSpeed config may override `gradient_accumulation_steps`; if the DeepSpeed config sets it explicitly, reconcile it with the YAML training value.

## Training Hyperparameters

Important fields:

- `output_dir`: checkpoints and final model are written under this runtime path; the final model is saved to `<output_dir>/model`.
- `epochs`: number of passes over the training dataloader.
- `lr`: common starting range is around `1e-5` to `5e-5`; LLM decoder runs usually use the lower end.
- `batch_size`: dataloader batch size; for grouped data this is number of groups, while model input pairs are `batch_size * train_group_size`.
- `gradient_accumulation_steps`: increases effective batch size.
- `warmup_proportion` and `stable_proportion`: each must be in `[0, 1]`, and their sum must be at most `1`.
- `mixed_precision`: use `fp16`, `bf16`, `no`, null, or a value accepted by the installed Accelerate version. `bf16` needs hardware support.
- `save_on_epoch_end`: saves intermediate epoch checkpoints when truthy.
- `num_max_checkpoints`: maximum epoch checkpoints retained by the project configuration.

## Logging

`log_with` is passed to Accelerate tracker setup. Typical values are `wandb` and `tensorboard`.

Use `tensorboard` or disable external logging if the runtime should avoid network-backed experiment tracking. For `wandb`, ensure the training environment is already authenticated and configured before launch.
