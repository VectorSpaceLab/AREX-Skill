# Torch backend and training guidance

## Install and import checks

```bash
pip install "darts[torch]"
python - <<'PY'
import torch
import pytorch_lightning as pl
from darts.models import TCNModel
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
print(TCNModel)
PY
```

If GPU execution is required, install a torch wheel that matches the device backend and verify an actual Darts trainer run on that device. Do not use CPU torch import as proof of CUDA/ROCm/MPS/TPU readiness.

## CPU-safe trainer kwargs

Use CPU-safe trainer kwargs for tiny prototypes and automated checks:

```python
pl_trainer_kwargs = {
    "accelerator": "cpu",
    "devices": 1,
    "enable_progress_bar": False,
    "enable_model_summary": False,
    "logger": False,
}
```

Keep `n_epochs`, `batch_size`, and model dimensions small for a smoke. Use a temporary or explicit work directory for checkpoints/logs.

## Chunk lengths

Torch forecasting models use chunk lengths. Common parameters include:

- `input_chunk_length`: how much history the model consumes.
- `output_chunk_length`: how many future steps are predicted per forward pass or training sample.
- `output_chunk_shift`: model-specific shift between input and output windows.

Validate that the target series is long enough for the chosen chunks and that covariates cover the historical/future ranges implied by those chunks.

## Checkpoint discipline

Darts torch models can create logs/checkpoints. For agent-generated examples:

- Prefer `save_checkpoints=False` in tiny smokes.
- Use `work_dir=tempfile.mkdtemp()` or a user-approved output path.
- Never write checkpoints inside the runtime skill directory.
- Clean temporary directories after smoke checks unless the user asked to keep artifacts.

## GPU/TPU escalation checklist

Before claiming accelerator success:

1. Confirm hardware visibility (`nvidia-smi`, `torch.cuda.is_available()`, or backend-specific probe).
2. Confirm installed torch wheel matches the backend runtime.
3. Run a tiny Darts model with backend trainer kwargs, not only a torch tensor allocation.
4. Record memory/device constraints and fall back to CPU only if the user accepts a CPU-scope answer.

## Baseline verification boundary

The baseline skill verification passed CPU torch import and a tiny one-epoch CPU `TCNModel` smoke. CUDA, ROCm, MPS, TPU, and foundation model weight execution remain unverified optional capabilities.
