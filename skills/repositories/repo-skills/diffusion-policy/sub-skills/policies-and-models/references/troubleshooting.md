# Troubleshooting

This guide focuses on policy/model failures: shape mismatches, checkpoint choice, optional dependency imports, and device placement.

## Quick health checks

Run these before a longer debug session:

```bash
python scripts/inspect_policy_interfaces.py
python -c "import diffusion_policy, torch, diffusers; print(diffusion_policy.__name__); print(torch.__version__); print(diffusers.__version__)"
```

If the import check fails, decide whether the missing module is optional for your selected family or whether the environment itself is incomplete.

## Common failure modes

| Symptom | Likely cause | What to check | Fix |
|---|---|---|---|
| `assert Do == self.obs_dim` or similar shape assertion | `shape_meta`, `obs_dim`, or `action_dim` does not match the actual batch | `shape_meta['action']['shape']`, observation key names, `n_obs_steps`, `n_action_steps`, `horizon`, `dataset_obs_steps` | Align the workspace config with the batch layout. For image families, make sure the observation keys and shapes match the encoder inputs exactly. |
| The policy returns the wrong number of action steps | `pred_action_steps_only`, `oa_step_convention`, or the action slice length is inconsistent | Whether the family returns `action` only or both `action` and `action_pred`; whether the metric compares the full horizon or only the executed slice | Compare the same slice the policy actually executes. If `pred_action_steps_only=True`, compare only that slice. |
| `eval.py` gives a different score from training rollouts | EMA and raw weights are being compared inconsistently | Whether `training.use_ema` was enabled in the checkpoint config | `eval.py` chooses `workspace.ema_model` when `training.use_ema: true`; otherwise it uses the raw model. Compare like-for-like. |
| `ModuleNotFoundError` for `robomimic`, `r3m`, or image encoder helpers | Selected an image or hybrid family without its optional vision stack | `robomimic`, `torchvision`, and any R3M/image-backbone extras required by the family | Install the image/robomimic dependencies expected by the family, or switch to a low-dim family that does not need them. |
| `ImportError` or symbol mismatch in `diffusers` / `huggingface_hub` | Package versions drifted apart | Whether `DDPMScheduler`, `EMAModel`, or hub helpers import cleanly | Keep the diffusion stack aligned as a set. The pinned environment uses `torch 1.12.1`, `torchvision 0.13.1`, and `diffusers 0.11.1`; upgrade or downgrade the related packages together. |
| `Expected all tensors to be on the same device` | Policy, scheduler, or batch tensors are split across CPU and GPU | `policy.device`, the batch tensor devices, and `training.device` | Move the policy and every batch tensor to the same device before inference. For manual calls, do `policy.to(device)` and move `obs_dict` tensors to that device first. |
| `CropRandomizer` or image encoder failures during hybrid/image policy creation | The crop size, image size, or encoder settings are inconsistent | `crop_shape`, input image shape, `obs_encoder_group_norm`, `eval_fixed_crop`, and `shape_meta` | Make the crop smaller than the source image and keep the image type metadata in `shape_meta` aligned with the actual tensors. |
| `normalize()` or `unnormalize()` gives strange scales | The policy normalizer was not loaded from the dataset | Whether `set_normalizer()` was called before inference or training-side sampling | Load the dataset normalizer into the policy before calling `predict_action()`. |
| Robomimic wrapper imports fail on startup | Robomimic-specific dependencies are missing | `robomimic`, `obs_utils`, and any image-backbone helper imports | Use a low-dim or diffusion family that does not need the Robomimic stack, or install the Robomimic extras for the selected family. |
| `prediction_type` error from the scheduler | The scheduler config does not match the policy code path | `noise_scheduler.config.prediction_type` | Keep `prediction_type` set to `epsilon` unless you intentionally changed the training target and the scheduler settings together. |

## Useful policy-specific checks

### Low-dim diffusion
- Check whether the policy is using `obs_as_local_cond`, `obs_as_global_cond`, or pure inpainting.
- If the action slice looks shifted, compare `oa_step_convention` with the metrics code.

### Image and hybrid diffusion
- Verify that the observation keys in the batch match the keys in `shape_meta`.
- For hybrid families, verify that Robomimic-style crop and normalization options are compatible with the chosen camera layout.
- If BatchNorm behaves badly at evaluation time, enable `obs_encoder_group_norm` or `eval_fixed_crop` where the family supports them.

### Robomimic and baselines
- `RobomimicLowdimPolicy` and `RobomimicImagePolicy` return one-step actions, not a full diffusion horizon.
- `BETLowdimPolicy` needs its action codebook fitted before training.
- `IbcDfo*` families rely on the candidate pool size and sampling loop; if the selected action looks unstable, inspect `train_n_neg`, `pred_n_iter`, and `pred_n_samples`.

## When to stop and reroute
- If the problem is data layout or ReplayBuffer sampling, hand it to `data-and-replay-buffers`.
- If the problem is command composition, rollout orchestration, or evaluation CLI wiring, hand it to `training-and-evaluation`.
- If the problem is camera, robot, or real-time IO, hand it to `real-robot-operations`.
