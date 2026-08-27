# PointLLM training configuration

The training entry point parses `ModelArguments`, `DataArguments`, and a
subclass of `transformers.TrainingArguments` with
`HfArgumentParser`. Values below are exact source defaults unless marked
**profile override**. Inherited Hugging Face defaults are not reproduced here;
set important inherited values explicitly in a run configuration instead of
assuming a version-independent default.

## ModelArguments

| Field | Default | Training meaning |
|---|---:|---|
| `model_name_or_path` | `""` | Initial model directory for Stage 1, or Stage-1 output for Stage 2. A usable path is required in practice. |
| `version` | `"v1"` | Conversation/model version selector. `v0` or a path containing `v0` raises `ValueError`; the supported branch selects the Vicuna v1.1 conversation template. |

The model config supplies `point_backbone`, `point_backbone_config_name`,
`mm_use_point_start_end`, and point-token constants. PointBERT construction
uses `PointTransformer_8192point_2layer` by default (the v1.2 profile). The
older v1.1 profile requires the matching base YAML and backbone checkpoint.
With `use_color=True`, model construction changes PointBERT input dimensions to
six; a three-column checkpoint/data pairing is then invalid.

## DataArguments

| Field | Default | Exact behavior |
|---|---:|---|
| `data_path` | `"ScanNet"` | Point-cloud directory; the shipped Objaverse profiles override it. |
| `anno_path` | `None` | Annotation JSON path. The dataset opens it directly, so `None` is not a usable training value. |
| `use_color` | `False` | Keep RGB columns and configure six-dimensional point input when true. The profiles set `True`. |
| `data_debug_num` | `0` | If greater than zero, truncate to that many records. |
| `split_train_val` | `False` | If true, construct train and validation datasets; otherwise `eval_dataset=None`. |
| `split_ratio` | `0.9` | Prefix fraction used for train and suffix for validation when splitting. |
| `pointnum` | `8192` | Filename suffix and expected sampling count. |
| `conversation_types` | `["simple_description"]` | Dataset filter. Stage 2 overrides it with `detailed_description`, `single_round`, and `multi_round`. |
| `is_multimodal` | `True` | Declared multimodal marker; the training body does not branch on it. |

The model fills `point_token_len`, `mm_use_point_start_end`, and
`point_backbone_config` into `data_args` before dataset construction. The
collator pads text, masks padding labels with `-100`, and returns point clouds
as a stacked tensor only when all shapes match; otherwise it returns a list.
The dataset normalizes XYZ, retains RGB when requested, filters two known
corrupt colored-object IDs, and replaces `<point>` with the configured number
of point tokens. A point-token count or point-start/end mismatch is a hard
model error, not a harmless warning.

## Custom TrainingArguments

| Field | Default | Profile / operational meaning |
|---|---:|---|
| `cache_dir` | `None` | Optional Transformers cache location. |
| `optim` | `adamw_torch` | Optimizer name passed to the inherited Trainer. |
| `model_max_length` | `2048` | Tokenizer truncation length and effective text limit. |
| `model_debug` | `False` | If true, builds from config instead of loading model weights; this is a model-init/debug mode, not a recovery shortcut. |
| `fix_llm` | `True` | True freezes the model first; false leaves the LLM trainable. |
| `fix_pointnet` | `True` | True runs the point backbone in eval/no-gradient context. In Stage 1 it also sets `requires_grad=False`; Stage 2 intentionally retains source FSDP handling. |
| `remove_unused_columns` | `False` | Required for the custom point-cloud batch fields. |
| `force_fsdp` | `False` | Declared source flag; no direct branch in the training body. Do not confuse it with inherited `fsdp`. |
| `tune_mm_mlp_adapter` | `True` | Projector/embedding adapter save and train switch. False freezes `point_proj`. |
| `stage_2` | `False` | Controls Stage-1 versus Stage-2 initialization path. |
| `pretrained_mm_mlp_adapter` | `None` | Declared adapter path; the visible training body does not consume it directly. Stage 2 instead loads the Stage-1 model directory. |
| `detatch_point_token` | `False` | Deprecated declaration; no active training behavior in the visible body. |
| `point_backbone_ckpt` | `None` | Stage 1's PointBERT checkpoint argument. Stage 1 calls the loader with it; a real file is required. |

The shell profiles also set the inherited arguments below explicitly:

| Setting | Stage 1 | Stage 2 |
|---|---:|---:|
| `num_train_epochs` | 3 | 3 |
| `per_device_train_batch_size` | 16 | 4 |
| `per_device_eval_batch_size` | 4 | 1 |
| `gradient_accumulation_steps` | 1 | 1 |
| `learning_rate` | `2e-3` | `2e-5` |
| `weight_decay` | `0.` | `0.` |
| `warmup_ratio` | `0.03` | `0.03` |
| `lr_scheduler_type` | `cosine` | `cosine` |
| `logging_steps` | 1 | 1 |
| `bf16` | True | True |
| `gradient_checkpointing` | True | True |
| `evaluation_strategy` | `no` | `no` |
| `save_strategy` | `no` | `no` |
| `save_steps` | 2400 | 2400 |
| `save_total_limit` | 1 | 1 |
| `report_to` | `wandb` | `wandb` |
| `use_color` | True | True |

Stage 2 additionally sets `eval_steps=100`, but with
`evaluation_strategy=no` this does not schedule evaluation. It sets
`fsdp="full_shard auto_wrap"` and
`fsdp_transformer_layer_cls_to_wrap="LlamaDecoderLayer"`. FSDP is a
resource/backend choice, not a substitute for a valid Stage-1 checkpoint.

## Freeze and adapter truth table

The following is the source control flow, not a generic multimodal recipe:

| Flags | LLM | Point projector | Point backbone forward |
|---|---|---|---|
| Stage 1 profile: `fix_llm=True`, `fix_pointnet=True`, `tune_mm_mlp_adapter=True` | frozen | trainable | eval + no gradient; `requires_grad=False` is set in the non-Stage-2 branch |
| Stage 1 variant with `fix_pointnet=False` | frozen | trainable | trainable; high memory and not the shipped profile |
| Stage 2 profile: `fix_llm=False`, `fix_pointnet=True`, adapter true | trainable | trainable | eval + no gradient; parameter wrapping follows the source FSDP experiment |
| Any stage with `tune_mm_mlp_adapter=False` | as above | frozen by the explicit branch | as above |

When `fix_llm=True`, tokenizer initialization can resize embeddings for point
start/end tokens and makes input embeddings trainable while preserving the
original embedding snapshot; output embeddings remain fixed. This is why a
Stage-1 adapter save may contain `embed_tokens` or `embed_in` as well as
`point_proj`.

## Configuration and checkpoint compatibility checks

Before a run, verify all of the following:

1. `version=v1`; do not pass a v0 model/path.
2. `use_color` agrees with both the data columns and the PointBERT checkpoint.
3. Stage 1 has `point_backbone_ckpt`; its YAML name and filename are the same
   family (`v1.2` or `v1.1`).
4. Stage 2's model directory is the final Stage-1 output, not merely an
   adapter-only directory.
5. `pointnum` agrees with the annotation-referenced `.npy` filename suffix.
6. `model_max_length` leaves room for the expanded point-token sequence; the
   source tokenizer truncates after expansion preparation, so overlong records
   can lose supervision.
7. If `split_train_val=True`, expect a real validation dataset only when the
   annotation list and split are valid. The shipped profiles deliberately do
   not evaluate.
8. If `bf16=True`, verify accelerator support and that the selected PyTorch
   build can execute the model's point and LLM kernels in bf16. The flag alone
   is not a proof of compatibility.
