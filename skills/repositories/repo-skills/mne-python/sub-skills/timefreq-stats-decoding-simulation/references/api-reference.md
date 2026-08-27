# Analysis API Reference

Use this for verified signatures and input/output notes for time-frequency,
statistics, decoding, and simulation workflows.

## Time-frequency and spectrum APIs

```python
mne.time_frequency.tfr_morlet(inst, freqs, n_cycles, use_fft=False,
                              return_itc=True, decim=1, n_jobs=None,
                              picks=None, zero_mean=True, average=True,
                              output='power', verbose=None)

mne.time_frequency.psd_array_welch(x, sfreq, fmin=0, fmax=inf, n_fft=256,
                                   n_overlap=0, n_per_seg=None, n_jobs=None,
                                   average='mean', window='hamming',
                                   remove_dc=True, *, output='power',
                                   verbose=None)
```

Object methods such as `raw.compute_psd()` and `epochs.compute_psd()` return
Spectrum-like MNE objects. Use `.get_data(return_freqs=True)` when you need
arrays and frequency values.

Parameter notes:

- `inst` for TFR can be `Epochs` or `Evoked` depending on the function; inspect
  whether trialwise output is needed.
- `freqs` and `n_cycles` must be compatible with epoch duration.
- `average=False` keeps individual trials for later statistics.
- Welch parameters depend on sample count; `n_fft` cannot exceed segment length
  unless data is padded as documented by MNE.

## Statistics APIs

```python
mne.stats.permutation_cluster_test(X, threshold=None, n_permutations=1024,
                                   tail=0, stat_fun=None, adjacency=None,
                                   n_jobs=None, seed=None, max_step=1,
                                   exclude=None, step_down_p=0, t_power=1,
                                   out_type='indices', check_disjoint=False,
                                   buffer_size=1000, verbose=None)
```

Common related functions include `permutation_cluster_1samp_test`,
`spatio_temporal_cluster_test`, `fdr_correction`, `bonferroni_correction`,
`linear_regression`, and adjacency helpers exposed from `mne`/`mne.stats`.

Parameter notes:

- `X` is a list/tuple of condition arrays for between-condition cluster tests.
  Check axis order before building adjacency.
- `tail` and `threshold` encode the hypothesis direction and clustering rule.
- Use `seed` for reproducible tests and examples.
- `out_type='indices'` is usually easier for programmatic follow-up.

## Decoding APIs

```python
mne.decoding.CSP(n_components=4, reg=None, log=None, cov_est='concat',
                 transform_into='average_power', norm_trace=False,
                 cov_method_params=None, *, restr_type='restricting',
                 info=None, rank=None, component_order='mutual_info')

mne.decoding.SlidingEstimator(base_estimator, scoring=None, n_jobs=None,
                              *, position=0, allow_2d=False, verbose=None)
```

Many decoding classes import scikit-learn. If `sklearn` is missing, install the
appropriate optional dependency path or avoid decoding workflows.

Input notes:

- Decoding arrays are commonly `(n_epochs, n_channels, n_times)` for epoched
  sensor data.
- Scikit-learn estimators expect samples on axis 0. MNE estimators adapt time or
  source dimensions but still need labels aligned with epochs.
- Put preprocessing/scaling/CSP inside a scikit-learn pipeline for
  cross-validation.

## Simulation APIs

```python
mne.simulation.simulate_raw(info, stc=None, trans=None, src=None, bem=None,
                            head_pos=None, mindist=1.0, interp='cos2',
                            n_jobs=None, use_cps=True, forward=None,
                            first_samp=0, max_iter=10000, verbose=None)
```

For lightweight sensor-space fixtures, `mne.create_info` and `mne.io.RawArray`
are usually simpler than full source simulation. Full source simulation needs
source-modeling inputs such as `src`, `bem`, `trans`, or a precomputed
`forward`.

## Shape conventions to verify

| Object/API | Common shape | Notes |
| --- | --- | --- |
| `Raw.get_data()` | `(n_channels, n_times)` | continuous data |
| `Epochs.get_data()` | `(n_epochs, n_channels, n_times)` | labels/events align with first axis |
| `Evoked.data` | `(n_channels, n_times)` | averaged data with `nave` |
| PSD array helper | depends on input plus frequency axis | inspect returned `freqs` |
| TFR | epochs/channels/frequencies/times or average | average/trialwise changes axes |
| Source estimate | `(n_vertices, n_times)` or vector/volume variants | object class matters |

Always print or assert shapes before writing downstream statistics or decoding
code.
