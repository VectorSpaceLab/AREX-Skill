# Source Modeling Workflows

Read this when a task needs MNE-Python source spaces, BEM/forward models,
inverse estimates, beamformers, dipoles, morphing, or label time courses.

## Stage the file graph first

Before running heavy code, make a table with these fields:

| Need | MNE object/file | Typical producer | Validation |
| --- | --- | --- | --- |
| Sensor metadata | `Info` from `Raw`, `Epochs`, or `Evoked` | I/O and preprocessing sub-skills | channel names/types, bads, projectors, reference, dig/montage |
| Head↔MRI transform | `trans` FIF or transform object | coregistration GUI/CLI or known montage alignment | source/head frames match; EEG electrode digitization exists for EEG |
| Source space | `src` FIF or `SourceSpaces` | `setup_source_space`, `setup_volume_source_space` | subject, spacing, surface/volume, distances as needed |
| Conductivity model | `bem` solution or sphere model | `make_bem_model` + `make_bem_solution`, `make_sphere_model` | conductivity layers match MEG/EEG needs |
| Noise covariance | `Covariance` | empty-room/raw/epochs covariance | rank and projector state match data |
| Forward model | `Forward` | `make_forward_solution` | same `Info`, `trans`, `src`, `bem`; picks match intended sensors |
| Inverse/beamformer | inverse operator or filters | minimum-norm or beamformer APIs | rank/noise/data covariance and orientation decisions documented |

Run `scripts/source_inputs_check.py` to catch missing files and suspicious
extensions before calling computation-heavy APIs.

## Source-space and BEM recipe

1. Confirm `subject` and `subjects_dir`. Do not assume the sample dataset or a
   FreeSurfer reconstruction exists.
2. Choose source space:
   - Surface: `mne.setup_source_space(subject, spacing='oct6', surface='white')`
     for common cortical source estimates.
   - Volume: `mne.setup_volume_source_space(...)` for subcortical/volume work.
   - Mixed: combine surface and volume spaces when both are scientifically
     required.
3. Choose a conductor model:
   - MEG-only can often use single-layer BEM or a sphere model for simpler
     checks.
   - EEG needs a three-layer model when using realistic BEM.
   - OpenMEEG is optional and not part of the base install.
4. Build the forward solution only after transform, source space, BEM/sphere,
   and `Info` are consistent.

Minimal API skeleton:

```python
import mne

src = mne.setup_source_space(subject, spacing='oct6', subjects_dir=subjects_dir)
model = mne.make_bem_model(subject, ico=4, conductivity=(0.3,), subjects_dir=subjects_dir)
bem = mne.make_bem_solution(model)
fwd = mne.make_forward_solution(evoked.info, trans=trans, src=src, bem=bem,
                                meg=True, eeg=False, mindist=5.0)
```

Replace the conductivity and MEG/EEG choices with the actual modality needs.

## Minimum-norm inverse recipe

1. Prepare `Evoked` or `Epochs` from the preprocessing sub-skill. Apply the same
   projectors/references that were used when computing covariance.
2. Compute or load `noise_cov` from empty-room, baseline, or selected epochs.
3. Build the inverse operator with `make_inverse_operator(info, forward,
   noise_cov, loose='auto', depth=0.8, fixed='auto')`.
4. Apply with `apply_inverse(evoked, inverse_operator, lambda2=1 / snr**2,
   method='dSPM' | 'MNE' | 'sLORETA' | 'eLORETA')`.
5. Validate `stc.subject`, vertices, time range, and whether orientation is
   scalar or vector before downstream plotting/statistics.

Common decisions:

- Use `pick_ori=None` for scalar estimates, `'normal'` for surface-normal
  orientation when appropriate, and `'vector'` when downstream code expects
  vector estimates.
- Use labels to restrict output only when anatomical label membership is known.
- Treat `lambda2=1 / snr**2` as an analysis assumption; record the SNR.

## Beamformer recipe

- LCMV uses a data covariance, optional noise covariance, and a forward model.
- DICS uses cross-spectral density (CSD) from time-frequency analysis.
- Always document `rank`, `reg`, `pick_ori`, `weight_norm`, and whether
  covariance/CSD was computed from active vs baseline windows.

```python
from mne.beamformer import make_lcmv, apply_lcmv

filters = make_lcmv(evoked.info, fwd, data_cov, reg=0.05,
                    noise_cov=noise_cov, pick_ori='max-power', rank='info')
stc = apply_lcmv(evoked, filters)
```

## Dipoles, morphing, labels, and source estimates

- Use `fit_dipole` for compact dipolar sources, not extended cortical maps.
- Use `compute_source_morph` or `SourceMorph` when moving source estimates
  between subjects or to a template.
- Use `read_labels_from_annot`, `extract_label_time_course`, and source-space
  adjacency helpers when reducing source estimates to ROIs or statistics.
- Vector, volume, mixed, and surface source estimates have different plotting,
  morphing, and data-shape behavior; check the object type before writing
  generic code.

## Validation checklist

- `info['bads']`, projectors, EEG reference, rank, and covariance are aligned.
- Coordinate frames are named and compatible: head, MRI, surface RAS, device.
- `trans`, `src`, `bem`, and `fwd` belong to the same subject or deliberately
  documented template.
- Optional data/tools are available before promising execution.
- Source estimate dimensions match vertices and time points expected by the
  downstream task.
