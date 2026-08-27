# PointLLM training workflows

These are safe-to-edit command templates distilled from the shipped training
profiles. They are documentation, not commands executed by this skill. Replace
angle-bracket values with local paths, run the bundled validator first, and
only then decide whether to launch. The templates use the installed package
module form so they do not depend on a particular checkout layout.

## Preconditions shared by both stages

- `model_name_or_path` must identify a compatible local initial model directory
  for Stage 1 or a complete Stage-1 output for Stage 2.
- `data_path` must contain files named `<object_id>_8192.npy` when `pointnum` is
  8192. The dataset normalizes XYZ around its centroid and unit radius; with
  `use_color=True`, it retains the RGB columns.
- `anno_path` is a JSON list of records. Records are filtered by
  `conversation_type`, and records whose first conversation does not contain
  `<point>` do not carry a point cloud into the multimodal path.
- `output_dir` is created/updated by the Hugging Face Trainer. It must not be
  reused accidentally: an existing `checkpoint-*` child makes `train.py`
  request resume automatically.
- The source profile uses `PYTHONPATH` only to make the package importable. In
  an installed package environment it is normally unnecessary; if running from
  a project checkout, set it to the project root explicitly.

## Stage 1: projector alignment profile

The source profile's effective values are:

```text
model_name_or_path       = <initial PointLLM_7B_or_13B_directory>
data_path               = <objaverse_point_cloud_directory>
anno_path               = <PointLLM_brief_description_660K_filtered.json>
output_dir              = <stage1_output_directory>
point_backbone_ckpt     = <initial_directory>/point_bert_v1.2.pt
version                 = v1
model_max_length        = 2048
num_train_epochs        = 3
per_device_train_batch_size = 16
per_device_eval_batch_size  = 4
gradient_accumulation_steps  = 1
evaluation_strategy     = no
save_strategy           = no
save_steps              = 2400
save_total_limit        = 1
learning_rate           = 2e-3
weight_decay            = 0.
warmup_ratio             = 0.03
lr_scheduler_type       = cosine
logging_steps           = 1
bf16                    = True
fix_llm                 = True
fix_pointnet            = True
gradient_checkpointing   = True
report_to               = wandb
use_color               = True
conversation_types      = [simple_description]  # dataclass default
stage_2                 = False                  # dataclass default
tune_mm_mlp_adapter     = True                   # dataclass default
```

In the source implementation, Stage 1 calls
`load_point_backbone_checkpoint(point_backbone_ckpt)` and initializes tokenizer
point tokens/embeddings. `fix_llm=True` first freezes the whole model, then
re-enables the projector and point-backbone parameters; the later
`fix_pointnet=True` branch explicitly turns point-backbone gradients off when
`stage_2=False`. Therefore the shipped shell is projector alignment, not proof
that the PointBERT backbone updates. To train the backbone, changing
`fix_pointnet` is a deliberate high-memory variant and must be validated and
reviewed separately.

Inert launch template:

```bash
export MASTER_PORT=<free_port>
export PYTHONPATH="${PYTHONPATH:-}"
torchrun --nnodes=1 --nproc_per_node=8 --master_port="${MASTER_PORT}" \
  -m pointllm.train.train_mem \
  --model_name_or_path "<initial_model_dir>" \
  --data_path "<point_cloud_dir>" \
  --anno_path "<brief_description_filtered.json>" \
  --output_dir "<stage1_output_dir>" \
  --version v1 --model_max_length 2048 --num_train_epochs 3 \
  --per_device_train_batch_size 16 --per_device_eval_batch_size 4 \
  --gradient_accumulation_steps 1 --evaluation_strategy no \
  --save_strategy no --save_steps 2400 --save_total_limit 1 \
  --learning_rate 2e-3 --weight_decay 0. --warmup_ratio 0.03 \
  --lr_scheduler_type cosine --logging_steps 1 --bf16 True \
  --fix_llm True --fix_pointnet True --gradient_checkpointing True \
  --report_to wandb --run_name stage1 --point_backbone_ckpt \
  "<initial_model_dir>/point_bert_v1.2.pt" --use_color True
```

The model config selects the PointBERT YAML. For the source's v1.2 profile the
name is `PointTransformer_8192point_2layer`; the older v1.1 reproduction uses
`PointTransformer_base_8192point` and the matching `point_bert_v1.1.pt` file.
Those two choices must not be mixed.

## Stage 2: instruction-tuning profile

The source profile's effective changes are:

```text
model_name_or_path       = <stage1_output_directory>
anno_path               = <PointLLM_complex_instruction_70K.json>
output_dir              = <stage2_output_directory>
per_device_train_batch_size = 4
per_device_eval_batch_size  = 1
learning_rate           = 2e-5
fix_llm                 = False
fix_pointnet            = True
stage_2                 = True
fsdp                    = "full_shard auto_wrap"
fsdp_transformer_layer_cls_to_wrap = LlamaDecoderLayer
conversation_types      = [detailed_description, single_round, multi_round]
```

All other values in the Stage-1 profile remain the same unless shown above.
The script does not pass `tune_mm_mlp_adapter`, so its source default remains
`True`; this means the projector is not implicitly frozen in Stage 2. In
Stage 2, `initialize_tokenizer_point_backbone_config_wo_embedding` assumes the
Stage-1 model already carries point-token configuration and learned weights.
The point backbone is run under `torch.no_grad()` and set to eval mode when
`fix_pointnet=True`; its `requires_grad` handling is intentionally left
compatible with the source's FSDP experiment and should not be "simplified"
without a new verification.

Inert launch template:

```bash
export MASTER_PORT=<free_port>
export PYTHONPATH="${PYTHONPATH:-}"
torchrun --nnodes=1 --nproc_per_node=8 --master_port="${MASTER_PORT}" \
  -m pointllm.train.train_mem \
  --model_name_or_path "<stage1_output_dir>" \
  --data_path "<point_cloud_dir>" \
  --anno_path "<complex_instruction_70K.json>" \
  --output_dir "<stage2_output_dir>" \
  --version v1 --model_max_length 2048 --num_train_epochs 3 \
  --per_device_train_batch_size 4 --per_device_eval_batch_size 1 \
  --gradient_accumulation_steps 1 --evaluation_strategy no \
  --eval_steps 100 --save_strategy no --save_steps 2400 \
  --save_total_limit 1 --learning_rate 2e-5 --weight_decay 0. \
  --warmup_ratio 0.03 --lr_scheduler_type cosine --logging_steps 1 \
  --bf16 True --fix_llm False --fix_pointnet True \
  --report_to wandb --run_name stage2 --gradient_checkpointing True \
  --stage_2 True --fsdp "full_shard auto_wrap" \
  --fsdp_transformer_layer_cls_to_wrap LlamaDecoderLayer \
  --conversation_types detailed_description single_round multi_round \
  --use_color True
```

## Entry-point choice

`train_mem.py` applies the FlashAttention monkey patch before importing
`train.py`; it expects a compatible `flash_attn` interface and does not support
attention outputs, cache use, or past-key-value use in its patched forward.
`train.py` is the unpatched entry point. It is useful for import/help or a
carefully tested fallback when FlashAttention is unavailable, but its resource
behavior is not interchangeable with `train_mem.py`.

## Resume and save sequence

1. `train.py` parses all three dataclasses and sets `model.config.use_cache=False`.
2. It builds the model/tokenizer, wires point-token metadata into the data
   arguments, and constructs `PointLLMTrainer`.
3. If `output_dir/checkpoint-*` has at least one child, it calls
   `trainer.train(resume_from_checkpoint=True)`; otherwise it calls
   `trainer.train()`.
4. It calls `trainer.save_state()` and then a CPU-state save. When
   `tune_mm_mlp_adapter=True`, the trainer's `_save` filters keys containing
   `point_proj`, `embed_tokens`, or `embed_in` into adapter output: a final
   `point_proj.bin` at the output root, or `<parent>/point_proj/checkpoint-N.bin`
   for a checkpoint directory. The normal Trainer save is also performed.

Because the templates use `save_strategy=no`, a clean run generally has no
periodic checkpoint to resume. Do not delete a `checkpoint-*` directory merely
to suppress resume until its state and provenance have been checked.
