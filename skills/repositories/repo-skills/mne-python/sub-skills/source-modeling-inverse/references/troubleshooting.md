# Source Modeling Troubleshooting

Use this when source-space, forward, inverse, beamformer, or dipole workflows
fail or produce suspicious results.

## Missing anatomy or `subjects_dir`

Symptoms:

- errors mentioning missing subject, surface, BEM, MRI, `SUBJECTS_DIR`, or
  FreeSurfer files;
- `setup_source_space` or BEM functions cannot locate surfaces;
- morphing cannot find source spaces for a subject.

Likely causes:

- no FreeSurfer reconstruction or wrong `subjects_dir`;
- task assumes the MNE sample dataset but it was not downloaded;
- subject name in the code differs from the anatomy directory.

Recovery:

1. Run `source_inputs_check.py` with `--subject` and `--subjects-dir`.
2. Ask for the anatomy root or decide whether a sphere/no-MRI approximation is
   acceptable.
3. Do not proceed with subject-specific claims until subject, transform, source
   space, and BEM provenance are clear.

## Coordinate-frame or transform mismatch

Symptoms:

- forward solution fails with inside/outside, transform, or coordinate-frame
  errors;
- EEG sensors plot far from the head;
- source estimate looks spatially implausible.

Likely causes:

- `trans` belongs to another subject/session;
- montage/digitization was not set before source modeling;
- head/MRI/device frames were mixed;
- EEG channel locations are missing.

Recovery:

1. Inspect `info['dig']`, channel positions, and the transform source.
2. Use MNE coregistration tools or known transforms; do not hand-edit matrices
   unless the user explicitly provides a validated transform.
3. If EEG lacks an MRI, route to documented no-MRI/spherical alternatives and
   name the limitation.

## Rank, covariance, and projector warnings

Symptoms:

- rank mismatch warnings;
- inverse operator construction warns about projectors or covariance;
- beamformer output is unstable or unexpectedly all-zero.

Likely causes:

- covariance computed before/after different bad-channel or projector state;
- EEG reference changed after covariance;
- too few baseline samples;
- incorrect `rank`, `reduce_rank`, or covariance window.

Recovery:

1. Recompute covariance from data with the same bads/projectors/reference state
   as the target evoked/epochs.
2. Use `compute_rank` or `rank='info'` deliberately and record the decision.
3. For LCMV/DICS, document data covariance/CSD windows and regularization.

## External binary or optional solver unavailable

Symptoms:

- errors mentioning FreeSurfer commands, OpenMEEG, watershed/flash tools, or
  missing system executables.

Recovery:

- Decide whether the exact workflow truly requires the external tool. If yes,
  stop and ask for installation/runtime approval or precomputed files.
- If not, choose a base-package alternative such as an existing BEM solution or
  a sphere model, and state the limitations.

## SourceEstimate shape or orientation surprises

Symptoms:

- downstream code expects `(n_vertices, n_times)` but receives vector/volume or
  mixed data;
- `stc.plot` or label extraction fails;
- morphing fails on vertices/subject mismatch.

Recovery:

1. Print `type(stc).__name__`, `stc.data.shape`, `len(stc.vertices)`,
   `stc.times[[0, -1]]`, and `stc.subject`.
2. Check whether `pick_ori='vector'`, volume/mixed source spaces, or morphing
   changed the object class.
3. Route plotting failures to `visualization-reporting` and statistical shape
   issues to `timefreq-stats-decoding-simulation`.

## Expensive or data-dependent examples

Many source examples need sample/testing datasets and can be slow. Do not treat
skipped examples as passes. For operating guidance, use the recipes in this
sub-skill and validate inputs with the bundled helper; run native examples only
when data, external tools, display, and runtime budget are explicitly available.
