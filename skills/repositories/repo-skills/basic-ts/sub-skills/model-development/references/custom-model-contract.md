# Custom Model Contract

## Purpose

Read this reference when you are implementing a new BasicTS model class or checking whether an existing class can run inside the BasicTS runner.

## Verified contract summary

The installed runner inspects the model's `forward` signature and only passes keys that the signature accepts.

A canonical BasicTS forward signature looks like this:

```python
def forward(
    self,
    inputs,
    targets=None,
    inputs_timestamps=None,
    targets_timestamps=None,
    inputs_mask=None,
    targets_mask=None,
    epoch=None,
    step=None,
    train=None,
    **kwargs,
):
    ...
```

A model may accept fewer parameters, but `inputs` must be present.

## What the runner passes

From source inspection of `src/basicts/runners/basicts_runner.py`:

- the runner always passes `inputs`
- it passes `targets`, `inputs_timestamps`, `targets_timestamps`, `inputs_mask`, and `targets_mask` only when those keys exist in the batch and the model signature accepts them
- it passes `epoch`, `step`, and `train` only when the model signature accepts them
- during non-training phases, the runner replaces `targets` with an empty tensor before calling the model

## Output contract

A model must return one of the following:

1. a tensor, which BasicTS wraps as `{"prediction": tensor}`
2. a dictionary containing at least `prediction`

Additional keys are preserved and made available to metrics, callbacks, and later pipeline stages.

## Internal loss support

If a model returns a dictionary with `loss`, the runner and callbacks can use that value as the training loss path.

Practical guidance:

- keep `prediction` present even when you compute an internal loss
- return named auxiliary losses separately if you want `AddAuxiliaryLoss` to consume them
- do not hide the main prediction behind a nonstandard key

## Auxiliary-loss pattern

A common pattern is:

```python
return {
    "prediction": prediction,
    "freq_loss": freq_loss,
    "lb_loss": lb_loss,
}
```

Then the config uses `AddAuxiliaryLoss(["freq_loss", "lb_loss"])`.

## Custom model checklist

1. Decide whether the model is forecasting, classification, or reconstruction.
2. Choose a config class that matches the task.
3. Make `forward` accept `inputs`.
4. Add timestamps or masks only when the model needs them.
5. Return a tensor or a dictionary with `prediction`.
6. If you emit auxiliary losses, document the callback needed to consume them.
7. Test the model with a tiny dummy batch before wiring it into a full training run.

## Common wrapper choices

- forecasting-only or forecasting-first families usually use `*ForForecasting` wrappers when they exist
- classification tasks use `*ForClassification`
- imputation or reconstruction tasks use `*ForReconstruction`

## DDP and unused-parameter notes

Some models require special callbacks or DDP settings because parameters are conditionally unused.

- If a model requires a callback, the runner checks `_required_callbacks` and raises an error when the callback is missing.
- If a model leaves parameters unused during a pass, `ddp_find_unused_parameters=True` may be needed.

## Dummy-check recipe

A minimal contract check usually looks like this:

```python
import torch
from basicts.models.DLinear import DLinear, DLinearConfig

cfg = DLinearConfig(input_len=8, output_len=4, num_features=2)
model = DLinear(cfg)
inputs = torch.randn(2, 8, 2)
output = model(inputs)
```

If the model accepts extra keys, pass only the keys that appear in the signature.

## Evidence sources

- `docs/model_design.md`
- `src/basicts/runners/basicts_runner.py`
- installed-package signature inspection in the CPU environment
- smoke-test model families under `tests/smoke_test/`
