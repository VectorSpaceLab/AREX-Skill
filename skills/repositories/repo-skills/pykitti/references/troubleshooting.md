# pykitti troubleshooting

Read this reference when import, layout, dependency, or cross-workflow checks
fail. Detailed route-specific recovery is linked from the corresponding
sub-skill.

## Import and installation

Install the package and its declared dependencies in the same environment used
for the workflow:

```bash
python -m pip install pykitti
python -m pip install opencv-python-headless
python -c "import pykitti; print(pykitti.__file__)"
```

If `import pykitti` reports `ModuleNotFoundError: cv2`, this is the release's
undeclared eager tracking dependency, not evidence that NumPy or Pillow are
missing. Install a compatible OpenCV distribution or, when intentionally
inspecting only source modules, document that top-level import remains
unverified. Do not solve an environment mismatch by adding a checkout to
`PYTHONPATH`.

If `pip check` or metadata inspection fails, use
`scripts/check_install.py --help` and then its normal read-only invocation.
Compare the distribution version and import module before continuing.

## Pick the correct layout

- Raw: `<base>/<date>/<date>_drive_<drive>_<dataset>/` plus date-level
  `calib_*.txt` files.
- Odometry: `<base>/sequences/<sequence>/` with `calib.txt` and `times.txt`,
  plus optional `<base>/poses/<sequence>.txt`.
- Tracking labels: a local label/detection text file or DataFrame; the large
  archive tree is not acquired by this skill.

A missing `calib.txt` or `times.txt` commonly means the wrong root was passed.
Do not substitute a raw tree for an odometry tree or vice versa. Check the route
sub-skill's data-layout reference before changing code.

## Metadata and synchronization

The loaders eagerly parse calibration and timestamps but lazily open images and
Velodyne files. Typical symptoms and actions:

- `KeyError` or reshape errors: inspect required calibration keys and exact
  value counts; do not pad or reorder records silently.
- `ValueError` parsing timestamps/OXTS: repair malformed source records and
  preserve KITTI timestamp precision assumptions.
- `IndexError`: validate `frames` against timestamp, pose, and every intended
  sensor list; selection is positional, not a frame-ID filter.
- Short or empty stereo/scan streams: compare file counts and numeric frame IDs
  before consuming generators; pykitti does not align streams for you.
- Pillow or reshape errors at getter time: check image integrity, `imtype`, and
  Velodyne file size divisibility into float32 groups of four.

Use the route's bundled fixture smoke to isolate package behavior from a large
archive. Do not run the original plotting demos or the repository downloader as
an automated recovery step.

## Tracking compatibility

`KittiTrackingLabels` and `to_array_list` are the preferred tracking surfaces.
The tracking loader itself is incomplete and diagnostic-only in this release.
Modern pandas can expose legacy incompatibilities in `id`, `num_objects`, or
ragged per-frame array conversion. Keep label schemas explicit, use a tiny
fixture first, and pin or adapt dependencies only after confirming the exact
failure. The downloader is intentionally excluded because it performs network
transfers, archive extraction, and file mutation.

## Cross-route recovery

- Raw file/layout/OXTS problem: [raw-data troubleshooting](../sub-skills/raw-data/references/troubleshooting.md).
- Odometry calibration/pose/sequence problem: [odometry troubleshooting](../sub-skills/odometry/references/troubleshooting.md).
- Label schema/pandas/tracking problem: [tracking troubleshooting](../sub-skills/tracking/references/troubleshooting.md).
