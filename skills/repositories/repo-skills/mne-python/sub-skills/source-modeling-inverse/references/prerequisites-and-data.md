# Source Modeling Prerequisites and Data

Read this before promising that a source-modeling workflow can run.
MNE-Python's base package can express many source workflows, but real source
models usually need anatomy, transforms, datasets, and sometimes external tools.

## Required inputs by workflow

| Workflow | Required inputs | Optional/external prerequisites |
| --- | --- | --- |
| Sphere-model forward | `Info`, approximate head model, sensor locations | scientifically acceptable only for simplified checks |
| Surface BEM forward | `Info`, `trans`, surface `src`, BEM solution, subject anatomy | FreeSurfer reconstruction; BEM surfaces; sometimes watershed/flash tools |
| Volume/mixed source space | `Info`, volume/mixed `src`, BEM/sphere, transform | MRI/anatomical labels; memory can be high |
| Minimum-norm inverse | `Evoked`/`Epochs`, `Forward`, noise covariance | sample/testing datasets if using tutorials; rank decisions |
| LCMV beamformer | `Evoked`/`Epochs`, `Forward`, data covariance, optional noise covariance | careful active/baseline windows and rank |
| DICS beamformer | `Forward`, cross-spectral density, frequency bands | time-frequency/CSD computation first |
| Dipole fitting | `Evoked`, covariance, BEM/sphere, `trans` | compact-source scientific assumption |
| Morphing/labels | `SourceEstimate`, source spaces/subjects, labels or annotation | FreeSurfer subjects, template subject, optional MRI files |

## `subjects_dir` and subject identity

- `subjects_dir` points to a directory containing subject subdirectories such
  as `sample`, `fsaverage`, or a participant ID.
- The `subject` string must match the anatomy used for source spaces, BEM, and
  morphing.
- Do not silently mix source spaces, transforms, and BEM files from different
  subjects. If a template is used, record that explicitly.

## Transforms and coordinate frames

A forward solution requires a head↔MRI transform unless the model/API path
explicitly avoids it. Typical failure causes:

- digitization points are missing from `Info`;
- EEG montage was not set before source modeling;
- the transform belongs to another subject/session;
- head/device/MRI coordinate frames are confused;
- bad or non-finite channel locations exist.

Validate the transform and channel locations before heavy computation. If a
user only has EEG sensor locations and no MRI, consider documented EEG-without-
MRI or spherical approaches, but name the scientific limitation.

## Optional external systems

- FreeSurfer: required for many anatomy/surface workflows. It is not installed
  by the base MNE-Python package.
- OpenMEEG: optional BEM solver path for some workflows.
- MNE-C utilities: optional legacy command-line helpers.
- PyVista/Qt/notebook backends: needed for some 3D visualizations, not for the
  source computation itself.
- MNE sample/testing datasets: convenient examples, but may require network and
  cache space. Use no-download checks before assuming they exist.

## Lightweight validation before computation

Use the bundled script:

```bash
python sub-skills/source-modeling-inverse/scripts/source_inputs_check.py \
  --trans sample-trans.fif --src sample-src.fif --bem sample-bem-sol.fif \
  --cov sample-cov.fif --subject sample --subjects-dir subjects
```

The helper does not compute a model. It checks path presence, common suffixes,
subject directory presence, and likely missing prerequisites so a future agent
can ask for the right files instead of starting an expensive failing run.

## When to stop and ask

Ask for missing or ambiguous inputs when:

- the task requires a subject-specific source estimate but no MRI/anatomy or
  transform is available;
- the user expects EEG source localization but only MEG-style one-layer BEM is
  available;
- covariance/rank/projection state is unclear and affects interpretation;
- external binaries or large datasets must be installed/downloaded;
- the user asks for scientific method selection without enough domain context.
