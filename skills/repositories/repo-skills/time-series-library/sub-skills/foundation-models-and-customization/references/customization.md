# Custom Models, Scripts, and Augmentation

## Adding a custom model

1. Create `models/<YourModel>.py` in the TSLib checkout.
2. Expose `class Model(nn.Module)` or a class named `YourModel`.
3. Accept the parsed `configs` namespace in `__init__` and store task-specific fields such as `task_name`, `seq_len`, `pred_len`, `enc_in`, and `c_out`.
4. Implement the relevant `forward(x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None)` task branch.
5. Run an import/shape smoke before launching a benchmark.

Minimal long-term forecast shape contract:

```python
class Model(nn.Module):
    def __init__(self, configs):
        super().__init__()
        self.task_name = configs.task_name
        self.pred_len = configs.pred_len
        self.proj = nn.Linear(configs.enc_in, configs.c_out)

    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None):
        if self.task_name in {"long_term_forecast", "short_term_forecast"}:
            return self.proj(x_enc[:, -self.pred_len:, :])
        raise ValueError(f"unsupported task {self.task_name}")
```

Use this only as a contract illustration; real models should follow the intended architecture.

## Adding scripts

Upstream contribution guidance expects a new model to include matching scripts under `scripts/`. For a reusable script:

- Start from a known task folder (`long_term_forecast`, `short_term_forecast`, `imputation`, `anomaly_detection`, `classification`, or `exogenous_forecast`).
- Keep dataset paths and GPU ids easy to edit.
- Include a small smoke variant or document how to reduce epochs/windows.
- Avoid hard-coding a GPU id that will silently select the wrong device on other machines.

## Using augmentation flags

`run.py` includes `--augmentation_ratio` plus method flags:

```text
--jitter --scaling --permutation --randompermutation --magwarp --timewarp
--windowslice --windowwarp --rotation --spawner --dtwwarp --shapedtwwarp
--wdba --discdtw --discsdtw
```

Guidelines:

- Start with `--augmentation_ratio 1` and one method.
- DTW-guided methods are slower and can be class-label dependent.
- Use fixed seeds and identical train/test splits when comparing augmentation effects.
- Validate batch shapes before combining several augmentation flags.

## Contribution expectations

The upstream contribution notes ask contributors who add a model to:

- Open an issue describing the model, paper, and official code.
- Submit a pull request in the existing TSLib style.
- Add a model file under `models/` and corresponding reproduction scripts.
- Prefer officially published papers as additions.

For private or experimental use, you can still add local model files, but do not assume upstream will accept unpublished baselines.

## Safe validation sequence for a new model

1. `python sub-skills/foundation-models-and-customization/scripts/inspect_tslib_models.py --repo-root /path/to/checkout --models YourModel`
2. Run `python run.py --help` from the checkout.
3. Use a tiny `custom` CSV and a short CPU command.
4. Check output shape and loss for one batch/epoch.
5. Only then port benchmark-scale settings from an existing script.
