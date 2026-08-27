# Model Architecture Troubleshooting

## Missing `torch` or `model` imports

Symptoms:

- `ModuleNotFoundError: No module named 'torch'`
- bundled runtime import errors from a copied or incomplete skill directory

Actions:

1. Install or activate a Python environment with PyTorch.
2. Run scripts from inside a complete generated `u-2-net` skill tree so root `scripts/u2net_runtime.py` is present.
3. If validating a separate source checkout, use the root environment checker with `--repo-root` only as an explicit user-supplied validation target.

## Checkpoint key or shape mismatch

Symptoms:

- `Missing key(s) in state_dict`
- `Unexpected key(s) in state_dict`
- tensor size mismatch for convolution weights

Likely causes and checks:

1. Wrong variant: `u2net.pth`, `u2net_human_seg.pth`, and `u2net_portrait.pth` use `U2NET(3,1)`; `u2netp.pth` uses `U2NETP(3,1)`.
2. DataParallel prefix: strip leading `module.` keys before loading.
3. Wrapped checkpoint: unwrap `state_dict` or `model_state_dict` when present.
4. Original vs refactored implementation: verify key names before loading original weights into `U2NET_full()` or `U2NET_lite()`.
5. Output-channel mismatch: official masks use `out_ch=1`.

Do not set `strict=False` until the variant and prefix issues are understood.

## CUDA confusion

Symptoms:

- `Torch not compiled with CUDA enabled`
- `--device cuda was requested, but torch.cuda.is_available() is False`
- out-of-memory errors on full `U2NET`

Actions:

- Use `--device cpu` for architecture smoke tests.
- Use `--device auto` for helpers when CUDA is helpful but not required.
- For a CUDA-only user request, first prove `torch.cuda.is_available()` in that environment.
- If full `U2NET` is too large, smoke-test with `U2NETP` or reduce input size; do not claim a full pretrained inference result from a random-weight smoke run.

## Deprecated upsample warning

Symptoms:

- Warning that `nn.functional.upsample` is deprecated.

Action: treat it as a compatibility warning for modern PyTorch, not as a failing gate. If code is edited to use `interpolate`, re-run `scripts/smoke_architecture.py` and any selected inference smoke tests.

## Unexpected number or order of outputs

Official original classes return seven outputs. The first output is the fused prediction. If a custom wrapper returns a single tensor or changes order, update downstream inference code deliberately and do not mix it with repository checkpoints without validation.
