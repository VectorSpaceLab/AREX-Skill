# Checkpoint Workflows

Use this reference to reason about TurboDiffusion checkpoint formats and conversions without running expensive model code by default.

## Format map

| Format / artifact | Where it is used | Notes |
| --- | --- | --- |
| Teacher `.pth` | Public pretrained Wan checkpoints before training | Must be converted to DCP before FSDP training. |
| DCP directory | FSDP/rCM/SLA training load/save format | Pass the DCP directory to `model.config.teacher_ckpt` or to DCP conversion utilities. |
| Training `.pth` after DCP conversion | Post-training merge and inference-export workflows | The bundled DCP-to-PTH utility keeps `net_ema.*` keys and rewrites them to `net.*`. |
| Sharded `.safetensors` with index JSON | External/HF-style DiT checkpoint shards | Convert to a `.pth` state dict before merge/export if the workflow needs PyTorch checkpoint files. |
| Modified inference `.pth` | One-shot inference/serving | Produced by the modify/export path after attention replacement, optional FastNorm, and optional INT8 linear conversion. |

## `.pth` teacher to DCP before training

FSDP2 training expects DCP for the teacher checkpoint. Use PyTorch's DCP format utility:

```bash
python -m torch.distributed.checkpoint.format_utils torch_to_dcp \
  <checkpoint-root>/Wan2.1-T2V-1.3B.pth \
  <checkpoint-root>/Wan2.1-T2V-1.3B.dcp
```

Use the 14B filenames for 14B experiments. Do not pass a `.pth` file to `model.config.teacher_ckpt` for training.

## Training DCP back to `.pth`

The public DCP-to-PTH script loads a DCP checkpoint directory through `torch.distributed.checkpoint.FileSystemReader` and saves a `.pth` file. Its behavior is important:

- Input is a DCP **directory**, commonly the `model` subdirectory under an iteration checkpoint.
- It loads state with PyTorch distributed checkpoint APIs in `no_dist=True` mode.
- It keeps keys that start with `net_ema.`.
- It rewrites `net_ema.` to `net.`.
- Floating tensors are saved in `bfloat16`.
- Non-floating tensors are preserved.

Generic command shape:

```bash
PYTHONPATH=<package-source-dir> python <package-source-dir>/scripts/dcp_to_pth.py \
  --dcp_checkpoint_dir <training-output>/checkpoints/<iteration>/model \
  --save_path <converted-output>/sla_or_rcm_checkpoint.pth
```

Validate that the saved `.pth` contains the expected `net.` keys before using it in merge/export.

## Merge SLA updates into rCM checkpoints

The merge utility performs vector arithmetic:

```text
merged[key] = base[key] + w * (diff_target[key] - diff_base[key])
```

Inputs:

- `--base`: the rCM checkpoint to be updated.
- `--diff_base`: the pretrained/full-attention baseline used as the difference reference.
- `--diff_target`: the SLA-tuned checkpoint.
- `--w`: weight factor, default `1.0`.
- `--output`: destination `.pth`.

Source behavior to preserve in reasoning:

- For tensor keys present in all three inputs with matching shapes, apply the formula in float and cast back to the base tensor dtype.
- Non-tensor keys in the base checkpoint are copied unchanged.
- Tensor keys missing from either difference checkpoint are copied from base.
- Shape mismatches are copied from base and emit warnings in the source utility.
- Keys present only in `diff_target` are added from target.

Because missing or mismatched keys are warning-level behavior, not hard failures, require a key coverage review before considering a merge successful. The bundled [../scripts/tiny_merge_models_check.py](../scripts/tiny_merge_models_check.py) verifies the arithmetic on tiny CPU tensors without using repository code or model checkpoints.

## Sharded safetensors to `.pth`

The safetensors converter expects this layout:

```text
<model-dir>/
  diffusion_pytorch_model.safetensors.index.json
  <one-or-more-shard>.safetensors
```

The index JSON must contain a `weight_map` from parameter names to shard filenames. Conversion behavior:

- Load each referenced tensor on CPU.
- If a parameter name contains `patch_embedding.weight`, reshape the tensor from Conv3d-style weight layout to a 2D linear layout.
- Convert all tensors to `bfloat16`.
- Optionally add a prefix such as `net.` to all output keys.
- Save the merged state dict with `torch.save`.

Use [../scripts/build_safetensors_to_pth_command.py](../scripts/build_safetensors_to_pth_command.py) to render the command. Do not download shards in the runtime skill; the user must supply the model directory.

## Modify/export checkpoints for inference

The modify/export path constructs a Wan model skeleton, loads an rCM/SLA-format state dict, optionally replaces attention and normalization/linear modules, and saves a model `state_dict()` usable by inference or serving.

Supported public model names:

| `--model` | Use case |
| --- | --- |
| `Wan2.1-1.3B` | Wan2.1 text-to-video 1.3B checkpoints. |
| `Wan2.1-14B` | Wan2.1 text-to-video 14B checkpoints. |
| `Wan2.2-A14B` | Wan2.2 image-to-video A14B high/low noise checkpoints. |

Important semantics:

- Input checkpoint is expected to contain a top-level `state_dict` in the rCM/SLA training/export shape.
- Keys with `net.` are loaded into the Wan model after dropping that prefix.
- `patch_embedding.weight` and `patch_embedding.bias` are reshaped if needed to match the target Wan model.
- `--attention_type sla` replaces Wan self-attention local attention with plain SLA.
- `--attention_type sagesla` uses SageSLA and requires the separate SpargeAttn/SageSLA backend.
- `--attention_type original` leaves attention unchanged.
- `--sla_topk` controls the SLA/SageSLA top-k ratio; public examples commonly use `0.2` for export and inference examples often discuss `0.1` to `0.15` quality trade-offs.
- By default the export code replaces LayerNorm/RMSNorm with FastNorm modules. Passing `--default_norm` keeps the default norm modules despite the confusing source help text.
- Passing `--quant_linear` replaces most linear layers with INT8 linear modules, skipping the projection layer named by the source implementation. The conversion uses CUDA/custom ops in real execution.

Use [../scripts/build_modify_model_command.py](../scripts/build_modify_model_command.py) to render a command without executing conversion.

## Quantized versus unquantized contract

- If the exported checkpoint was produced with `--quant_linear`, later inference/serving commands must also include `--quant_linear` so the runtime model structure matches the checkpoint.
- If the checkpoint is unquantized, omit `--quant_linear` in inference/serving.
- Quantized checkpoints are intended for lower-memory consumer/server GPUs; unquantized checkpoints are recommended when sufficient memory is available.
- Quantized export requires CUDA, compiled TurboDiffusion custom ops, and compatible checkpoint shapes; treat failures as acceleration-backend issues after path/model-name checks.

## Wan2.2 I2V high/low noise checkpoints

Wan2.2 A14B I2V uses separate high-noise and low-noise checkpoints. Convert and modify each branch separately, then hand the resulting pair to the inference or interactive-serving workflow. Do not swap the high/low names: a syntactically valid path can still be semantically wrong.

## Non-destructive validation sequence

1. Confirm input files/directories and output parent directories.
2. For DCP, confirm the input path is a directory with DCP metadata rather than a `.pth` file.
3. For `.pth`, load only metadata/key summaries when possible; avoid full GPU model construction.
4. For merge, run the tiny arithmetic check if the user is asking about semantics.
5. For modify/export, render the command and route CUDA/custom-op backend failures to `acceleration-backends`.
6. After export, route actual generation or serving to `video-inference` or `interactive-serving`.
