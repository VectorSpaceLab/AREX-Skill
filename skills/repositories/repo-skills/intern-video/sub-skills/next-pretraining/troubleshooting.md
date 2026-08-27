# InternVideo-Next troubleshooting

## Import fails before training starts

- Core model files import `flash_attn`, `FusedMLP`, and `DropoutAddRMSNorm`. A CPU-only environment or a PyTorch/CUDA/FlashAttention mismatch can fail during import, not only during training.
- The FlashAttention wrapper asserts CUDA tensors and half/bfloat16 dtype. If attention fails at runtime, verify tensor dtype/device before changing model flags.
- `timm`, `einops`, `decord`, `torchvision`, DeepSpeed, and teacher-model dependencies must be installed in the same environment.

## Dataset list loads zero samples or crashes

- Check the delimiter. The parser uses `line.split(args.split)`; quoted CSV with spaces is not supported. Use a separator that cannot appear in media paths.
- The multi pretraining loader expects six fields: `source path total_time start_time end_time label`. Missing fields or nonnumeric time fields cause immediate failures.
- `VideoMAE_multi` asserts `use_decord=True`; frame-folder fallback is not implemented for that loader.
- `source == ssv2` changes augmentation behavior. If Something-Something data uses another source string, it may get the wrong flip policy.
- In the inspected snapshot, the multi loader checks an undefined variable named `fname` when choosing the S3/decord path. If a dry loader raises `NameError: fname`, patch the user's working copy to test the constructed video path variable instead, or use an upstream/fixed version.

## Stage1 teacher or losses look wrong

- Stage1 creates an external teacher from `--clip_teacher`; verify the selected factory and teacher weights before launching.
- With `--mask_type attention`, teacher attention is used to build the mask. If teacher attention is unavailable, use a supported mask type (`tube` or `random`) and record the ablation.
- `--clip_loss_ratio` has three components: middle-feature, final-feature, and diffusion loss. Setting a component to zero changes the training objective and should be treated as an ablation.
- `--clip_teacher_final_dim <= 0` disables final-feature distillation in code.

## Stage2 checkpoint mismatch

- The intended recipe loads `--stage1_checkpoint` and reads the `module` key from the checkpoint. If the checkpoint was saved as a raw state dict, remap it before loading.
- Stage2 deep-copies the student into a frozen target encoder and updates it by momentum. If target parameters require gradients or diverge unexpectedly, inspect the copy/freeze step and the momentum update.
- Stage2's `clip_input_frame` passed to the engine comes from `--num_frames`; keep frame counts consistent with JEPA mask expectations.

## DeepSpeed/DDP issues

- If `--enable_deepspeed` is used, the code calls DeepSpeed config helpers and asserts `model.gradient_accumulation_steps() == --update_freq`.
- If DeepSpeed is not used and distributed mode is enabled, standard DDP wraps the model with `find_unused_parameters=False`; unused branches from ablation flags can produce DDP errors.
- Do not set `--num_workers 0` casually: the DataLoader is constructed with persistent workers in the inspected code path, and zero workers may require a local code adjustment depending on PyTorch version.

## OOM or unstable losses

- Reduce `--batch_size`, `--num_frames`, `--input_size`/teacher resolution, model size, or disable unnecessary repeated samples before changing the objective.
- Enable gradient checkpointing flags (`--use_checkpoint`, `--checkpoint_num`) only after confirming the selected model supports the desired setting.
- The stage1 engine skips iterations if gathered losses contain NaN/Inf. Treat repeated skips as a data/model objective problem, not success.
- Long runs save `latest` checkpoints each epoch when `--output_dir` is set; ensure storage capacity before scheduling.

## Ceph/S3 paths do not work

- Source loaders optionally use Petrel/Ceph clients. If the environment lacks the client or config, prefer local media paths for validation.
- Do not rely on user-private object storage defaults. Require explicit user-provided storage config and credentials before running remote-data jobs.
