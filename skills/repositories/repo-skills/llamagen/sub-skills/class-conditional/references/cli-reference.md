# CLI and wrapper reference

All bundled wrappers pin `--gpt-type c2i`; route `t2i` requests to the text-conditional sub-skill instead.

## `scripts/train_c2i.sh`
Wrapper for DDP training.

Required distributed environment variables:
- `nnodes`
- `nproc_per_node`
- `node_rank`
- `master_addr`
- `master_port`

Important forwarded flags:
- `--cloud-save-path`
- `--code-path`
- `--gpt-model`
- `--gpt-ckpt`
- `--gpt-type c2i`
- `--vq-model`
- `--vq-ckpt`
- `--image-size`
- `--downsample-size`
- `--num-classes`
- `--epochs`
- `--lr`
- `--weight-decay`
- `--global-batch-size`
- `--global-seed`
- `--num-workers`
- `--log-every`
- `--ckpt-every`
- `--mixed-precision none|fp16|bf16`
- `--ema`
- `--no-compile`

## `scripts/train_c2i_fsdp.sh`
Wrapper for FSDP training.

Required distributed environment variables:
- `nnodes`
- `nproc_per_node`
- `node_rank`
- `master_addr`
- `master_port`

Important forwarded flags:
- `--cloud-save-path`
- `--code-path`
- `--gpt-model`
- `--gpt-resume`
- `--gpt-type c2i`
- `--vq-model`
- `--vq-ckpt`
- `--image-size`
- `--downsample-size`
- `--num-classes`
- `--epochs`
- `--lr`
- `--weight-decay`
- `--global-batch-size`
- `--global-seed`
- `--mixed-precision fp32|tf32|fp16|bf16`
- `--data-parallel fsdp|sdp|hsdp`
- `--grad-precision fp32|fp16|bf16`
- `--wandb-project`
- `--no-wandb`

## `scripts/sample_c2i.sh`
Wrapper for single-process sampling.

Important forwarded flags:
- `--gpt-model`
- `--gpt-ckpt`
- `--gpt-type c2i`
- `--from-fsdp`
- `--vq-model`
- `--vq-ckpt`
- `--image-size`
- `--downsample-size`
- `--num-classes`
- `--cfg-scale`
- `--cfg-interval`
- `--precision none|fp16|bf16`
- `--compile`
- `--top-k`
- `--top-p`
- `--temperature`

## `scripts/sample_c2i_ddp.sh`
Wrapper for DDP sampling.

Important forwarded flags:
- `--gpt-model`
- `--gpt-ckpt`
- `--gpt-type c2i`
- `--from-fsdp`
- `--vq-model`
- `--vq-ckpt`
- `--image-size`
- `--image-size-eval`
- `--downsample-size`
- `--num-classes`
- `--cfg-scale`
- `--cfg-interval`
- `--sample-dir`
- `--per-proc-batch-size`
- `--num-fid-samples`
- `--global-seed`
- `--precision none|fp16|bf16`
- `--compile`
- `--top-k`
- `--top-p`
- `--temperature`

## `scripts/serve_c2i_vllm.sh`
Wrapper for the vLLM-backed class-conditional path.

Important forwarded flags:
- `--gpt-model`
- `--gpt-ckpt`
- `--gpt-type c2i`
- `--from-fsdp`
- `--vq-model`
- `--vq-ckpt`
- `--image-size`
- `--downsample-size`
- `--num-classes`
- `--cfg-scale`
- `--precision none|fp16|bf16`
- `--compile`
- `--top-k`
- `--top-p`
- `--temperature`

## `scripts/sample_c2i_ddp_pack_npz.py`
- Positional `sample_dir`
- `--num` for the number of PNGs to package
- `--output` to override the output `.npz`

## `scripts/evaluate_c2i.sh`
- Positional `ref_batch`
- Positional `sample_batch`

## Key checkpoint flags
- Use `--from-fsdp` when loading raw consolidated FSDP weights.
- Omit `--from-fsdp` when loading checkpoints that already carry `model`, `module`, or `state_dict`.
- FSDP resume is directory-based; sampling and serving are file-based.
