# GRPO training workflows

This reference distills the VLM-R1 GRPO launch patterns into reusable recipes. Use it with `../scripts/launch_grpo_jsonl.sh` for single-node previews/execution and `../scripts/render_multinode_torchrun.py` for multi-node command rendering.

## Common launch contract

A VLM-R1 GRPO run launches `src/open_r1/grpo_jsonl.py` from the open-r1-multimodal package root under `torchrun`.

Minimum inputs:

- `model_name_or_path`: model id or local checkpoint path.
- `data_file_paths`: one or more JSONL files separated by `:`.
- `image_folders`: one image root per JSONL file, also separated by `:`. The loader joins each JSONL `image` value to its corresponding image root.
- `output_dir` and `run_name`.
- `task_type`: examples include `rec`, `gui`, `gui_defect`, and task names introduced with custom rewards.
- `reward_funcs`: usually `accuracy format`; add `length` or `repetition` only when the selected reward strategy expects them.
- `deepspeed`: usually a ZeRO-2 or ZeRO-3 JSON configuration.

Recommended command-building order:

1. Make the colon-separated lists first and count them.
2. Decide whether rewards come from the VLM module (`--is_reward_customized_from_vlm_module true`) or the generic reward registry (`false`).
3. Choose ZeRO-2 for LoRA or smaller memory pressure; choose ZeRO-3 for full fine-tuning or when the reference model is too large.
4. Pick `nproc_per_node`, `per_device_train_batch_size`, and `num_generations` so `nproc_per_node * nnodes * per_device_train_batch_size` is divisible by `num_generations`.
5. Render a dry-run command. Execute only after the paths, batch divisibility, logging, and rendezvous settings are correct.

## Single-node Qwen REC full fine-tuning

Use this for Qwen2-VL or Qwen2.5-VL REC-style bbox grounding.

```bash
sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh \
  --workdir <open-r1-multimodal-package-root> \
  --model-name-or-path Qwen/Qwen2.5-VL-3B-Instruct \
  --data-file-paths data/refcoco_train.jsonl:data/refcocop_train.jsonl:data/refcocog_train.jsonl \
  --image-folders images/coco:images/coco:images/coco \
  --output-dir outputs/rl/qwen-rec \
  --run-name qwen-rec \
  --task-type rec \
  --custom-vlm-reward true \
  --reward-funcs accuracy,format \
  --zero-stage 3 \
  --nproc-per-node 8 \
  --per-device-train-batch-size 8 \
  --gradient-accumulation-steps 2 \
  --num-train-epochs 2 \
  --num-generations 8 \
  --max-completion-length 2048 \
  --attn-implementation flash_attention_2 \
  --report-to wandb
```

Notes:

- `--custom-vlm-reward true` routes `accuracy` and `format` to the Qwen VLM module's REC IoU and REC format rewards.
- Qwen image resizing is controlled by `--max-pixels` and `--min-pixels`; keep defaults unless memory or resolution requirements force a change.
- If CUDA memory fails, lower `--per-device-train-batch-size`, lower `--max-completion-length`, use LoRA, or move from ZeRO-2 to ZeRO-3.

## LoRA plus freeze-vision with no W&B

This is the safest pattern when the user wants a lightweight REC run, vision towers frozen, matching two data/image roots, and no W&B side effects.

```bash
sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh \
  --workdir <open-r1-multimodal-package-root> \
  --model-name-or-path Qwen/Qwen2.5-VL-3B-Instruct \
  --data-file-paths data/refcoco_train.jsonl:data/refcocop_train.jsonl \
  --image-folders images/coco:images/coco \
  --output-dir outputs/rl/qwen-rec-lora-freeze \
  --run-name qwen-rec-lora-freeze \
  --task-type rec \
  --custom-vlm-reward true \
  --reward-funcs accuracy,format \
  --zero-stage 2 \
  --use-peft true \
  --lora-r 64 \
  --lora-alpha 128 \
  --lora-dropout 0.05 \
  --freeze-vision-modules true \
  --learning-rate 1e-5 \
  --nproc-per-node 8 \
  --per-device-train-batch-size 8 \
  --num-generations 8 \
  --no-wandb
```

Audit points:

- The launcher rejects a mismatch such as two JSONL files but one image root.
- `--no-wandb` exports `WANDB_DISABLED=true` and passes `--report_to none`.
- LoRA target modules are selected by the trainer from linear layers that do not match the model's vision-module keywords. `freeze_vision_modules` additionally sets matching vision parameters to non-trainable.
- If the user also uses `gradient_checkpointing`, the trainer disables model cache for compatibility.

## GUI and other multi-image runs

For GUI/multi-image data, the JSONL `image` field is a list. The training command is still one JSONL path matched to one image root, but the loader creates one prompt with multiple image placeholders.

```bash
sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh \
  --workdir <open-r1-multimodal-package-root> \
  --model-name-or-path Qwen/Qwen2.5-VL-3B-Instruct \
  --data-file-paths data/gui_multi-image.jsonl \
  --image-folders images/gui_multi-image \
  --output-dir outputs/rl/gui-multi-image \
  --run-name gui-multi-image \
  --task-type gui \
  --custom-vlm-reward false \
  --reward-method all_match \
  --reward-funcs accuracy,format \
  --zero-stage 3 \
  --per-device-train-batch-size 2 \
  --max-steps 1200 \
  --save-steps 400 \
  --num-generations 8
```

Route JSONL field validation and reward-method details to the data-and-rewards sub-skill. Training-workflows only ensures the command wires the data and reward method consistently.

## InternVL REC runs

InternVL routes by model name containing `InternVL` and changes several model-loading details internally.

```bash
sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh \
  --workdir <open-r1-multimodal-package-root> \
  --model-name-or-path OpenGVLab/InternVL2_5-4B-MPO \
  --data-file-paths data/refcoco_train.jsonl:data/refcocop_train.jsonl:data/refcocog_train.jsonl \
  --image-folders images/coco:images/coco:images/coco \
  --output-dir outputs/rl/internvl-rec \
  --run-name internvl-rec \
  --task-type rec \
  --custom-vlm-reward true \
  --max-anyres-num 6 \
  --zero-stage 2 \
  --nproc-per-node 8 \
  --per-device-train-batch-size 8 \
  --num-generations 8
```

InternVL-specific notes:

- The VLM module sets `trust_remote_code=True` and converts `flash_attention_2` into InternVL's `use_flash_attn` model-init flag.
- `--max-anyres-num` limits dynamic image patch blocks; lower it if image memory is too high.
- InternVL gradient checkpointing is enabled through model-specific fields, and the trainer may turn off the generic gradient-checkpointing flag afterward to avoid an unsupported operation.

## DeepSpeed selection

- ZeRO-2: lower complexity; commonly paired with LoRA/freeze-vision runs.
- ZeRO-3: better model/reference-model memory partitioning for full fine-tuning; VLM-R1 applies a Qwen2.5-VL forward monkey patch when the DeepSpeed path contains `zero3`.
- ZeRO-3 offload: useful when GPU memory is the blocker, but CPU memory and host bandwidth become the new bottlenecks.

The bundled launcher can resolve `--zero-stage 2`, `--zero-stage 3`, or `--zero-stage 3-offload` to repository-standard relative config locations under the workdir, or accept an explicit `--deepspeed` path.

## Multi-node rendering

Use the renderer to generate one command per node and avoid hand-editing `node_rank`, `master_addr`, and `nnodes`.

```bash
sub-skills/training-workflows/scripts/render_multinode_torchrun.py \
  --hosts train-a=10.0.0.11,train-b=10.0.0.12 \
  --nodes train-a,train-b \
  --master train-a \
  --workdir <open-r1-multimodal-package-root> \
  --script src/open_r1/grpo_jsonl.py \
  --nproc-per-node 8 \
  --arg output_dir=outputs/rl/two-node-rec \
  --arg model_name_or_path=Qwen/Qwen2.5-VL-3B-Instruct \
  --arg data_file_paths=data/refcoco_train.jsonl:data/refcocop_train.jsonl \
  --arg image_folders=images/coco:images/coco \
  --arg task_type=rec \
  --arg is_reward_customized_from_vlm_module=true \
  --arg reward_funcs=accuracy,format \
  --arg deepspeed=local_scripts/zero3.json
```

Validation behavior:

- Every `--nodes` item must exist in the host map.
- If `--master-addr` is omitted, the master node must appear in the host map with an address.
- The renderer assigns ranks by node order and sets `--nnodes` from the number of nodes.
- Add `--ssh` when the rendered output should wrap each per-node command in an `ssh host '...'` prefix.
