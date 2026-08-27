# Analysis Troubleshooting

Use this when spectra, TFR, statistics, decoding, or simulation workflows fail.

## Frequency and epoch-length errors

Symptoms:

- errors about `n_fft`, segment length, or frequency resolution;
- empty frequency ranges;
- TFR looks smeared or impossible at low frequencies.

Likely causes:

- epoch duration is too short for requested frequencies or cycles;
- `fmax` exceeds Nyquist (`sfreq / 2`);
- `n_fft`/`n_per_seg` exceed available samples for Welch;
- decimation is applied before validating time resolution.

Recovery:

1. Print `sfreq`, number of time samples, time range, and desired frequency
   range.
2. Lower `fmin`, reduce `n_cycles`, lengthen epochs, or change method only when
   scientifically acceptable.
3. For smoke checks, use small valid ranges such as 1-40 Hz on 100 Hz synthetic
   data.

## Shape and axis mismatch

Symptoms:

- cluster/stat functions reject arrays;
- decoding labels do not match samples;
- plots/statistics appear transposed.

Recovery:

- Assert array shapes before fitting/testing.
- Keep observations on axis 0 for statistics and scikit-learn.
- For MNE `Epochs`, labels/events align with `epochs.get_data().shape[0]`.
- Rebuild adjacency after channel picking, frequency selection, or source-space
  changes.

## Baseline and output interpretation

Symptoms:

- TFR values are unexpectedly negative or huge;
- condition comparisons disagree after baseline correction;
- PSD units are unclear.

Recovery:

1. Record TFR `output` and baseline `mode`.
2. Apply the same baseline window/mode across comparable conditions.
3. Keep linear power, log-ratio, percent, and z-score outputs separate in
   variable names and reports.

## Cluster/statistical pitfalls

Symptoms:

- no clusters found;
- all clusters nonsignificant;
- p-values change across runs;
- memory/runtime is excessive.

Recovery:

- Set `seed` for reproducibility.
- Use tiny permutations only for code checks; do not interpret them
  scientifically.
- Check `tail`, threshold, adjacency, and observation count.
- Reduce dimensions or use sparse adjacency for large source/time-frequency
  grids.
- If data are not exchangeable under the null, choose a different statistical
  design.

## Missing scikit-learn or decoding failures

Symptoms:

- `ModuleNotFoundError: No module named 'sklearn'`;
- `CSP`/`SlidingEstimator` import or pipeline creation fails;
- cross-validation score is suspiciously perfect.

Recovery:

1. Install `scikit-learn` or an MNE full optional dependency set if decoding is
   truly required.
2. Put all preprocessing/scaling/CSP/feature selection inside a pipeline.
3. Use cross-validation splits that respect subjects, runs, or time if leakage
   is possible.
4. Compare with a chance-level baseline and inspect label balance.

## Simulation prerequisites

Symptoms:

- `simulate_raw` asks for `src`, `bem`, `trans`, or `forward`;
- source simulation is slow or fails before data are created.

Recovery:

- Use `RawArray` for simple sensor-space fixtures.
- Build/validate source-modeling inputs with `source-modeling-inverse` before
  using full source simulation.
- Keep random seeds and generated dimensions small in tests/examples.

## Optional data and long examples

Many MNE examples use sample/testing datasets and can download data or run for a
long time. Do not treat skipped examples as passing. Use bundled synthetic
helpers for code-path verification, and only run native examples when data,
network/cache, optional dependencies, and runtime budget are available.
