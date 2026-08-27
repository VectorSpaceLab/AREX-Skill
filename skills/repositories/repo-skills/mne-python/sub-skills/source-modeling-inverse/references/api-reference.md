# Source Modeling API Reference

Use this reference for verified signatures and decision notes. Signatures were
checked against the installed MNE-Python package used during skill creation.

## Source spaces and conductor models

```python
mne.setup_source_space(subject, spacing='oct6', surface='white',
                       subjects_dir=None, add_dist=True, n_jobs=None,
                       *, verbose=None)
mne.make_bem_model(subject, ico=4, conductivity=(0.3, 0.006, 0.3),
                   subjects_dir=None, verbose=None)
mne.make_forward_solution(info, trans, src, bem, meg=True, eeg=True,
                          *, mindist=0.0, ignore_ref=False, n_jobs=None,
                          on_inside='raise', verbose=None)
```

Decision notes:

- `spacing='oct6'` is common for surface estimates; denser spacing increases
  runtime and memory.
- `conductivity=(0.3,)` is common for single-layer MEG BEM; EEG generally needs
  three layers such as `(0.3, 0.006, 0.3)`.
- `mindist` excludes sources too close to the inner skull surface; increasing it
  can reduce unrealistic sources but changes the source space.
- `on_inside='raise'` catches head/model inconsistencies rather than silently
  continuing.

## Minimum-norm inverse

```python
from mne.minimum_norm import make_inverse_operator, apply_inverse

make_inverse_operator(info, forward, noise_cov, loose='auto', depth=0.8,
                      fixed='auto', rank=None, use_cps=True, verbose=None)
apply_inverse(evoked, inverse_operator, lambda2=0.1111111111111111,
              method='dSPM', pick_ori=None, prepared=False, label=None,
              method_params=None, return_residual=False, use_cps=True,
              verbose=None)
```

Decision notes:

- `lambda2` is usually `1 / snr**2`; the default corresponds to SNR 3.
- `method` can be `'MNE'`, `'dSPM'`, `'sLORETA'`, or `'eLORETA'` depending on
  normalization needs.
- `loose`, `fixed`, and `pick_ori` control orientation constraints and output
  type. Record choices because downstream source-estimate interpretation changes.
- `rank='info'` or an explicit rank can prevent covariance/rank mismatch; do
  not ignore rank warnings without checking projectors and bad channels.

## Beamformers

```python
from mne.beamformer import make_lcmv, apply_lcmv, make_dics, apply_dics

make_lcmv(info, forward, data_cov, reg=0.05, noise_cov=None, label=None,
          pick_ori=None, rank='info', weight_norm='unit-noise-gain-invariant',
          reduce_rank=False, depth=None, inversion='matrix', verbose=None)
```

The installed signature for `make_lcmv` above is the main entry point for LCMV
filters. DICS uses CSD rather than a time-domain data covariance; route CSD
creation to the time-frequency/statistics sub-skill.

Decision notes:

- `data_cov` must represent the activity window used by the beamformer; for
  contrasts, compute compatible active and baseline estimates.
- `pick_ori='max-power'` is common for scalar LCMV output; vector choices change
  output dimensionality.
- `reduce_rank` and `rank` are critical for MEG/EEG rank-deficient data.

## Source estimate and label utilities

Common public classes/functions include:

- `SourceEstimate`, `VectorSourceEstimate`, `VolSourceEstimate`,
  `MixedSourceEstimate`, and their vector variants.
- `read_source_estimate`, `stc_to_label`, `extract_label_time_course`,
  `compute_source_morph`, `read_labels_from_annot`, `morph_labels`,
  `spatio_temporal_src_adjacency`.

Operational notes:

- Check `stc.vertices`, `stc.times`, `stc.subject`, and the class name before
  choosing plotting, morphing, or statistics code.
- Label time courses depend on the label mode and sign-flip strategy; document
  `mode`, `allow_empty`, and whether labels match source-space vertices.
- Source-space adjacency functions are needed for cluster statistics on source
  estimates; route statistical inference to the analysis sub-skill after
  adjacency is built.

## Dipoles and sparse inverses

- `fit_dipole` expects an evoked response, covariance, BEM/sphere, and transform;
  it estimates compact dipolar sources rather than distributed maps.
- Sparse inverse methods live under `mne.inverse_sparse`; use them when the task
  explicitly asks for mixed-norm/gamma-MAP/sparse solvers and record additional
  assumptions.

## Safe inspection pattern

When writing code for a user, prefer an early validation block:

```python
for name, value in {'trans': trans, 'src': src, 'bem': bem}.items():
    if value is None:
        raise ValueError(f'Missing source-modeling input: {name}')
print(evoked.info['ch_names'][:5], evoked.info['bads'])
```

Then call MNE APIs only after all inputs and optional prerequisites are known.
