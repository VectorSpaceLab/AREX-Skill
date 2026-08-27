# XLNet API Reference

All tensor shapes below use XLNet's native `[len, bsz, ...]` layout unless noted. Downstream task wrappers often transpose batch-first features before building the model.

## Core configuration and wrapper objects

| API | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `xlnet.XLNetConfig` | `__init__(FLAGS=None, json_path=None)` | Load model hyperparameters from flags or JSON. | Required JSON keys: `n_layer`, `d_model`, `n_head`, `d_head`, `d_inner`, `ff_activation`, `untie_r`, `n_token`. `untie_r` must be present even if you keep tied biases. |
| `xlnet.RunConfig` | `__init__(is_training, use_tpu, use_bfloat16, dropout, dropatt, init='normal', init_range=0.1, init_std=0.02, mem_len=None, reuse_len=None, bi_data=False, clamp_len=-1, same_length=False)` | Hold run-time hyperparameters that may differ between pretraining and finetuning. | `mem_len`, `reuse_len`, `bi_data`, and `same_length` are mainly pretraining knobs. |
| `xlnet.create_run_config` | `create_run_config(is_training, is_finetune, FLAGS)` | Convenience wrapper for `RunConfig`. | Uses `FLAGS.use_tpu`, `FLAGS.use_bfloat16`, `FLAGS.dropout`, `FLAGS.dropatt`, `FLAGS.init`, `FLAGS.init_range`, `FLAGS.init_std`, and `FLAGS.clamp_len`; adds memory settings only when `is_finetune=False`. |
| `xlnet.XLNetModel` | `__init__(xlnet_config, run_config, input_ids, seg_ids, input_mask, mems=None, perm_mask=None, target_mapping=None, inp_q=None, **kwargs)` | Build the XLNet computation graph and expose the main outputs. | `input_ids`, `seg_ids`, and `input_mask` are `[len, bsz]`. `mems` is a list of length `n_layer`. `target_mapping` and `inp_q` are pretraining-only. |

## `XLNetModel` outputs

| Method | Returns | Use when | Notes |
| --- | --- | --- | --- |
| `get_pooled_out(summary_type, use_summ_proj=True)` | `[bsz, d_model]` | You need one vector per example for classification or regression. | `summary_type` can be `last`, `first`, `mean`, or `attn`. `use_summ_proj=False` skips the tanh projection layer. |
| `get_sequence_output()` | `[len, bsz, d_model]` | You need token-level features, span heads, or a custom pooling scheme. | This is the raw final-layer sequence representation. |
| `get_new_memory()` | list of `[mem_len, bsz, d_model]` tensors | You want to feed XLNet memories into the next segment. | The list length matches `n_layer`. |
| `get_embedding_table()` | `[n_token, d_model]` | You need tied input/output embeddings or a tied LM head. | Pair with `modeling.lm_loss(..., tie_weight=True, lookup_table=...)`. |
| `get_initializer()` | TensorFlow initializer | You are adding new layers on top of XLNet. | Use the same initializer family as the base model so the new head matches the checkpoint setup. |

### Output choice rule of thumb

- Use `get_pooled_out()` when your label is one value per example.
- Use `get_sequence_output()` when the answer depends on token positions.
- Use `get_pooled_out(summary_type='attn')` if you want a learned mask-aware summary instead of `last` or `mean`.

## Graph and loss primitives

| API | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `modeling.transformer_xl` | `transformer_xl(inp_k, n_token, n_layer, d_model, n_head, d_head, d_inner, dropout, dropatt, attn_type, bi_data, initializer, is_training, mem_len=None, inp_q=None, mems=None, same_length=False, clamp_len=-1, untie_r=False, use_tpu=True, input_mask=None, perm_mask=None, seg_id=None, reuse_len=None, ff_activation='relu', target_mapping=None, use_bfloat16=False, scope='transformer', **kwargs)` | Build the core Transformer-XL / XLNet graph. | Returns `(output, new_mems, lookup_table)`. `attn_type='bi'` is used by the XLNet wrapper. `target_mapping` and `inp_q` activate two-stream pretraining behavior. |
| `modeling.lm_loss` | `lm_loss(hidden, target, n_token, d_model, initializer, lookup_table=None, tie_weight=False, bi_data=True, use_tpu=False)` | Compute token-level language-model loss. | `tie_weight=True` requires `lookup_table`. TPU mode uses the one-hot / log-softmax path. |
| `modeling.summarize_sequence` | `summarize_sequence(summary_type, hidden, d_model, n_head, d_head, dropout, dropatt, input_mask, is_training, initializer, scope=None, reuse=None, use_proj=True)` | Turn a sequence of hidden states into a single vector summary. | `scope` lets you keep separate heads from sharing parameters. `attn` summary uses `input_mask` when provided. |
| `modeling.classification_loss` | `classification_loss(hidden, labels, n_class, initializer, scope, reuse=None, return_logits=False)` | Dense classification head used by task wrappers. | Returns per-example loss; with `return_logits=True`, also returns logits. |
| `modeling.regression_loss` | `regression_loss(hidden, labels, initializer, scope, reuse=None, return_logits=False)` | Dense scalar regression head used by task wrappers. | Uses a single logit and squared-error loss. |

## Task-head wrappers from `function_builder`

| API | What it builds | Required feature keys | Returns | Notes |
| --- | --- | --- | --- | --- |
| `get_classification_loss(FLAGS, features, n_class, is_training)` | XLNet + pooled summary + classification head | `input_ids`, `segment_ids`, `input_mask`, `label_ids` | `total_loss, per_example_loss, logits` | Uses `FLAGS.summary_type`, `FLAGS.use_summ_proj`, and a task-specific classification scope. |
| `get_regression_loss(FLAGS, features, is_training)` | XLNet + pooled summary + regression head | `input_ids`, `segment_ids`, `input_mask`, `label_ids` | `total_loss, per_example_loss, logits` | Uses a task-specific regression scope. |
| `get_qa_outputs(FLAGS, features, is_training)` | XLNet + span QA heads | `input_ids`, `segment_ids`, `input_mask`, `p_mask`, `cls_index`, and `start_positions` when training | dict of logits / log-probs | Training returns `start_log_probs`, `end_log_probs`, and `cls_logits`. Inference returns top-k start/end candidates plus `cls_logits`. |
| `get_race_loss(FLAGS, features, is_training)` | XLNet + pooled summary + 4-way choice head | `input_ids`, `segment_ids`, `input_mask`, `label_ids` | `total_loss, per_example_loss, logits` | Expects the four answer choices to be flattened in the same layout as the RACE wrapper. |

## Runtime and optimization helpers

| API | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `model_utils.configure_tpu` | `configure_tpu(FLAGS)` | Build a legacy `tf.contrib.tpu.RunConfig` or mirrored single-host strategy setup. | `use_tpu=True` uses `TPUClusterResolver`; `num_core_per_host > 1` on non-TPU uses `MirroredStrategy`; otherwise single-device mode. |
| `model_utils.init_from_checkpoint` | `init_from_checkpoint(FLAGS, global_vars=False)` | Map checkpoint variables into the current graph. | Returns a TPU scaffold function when `FLAGS.use_tpu` is true, otherwise initializes immediately. If `FLAGS.init_checkpoint` ends with `latest`, the latest checkpoint in that directory is used. |
| `model_utils.get_train_op` | `get_train_op(FLAGS, total_loss, grads_and_vars=None)` | Build the optimizer, learning-rate schedule, clipping, and optional layerwise decay. | Returns `train_op, learning_rate, gnorm`. Supports warmup plus polynomial or cosine decay. Weight decay is not supported with multi-GPU non-TPU training. |
| `model_utils.clean_ckpt` | CLI entrypoint in `model_utils.py` | Remove optimizer baggage from a checkpoint. | Drops `global_step` and Adam-slot variables, then saves a fresh checkpoint. |
| `model_utils.avg_checkpoints` | `avg_checkpoints(model_dir, output_model_dir, last_k)` | Average the last `k` checkpoints. | Averages only variable tensors, not optimizer slots or step state. |
| `gpu_utils.assign_to_gpu` | `assign_to_gpu(gpu=0, ps_dev='/device:CPU:0')` | Build a tower-placement function for multi-GPU graphs. | Variables go to CPU by default; non-variable ops go to the selected GPU. |
| `gpu_utils.average_grads_and_vars` | `average_grads_and_vars(tower_grads_and_vars)` | Average dense and sparse gradients across towers. | Returns averaged `(grad, var)` pairs using the first tower's variable references. |
| `gpu_utils.load_from_checkpoint` | `load_from_checkpoint(saver, logdir)` | Restore the latest checkpoint into the current session. | Session-bound helper; returns `False` when no checkpoint is available. |

## Tokenization helpers

| API | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `prepro_utils.preprocess_text` | `preprocess_text(inputs, lower=False, remove_space=True, keep_accents=False)` | Normalize raw text before SentencePiece tokenization. | Collapses whitespace, normalizes quotes, strips accents unless `keep_accents=True`, and lowercases when `lower=True`. |
| `prepro_utils.encode_pieces` | `encode_pieces(sp_model, text, return_unicode=True, sample=False)` | Convert text to SentencePiece pieces. | `sample=True` uses stochastic segmentation. The helper preserves the repo's special handling for comma-after-digit pieces. |
| `prepro_utils.encode_ids` | `encode_ids(sp_model, text, sample=False)` | Convert text to integer token ids. | Call `preprocess_text()` first when you want release-parity tokenization behavior. |

## Quick build pattern

```python
xlnet_config = xlnet.XLNetConfig(json_path=FLAGS.model_config_path)
run_config = xlnet.create_run_config(is_training=True, is_finetune=True, FLAGS=FLAGS)
model = xlnet.XLNetModel(
    xlnet_config=xlnet_config,
    run_config=run_config,
    input_ids=input_ids,
    seg_ids=seg_ids,
    input_mask=input_mask)
summary = model.get_pooled_out('last')
sequence = model.get_sequence_output()
```
