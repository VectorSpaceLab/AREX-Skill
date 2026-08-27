# Classification troubleshooting

Evidence labels distilled into this reference: classification source entry points, YACS config defaults, model builder, DCNv3 import surfaces, Hugging Face model card/scripts, and the integration environment report.

## First triage checklist

1. Is the user running the generated command from a real InternImage checkout with `INTERNIMAGE_REPO` set and `cd "$INTERNIMAGE_REPO/classification"` completed?
2. Does the selected config label match the task, model size, and dataset (`imagenet`, `imagenet22K`, or `inat18`)?
3. Is the checkpoint type correct for the argument: `--resume` for evaluation/resume, `--pretrained` for initialization?
4. Is the command launched through a distributed launcher rather than plain `python main.py`? The source `main.py` requires `--local-rank` and initializes NCCL distributed state.
5. Are GPU, PyTorch, CUDA, DCNv3, and optional DeepSpeed/Accelerate/Transformers dependencies installed in the user's runtime environment? The generated skill did not runtime-verify those heavy backends.

## Common failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `error: the following arguments are required: --local-rank` | Running `main.py` or `main_deepspeed.py` directly instead of through the expected distributed launch or Slurm shape | Rebuild the command with `scripts/build_classification_command.py --mode eval|train --launcher launch` or `--launcher srun`. For Slurm, the builder appends `--local-rank 0` like the source shell launchers. |
| `--local_rank` appears but `--local-rank` is still required | Older PyTorch launchers may use underscore spelling while this source parser requires dash spelling | Prefer a PyTorch distributed launcher version that passes `--local-rank`, or use an approved small wrapper/patch in the user's checkout that accepts both spellings before attempting large jobs. |
| NCCL or distributed init hangs | Missing `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, or `MASTER_PORT`; launcher mismatch; blocked port; Slurm environment not propagated | Use the builder's `--master-port` for local launch, avoid plain `python main.py`, and verify scheduler variables for multi-node Slurm. Try a one-GPU launch first. |
| `ModuleNotFoundError: DCNv3` or `No module named 'ops_dcnv3'` | Local classification configs use `CORE_OP: DCNv3` and model modules import the compiled extension path | Route DCNv3 build/diagnosis to deployment. As a classification workaround only for experiments, try `--cfg-option MODEL.INTERN_IMAGE.CORE_OP=DCNv3_pytorch` and treat speed/metric parity as unverified. |
| Build fails with `Cuda is not availabel` or no `nvcc` | Source DCNv3 setup requires CUDA toolkit/compiler compatibility, not just a visible GPU | Route to deployment. Distinguish NVIDIA driver/runtime from toolkit `nvcc`; use a compatible prebuilt wheel only if it matches PyTorch/CUDA. |
| `NotImplementedError: Unkown model` | `MODEL.TYPE` does not exactly match the model builder's lowercase strings | Use a shipped config or set `MODEL.TYPE=intern_image` / `MODEL.TYPE=intern_image_meta_former`. The base default is uppercase and is not a safe standalone config. |
| Validation has zero or wrong classes | Data root does not match expected split layout, or `--dataset` overrides the config incorrectly | For ImageNet use `train/<class>` and `val/<class>` folders. For iNaturalist use the iNat config and `--dataset inat18`. Avoid custom class-count overrides unless the head/checkpoint are adapted. |
| Zipped ImageNet fails to find map files | The zipped path was source-documented but not runtime-verified by this skill, and map filename expectations can differ | Prefer standard folder layout. If the user must use zip mode, ensure the zip files and map text files match the package version and pass `--zip --cache-mode part|full|no`. |
| Checkpoint loads with missing/unexpected keys | Using a pretrained checkpoint with `--resume`, classifier class count mismatch, DeepSpeed checkpoint directory passed to a normal loader, or converted HF naming mismatch | Use `--pretrained` for initialization/fine-tuning and `--resume` for exact resume/eval. For DeepSpeed eval, source code can try fp32 extraction from a ZeRO checkpoint directory. For HF conversion, apply `gamma*` to `layer_scale*` rename and `model.` prefix. |
| `AMP` assertion or mixed-precision failure | `main.py` defaults `--amp-opt-level O1` and asserts native AMP support when not `O0` | Use a supported PyTorch version, or pass `--amp-opt-level O0` for a float32 diagnostic run if memory permits. |
| Out-of-memory on H/G/L/XL | High resolution, large channels/depths, no checkpointing, too-large per-GPU batch, missing DeepSpeed/Accelerate offload | Lower `--batch-size`, add `--use-checkpoint`, increase `--accumulation-steps`, choose DeepSpeed stage 1/2, or use Accelerate ZeRO-3/offload configs. Remember LR scales with global batch and accumulation. |
| Plain DeepSpeed `--zero-stage 3` rejected | Source README examples and source parser disagree; `main_deepspeed.py` accepts only stages 1 or 2 | Use builder `--mode accelerate --accelerate-config configs/accelerate/dist_8gpus_zero3_offload.yaml` for ZeRO-3/offload. |
| Accelerate run writes to an unexpected directory | `main_accelerate.py` appends `_deepspeed` to `OUTPUT` | Include this suffix in experiment tracking and avoid assuming the exact `main.py` output path. |
| Feature extraction saves to an unexpected filename | Source `extract_feature.py --save` derives output from `args.img[:-3] + '.pth'` | Use a simple `.png`/`.jpg` input path or move/rename the saved file after the run. The source script has no explicit output argument. |
| Feature extraction key not found | `--keys` names must match nested module attributes exactly | Start with known keys `patch_embed`, `levels.0.downsample`, or `levels.0.blocks.0.dcn`. For custom keys, inspect the instantiated model in the user's runtime environment, not the generated skill. |
| Hugging Face `trust_remote_code` error | Transformers requires explicit trust for custom InternImage model code | Use `trust_remote_code=True` as in the bundled template after confirming trust policy. |
| Hugging Face download/cache failure | No network, model not cached, wrong model ID, or private cache policy | Pre-cache the model, use a local model directory, or choose one of the published `OpenGVLab/internimage_*` IDs from `references/huggingface.md`. |
| Hugging Face OOM on large models | H/G checkpoints are very large, especially high-resolution classifier variants | Use T/S/B for smoke tests, CPU only for tiny checks, or provision a GPU with enough memory. |

## Safe narrowing strategy

When a user reports a failing large run, narrow in this order:

1. Rebuild the command with the bundled helper and remove unneeded overrides.
2. Switch to a small config (`internimage_t_1k_224`) and one GPU to validate launcher, data, and checkpoint flow.
3. Check dataset folder/JSON layout before changing model settings.
4. If the error is an import/build error, stop trying training flags and resolve environment/DCNv3 first.
5. If the error is OOM, preserve the model/config and reduce per-GPU batch before changing LR-sensitive global batch or accumulation.
6. If the error is DeepSpeed ZeRO-3 related, switch from `deepspeed` mode to `accelerate` mode.

## What not to claim

- Do not claim CPU-only verification of CUDA/DCNv3/TensorRT behavior.
- Do not treat command-builder success as proof that data, checkpoint, or GPU runtime is valid.
- Do not present source top-1 numbers as reproduced unless the user actually ran the corresponding evaluation with the correct checkpoint/data.
- Do not launch full training/evaluation/downloads without explicit user approval for runtime, data, and hardware cost.
