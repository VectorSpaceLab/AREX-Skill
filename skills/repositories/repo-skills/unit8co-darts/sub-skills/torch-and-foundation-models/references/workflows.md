# Torch workflows

## Tiny CPU TCNModel smoke

```python
import tempfile
import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.models import TCNModel

series = TimeSeries.from_times_and_values(
    pd.date_range("2024-01-01", periods=36, freq="D"),
    np.sin(np.arange(36) / 3.0),
)
with tempfile.TemporaryDirectory(prefix="darts-torch-") as work_dir:
    model = TCNModel(
        input_chunk_length=12,
        output_chunk_length=3,
        n_epochs=1,
        batch_size=4,
        random_state=42,
        save_checkpoints=False,
        force_reset=True,
        work_dir=work_dir,
        pl_trainer_kwargs={
            "accelerator": "cpu",
            "devices": 1,
            "enable_progress_bar": False,
            "enable_model_summary": False,
            "logger": False,
        },
    )
    model.fit(series, verbose=False)
    forecast = model.predict(3)
    assert len(forecast) == 3
```

For automated checks, prefer the bundled `scripts/torch_model_smoke.py --train`.

## Neural covariates workflow

1. Build target and covariates with `time-series-and-data`.
2. Fill/scale and validate spans with `data-processing-and-covariates`.
3. Choose a torch model whose class supports the requested covariate type.
4. Configure chunk lengths and tiny trainer kwargs first.
5. Evaluate output in `evaluation-and-explainability`.

Do not skip covariate span validation. Neural chunk windows often require more history/future coverage than a basic one-step example.

## Staged CPU → GPU escalation

- Stage 1: pass CPU import and `torch_model_smoke.py` construction.
- Stage 2: pass tiny CPU `--train` smoke.
- Stage 3: install/verify backend-specific torch wheel and hardware.
- Stage 4: run the same tiny Darts model with GPU trainer kwargs.
- Stage 5: only then scale series length, model dimensions, or epochs.

## Foundation no-network plan

Before constructing foundation wrappers:

```python
import importlib.util
for name in ["torch", "huggingface_hub", "neuralforecast", "tirex"]:
    print(name, bool(importlib.util.find_spec(name)))
```

Then require one of:

- user-approved network download;
- explicit local model/cache path;
- a pre-provisioned environment documented by the user.

If none is available, provide planning guidance but do not instantiate the wrapper or claim inference was tested.
