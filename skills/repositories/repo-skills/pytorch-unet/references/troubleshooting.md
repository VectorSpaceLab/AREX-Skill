# Cross-cutting troubleshooting

Use this reference when a Pytorch-UNet issue spans installation, imports, runtime dependencies, backend selection, credentials, or route choice.

## Import or packaging failure

### Symptom
`ModuleNotFoundError: No module named 'unet'` or imports work only from the repository root.

### Likely cause
Pytorch-UNet exposes top-level packages but does not include packaging metadata in the checkout. It is often used by running scripts from the checkout root rather than installing a distribution.

### Recovery
- Run scripts from a checkout root that contains `unet/`, `utils/`, `train.py`, and `predict.py`.
- Or set `PYTHONPATH`/package the checkout in a controlled project environment.
- Bundled helper scripts support `--repo-root` where import from a checkout root is needed.

## PyTorch or torchvision missing

### Symptom
Imports fail for `torch`, `torchvision`, or CUDA symbols.

### Likely cause
The core model and scripts require PyTorch. Training imports `torchvision.transforms`; prediction and data code require Pillow/NumPy; training imports W&B.

### Recovery
Install a PyTorch build compatible with the desired CPU/CUDA backend, then install the repository requirements. Verify with the root `scripts/check_environment.py` and the model/prediction smoke helpers.

## Old W&B dependency behavior

### Symptom
`wandb` import fails with a `pkg_resources` error or W&B logging fails in offline environments.

### Likely cause
The documented `wandb==0.13.5` is old and expects setuptools' `pkg_resources` module. Training also initializes W&B by default.

### Recovery
- Ensure setuptools compatibility if using the pinned W&B version.
- Configure W&B offline/disabled behavior externally when network is not available.
- Use parser/help and bundled smoke checks for non-training validation.

## CUDA availability confusion

### Symptom
README suggests CUDA/AMP, but the task only needs import, model shape, data validation, or a tiny prediction check.

### Likely cause
CUDA is recommended for efficient training, not required for all workflows.

### Recovery
Use CPU for safe functional checks. Require CUDA only when the user asks for GPU training/performance evidence or when running a full training scenario that cannot fit CPU time budgets.

## Credentials or network required

### Symptom
Data download or pretrained torch.hub loading asks for credentials, downloads from Kaggle/GitHub, or fails in offline mode.

### Likely cause
Carvana data and pretrained weights are external artifacts.

### Recovery
- Ask for explicit approval before running network/credentialed commands.
- Prefer local user-provided data and checkpoints when possible.
- Use `pretrained=False` for architecture-only torch.hub use.

## Choosing the right sub-skill

- Model object, checkpoint shape, bilinear, channel/class, hub model: `model-api`.
- Dataset layout, training command, W&B, checkpoints from training, data validation: `data-training`.
- `predict.py`, output masks, Dice/evaluate, palette conversion, visualization: `prediction-evaluation`.

If a failure crosses routes, start from the user-visible symptom and then follow the cross-link: a prediction checkpoint mismatch usually starts in `prediction-evaluation` but may need `model-api`; a wrong class count during evaluation usually starts in `data-training` mask values and then affects prediction/evaluation.
