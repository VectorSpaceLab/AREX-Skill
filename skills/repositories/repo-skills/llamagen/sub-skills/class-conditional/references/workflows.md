# Workflows

## Decision tree
1. **Training a class-conditional ImageNet model**
   - Use `scripts/train_c2i.sh` for DDP families.
   - Use `scripts/train_c2i_fsdp.sh` for the larger FSDP families.
2. **Sampling images**
   - Use `scripts/sample_c2i.sh` for a single-process sample run.
   - Use `scripts/sample_c2i_ddp.sh` when you want per-rank PNGs and an `.npz` batch.
3. **Serving with vLLM**
   - Use `scripts/serve_c2i_vllm.sh` for the vLLM-backed class-conditional path.
4. **Evaluation**
   - Package a PNG folder with `scripts/sample_c2i_ddp_pack_npz.py`.
   - Evaluate with `scripts/evaluate_c2i.sh` or `python3 evaluations/c2i/evaluator.py`.

## Model-family notes
| Model family | Typical training path | Checkpoint shape | Notes |
| --- | --- | --- | --- |
| GPT-B | DDP | single `.pt` with `model` / `optimizer` / `steps` / `args` | smallest released c2i family |
| GPT-L | DDP | same as GPT-B | standard DDP resume path |
| GPT-XL | DDP | same as GPT-B | appears in README examples |
| GPT-XXL | FSDP | `consolidated.pth` + `optimizer.<rank>.pth` + `resume_step.txt` | use `--from-fsdp` for sampling / serving |
| GPT-3B | FSDP | same as GPT-XXL | largest README-advertised c2i family |
| GPT-XXXL | source code only | not wired in the README serving examples | mention only when the checkpoint and JSON config both exist |

`GPT-7B` and the rest of the text-conditional families are out of scope here.

## Training flow
### DDP
- Entry point: `scripts/train_c2i.sh`.
- Underlying script: `autoregressive/train/train_c2i.py`.
- Requires ImageNet discrete codes under `--code-path`.
- Uses distributed init from `nnodes`, `nproc_per_node`, `node_rank`, `master_addr`, and `master_port`.
- Saves checkpoints with `model`, `optimizer`, `steps`, `args`, and optional `ema`.
- Resume from a `.pt` checkpoint path with `--gpt-ckpt`.

### FSDP
- Entry point: `scripts/train_c2i_fsdp.sh`.
- Underlying script: `autoregressive/train/train_c2i_fsdp.py`.
- Requires the same distributed env vars as DDP.
- Resume from a checkpoint directory with `--gpt-resume`.
- That directory must contain `consolidated.pth`, one optimizer shard per rank, and `resume_step.txt`.
- The resume world size must match the saved optimizer-shard count.

## Sampling flow
### Single process
- Entry point: `scripts/sample_c2i.sh`.
- Underlying script: `autoregressive/sample/sample_c2i.py`.
- Loads a VQ tokenizer checkpoint and a GPT checkpoint.
- Accepts DDP, deepspeed, standard state-dict, or raw FSDP weights via `--from-fsdp`.

### DDP sampling and packaging
- Entry point: `scripts/sample_c2i_ddp.sh`.
- Underlying script: `autoregressive/sample/sample_c2i_ddp.py`.
- Writes numbered PNGs into a sample folder.
- Rank 0 then packages the folder into `<sample_dir>.npz` with `arr_0`.
- The bundled helper `scripts/sample_c2i_ddp_pack_npz.py` can be used separately when packaging needs to be rerun, and it also accepts a sample root that already contains an `images/` subfolder.

## Serving flow
- Entry point: `scripts/serve_c2i_vllm.sh`.
- Underlying script: `autoregressive/serve/sample_c2i.py`.
- Uses the local fake JSON model configs in `autoregressive/serve/fake_json/`.
- Supports the same checkpoint key patterns as sampling; `--from-fsdp` is required for raw consolidated FSDP weights.

## Evaluation flow
- Entry point: `scripts/evaluate_c2i.sh`.
- Underlying script: `evaluations/c2i/evaluator.py`.
- Needs a reference `.npz` and a sample `.npz`.
- The sample `.npz` must expose `arr_0` with NHWC uint8 images.
- The reference `.npz` may also contain cached statistics (`mu`, `sigma`, `mu_s`, `sigma_s`).
