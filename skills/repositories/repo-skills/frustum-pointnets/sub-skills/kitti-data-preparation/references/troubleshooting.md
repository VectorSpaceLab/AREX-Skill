# KITTI preparation troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| index id has no image/calibration/Velodyne | wrong dataset root, split, or incomplete download | run the bundled validator with `--check-complete`; correct the layout before conversion |
| labeled branch has no `label_2` | RGB detector input was confused with ground truth | use the RGB branch for unlabeled inference frustums or acquire training labels |
| detector row fails parsing | wrong column count, id, type id, confidence, or box | reject the row; preserve the original detector format and validate finite, ordered coordinates |
| zero points in a frustum | calibration/image coordinates do not match the point cloud or box is out of frame | inspect calibration and frame id; do not fabricate points or labels |
| output pickle is truncated | interrupted multi-GB write or insufficient disk | discard only the known staging file, free space, rerun atomically, and validate object count |
| `cPickle` import fails on Python 3 | legacy import | apply the explicit compatibility import and preserve a documented pickle protocol |
| `scipy.spatial.Delaunay` fails | malformed/degenerate box or incompatible SciPy | validate box geometry and use the pinned legacy-compatible SciPy before changing algorithms |
| preparation pauses at `raw_input` | `--demo` or visualization path was selected | use non-demo generation for automation; run visualization only in an interactive GUI |

The validator is intentionally a preflight, not proof that geometric extraction
matches a benchmark. Compare representative point counts and angles after a
small approved fixture run before committing to the full dataset.
