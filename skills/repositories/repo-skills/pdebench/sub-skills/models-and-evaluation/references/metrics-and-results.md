# Metrics and result analysis

## Forward metric API

Verified public signatures:

```text
metric_func(pred, target, if_mean=True, Lx=1.0, Ly=1.0, Lz=1.0,
            iLow=4, iHigh=12, initial_step=1)
LpLoss(p=2, reduction="mean")
FftLpLoss(p=2, reduction="mean")
FftMseLoss(reduction="mean")
```

`metric_func` expects a trajectory in dataset layout:
`[batch, x1, ..., xd, time, variables]`. It removes the first
`initial_step` time entries and computes:

1. spatial RMSE,
2. normalized RMSE,
3. RMSE of the conserved-variable sum,
4. maximum pointwise error,
5. boundary RMSE,
6. radial Fourier-space error split into low/middle/high bands.

With `if_mean=True`, it returns six scalar tensors (averaged over batch,
space/variable as implemented). With `if_mean=False`, it returns the
unreduced tensors, retaining channel/time or channel/frequency-band/time
information. `iLow` and `iHigh` are Fourier-band indices, not physical
frequencies. `Lx`, `Ly`, and `Lz` scale Fourier errors; use domain lengths
consistent with the experiment rather than blindly retaining `1.0`.

`LpLoss` computes a relative per-example p-norm after flattening all non-batch
dimensions and then applies `mean`, `sum`, or no reduction. `FftLpLoss`
Fourier-transforms all non-batch dimensions and can restrict the same
frequency interval using `flow`/`fhigh` call arguments. `FftMseLoss` transforms
all dimensions except batch and the final channel-like dimension, then
returns squared complex-difference magnitudes with the chosen reduction.
All three default to the verified `p=2`/`reduction="mean"` combinations.

The higher-level `metrics(...)` helper rolls a U-Net or FNO model over a
validation loader, calls `metric_func`, logs the six values, optionally writes
prediction/data PDFs, and saves a time-MSE `.npz`. Its PINN branch raises
`NotImplementedError`; PINN evaluation uses its own post-training conversion
and direct `metric_func` call in the source trainer.

## Inverse metric API

`inverse_metrics(u0, x, pred_u0, y)` compares the estimated initial field
`u0` with true initial field `x`, and the forward prediction `pred_u0` with
observed/true field `y`. It returns a dictionary containing MSE, L2, L3, and
low/mid/high Fourier variants for both the initial field and prediction, with
keys such as:

```text
mseloss_u0, l2loss_u0, l3loss_u0,
mseloss_pred_u0, l2loss_pred_u0, l3loss_pred_u0,
fftmseloss_{u0,pred_u0}, fftmseloss_{low,mid,hi}_{u0,pred_u0},
fftl2loss_{u0,pred_u0}, fftl2loss_{low,mid,hi}_{u0,pred_u0},
fftl3loss_{u0,pred_u0}, fftl3loss_{low,mid,hi}_{u0,pred_u0}.
```

The inverse code flattens fields for base-space errors and chooses one-quarter
of the spatial extent as the Fourier band width. Preserve the dimensions and
channel semantics when adapting it; a wrong squeeze/reshape can produce
plausible but meaningless numbers.

## Forward pickle and CSV flow

During FNO/U-Net evaluation, the trainer writes the tuple returned by
`metrics` to `<model-name>.pickle` in the active run directory. The forward
analysis program scans `*.pickle`, expands the last Fourier tuple into three
columns, and writes:

- `Results.csv` with a three-level index `(PDE, param, model)` and columns
  `MSE`, `normalized MSE`, `Conservation MSE`, `Maximum Error`, `MSE at
  boundary`, `MSE FT low`, `MSE FT mid`, `MSE FT high`;
- `Results.pdf`, a log-scale MSE bar chart grouped by PDE/model.

The filename parser is part of the contract: keep model/checkpoint pickle
names in the expected underscore-separated PDE naming convention. Run the
analysis from a directory containing only the intended forward pickle files,
and inspect the parsed index before publishing a comparison.

## Inverse CSV/pickle flow

`inverse/train.py` writes one pandas DataFrame per dataset/model/inverse
method as:

```text
<base_path><filename-without-last-five-chars>_<model>_<inverse-type>.csv
<base_path><filename-without-last-five-chars>_<model>_<inverse-type>.pickle
<base_path><filename-without-last-five-chars>_<model>_<inverse-type>_stats.csv
```

The dedicated inverse utilities provide `get_metric_name(...)`,
`read_results(...)`, and `process_results(...)`. `read_results` loads each
pickle, adds `model` and short PDE labels, and concatenates frames.
`process_results` groups selected columns by `(pde, model)`, aggregates mean
and standard deviation, and writes the configured result CSV. The separate
inverse analysis program expects a CSV with a `pde` column, `mean`/`std` rows,
and the final two model columns, then writes `ResultsInverse.pdf` on a log
scale.

## Plotting and comparison discipline

Plotting is opt-in (`plot: false` is the safe default). The forward metrics
plotter writes PDF images and an `*mse_time.npz`; use a non-interactive
Matplotlib backend in headless environments and give each run a separate
output directory. For 2D, the source transposes the displayed spatial slice;
for 3D it does not provide a corresponding plot branch. Compare identical
channel, time-window, spatial-domain, reduction, and Fourier-band settings.

Do not compare a scalar averaged metric from one run with an unreduced
per-channel/per-time array from another. Record whether the target was scaled,
which context was excluded, and whether the error is physical-space or
Fourier-space. MSE/relative-norm values are not evidence that a benchmark was
reproduced unless the same dataset split, checkpoint, config, and metric
arguments were used.
