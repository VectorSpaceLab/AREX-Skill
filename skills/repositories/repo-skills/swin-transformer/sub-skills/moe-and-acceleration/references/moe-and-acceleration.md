# MoE and Acceleration Workflows

## Swin-MoE command shape

MoE training/evaluation uses `main_moe.py`, not baseline `main.py`:

```bash
torchrun --nproc_per_node 8 --nnodes <nodes> \
  --node_rank <rank> --master_addr <addr> --master_port 12345 \
  main_moe.py \
  --cfg <swinmoe-config.yaml> \
  --data-path <imagenet22k-root> \
  --batch-size <per-gpu-batch>
```

Evaluation typically uses `--eval --resume <checkpoint-base-path>`. Public MoE checkpoints may be distributed as rank-sharded files; the documented resume path omits rank suffixes so each rank can find its shard.

## Key MoE config fields

- `MODEL.SWIN_MOE.MOE_BLOCKS`: stage/block placement of MoE layers.
- `NUM_LOCAL_EXPERTS`: experts per worker; negative values in provided configs encode distributed expert allocation patterns.
- `TOP_VALUE`: top-k routing.
- `CAPACITY_FACTOR`, `COSINE_ROUTER`, `NORMALIZE_GATE`, `USE_BPR`, `IS_GSHARD_LOSS`: router and load-balancing behavior.
- `AUX_LOSS_WEIGHT`: auxiliary routing loss weight.
- `TRAIN.MOE.SAVE_MASTER`: controls master-only saving in MoE checkpoint utilities.

## Optional fused window process

The optional extension exposes `swin_window_process` and is used only when `--fused_window_process` is passed. Building it requires a CUDA-capable PyTorch environment and a matching CUDA toolkit/compiler. The bundled probe checks importability; it does not build the extension.

## Apex optional acceleration

- `--fused_layernorm` attempts to use Apex `FusedLayerNorm`.
- `--optim fused_adam` and `--optim fused_lamb` require Apex optimizers.
- Missing Apex is not a baseline failure; switch to ordinary AdamW/SGD or install Apex deliberately.

## Backend status checklist

Before relying on these paths, record:

1. PyTorch CUDA availability and device capability.
2. Tutel importability for MoE.
3. Apex importability when using fused ops.
4. `swin_window_process` importability when using fused window process.
5. `nvcc` availability if building the extension from source.
