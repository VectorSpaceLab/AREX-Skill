# Evaluation Troubleshooting and Gates

Use the failure class first. Do not “fix” a missing dataset by silently
switching protocol, and do not turn an import failure into a claimed benchmark
result.

## Gate checklist

| Gate | Read-only check | Blocked consequence |
|---|---|---|
| Dataset | Confirm dataset root, metadata/annotations, JPEGs, and frame/GT counts | Stop production/evaluation; layout-only checks can still run on synthetic files |
| Config/checkpoint | Confirm the requested config and checkpoint are readable and belong to the same NanoTrack variant | Route to inference; no prediction run |
| Python dependencies | Probe PyTorch, OpenCV, NumPy, yacs, tqdm, colorama, Cython, and any wrapper-specific package | Repair an isolated runtime; do not copy historical pins blindly |
| CUDA | Select a free compatible device and run a small model/device smoke check | Stock `bin/test.py` is not a CPU fallback; no full test claim |
| Cython region | Rebuild and import `toolkit.utils.region` for the active interpreter | All VOT overlap imports and `toolkit.evaluation` are blocked |
| Results | Run `check_result_layout.py` before evaluator | Fix paths/rows/counts; no metric claim |
| Workers | Start with `--num 1`, then increase only after one complete case | Diagnose serialization, memory, and path contention before parallelism |
| GUI | Keep `--vis` and `--show_video_level` off on headless hosts unless intentionally supported | Use headless mode or provide a display; do not interpret GUI errors as metric errors |

The inspected preparation facts were: Python 3.13 overlay, PyTorch 2.13.0+cu130,
CUDA preparation smoke passed on an A100 SM80 when a free device was selected,
yacs/Cython/colorama/wget installed, and `pip check` passed. Those facts establish
an environment preparation checkpoint, not complete tracker/evaluator execution.

## Stale or incompatible region extension

The evaluation package imports `toolkit.utils.region` through its package init.
The checkout's prebuilt `region.so` is ABI-incompatible with Python 3.13; an
import failure such as an undefined Python C-API symbol is expected from that
artifact. It must not be used as evidence that evaluation imports.

Build a fresh extension with the bundled [region extension builder](../../../scripts/build_region_extension.py)
in an isolated environment. Pass the active implementation root explicitly;
the default temporary-copy mode does not modify that root:

```bash
python ../../../scripts/build_region_extension.py \
  --repo-root /path/to/selected-implementation-root --json
```

The helper builds and imports `toolkit.utils.region` from the Cython and C
sources. Cython, compiler, Python headers, NumPy ABI, and the interpreter must
belong to the same isolated environment. Use `--in-place` only when mutation of
a disposable source copy is intentional, never on an unrelated Python
installation.

A successful `vot_float2str`/`vot_overlap` smoke test proves only the extension
and its basic call contract. Then import the complete evaluation package in the
same process. Do not use a prebuilt extension from another Python minor version.

## Historical dependencies and current runtime

The historical top-level installer asks for Python 3.8, PyTorch 1.7.0 with
CUDA 10.0, old matplotlib/Pillow, and assorted training/development packages.
Another snapshot pins even older Torch/Cython/OpenCV/NumPy/Shapely versions.
These are compatibility evidence for the old checkout, not a safe modern
installation recipe. In particular:

- do not downgrade an existing working PyTorch/CUDA stack just to reproduce a
  README table;
- install only packages needed by the selected evaluation path;
- check import and native extension ABI after any version change;
- keep training-only packages out of an evaluation-only environment where
  possible;
- if a required old dependency conflicts with the current interpreter, create a
  disposable environment or narrow the claim.

The prepared overlay's `pip check` passed, but package consistency does not
prove that every optional GOT-10k visualization or benchmark import works.
Probe the exact selected branch.

## Dataset and path failures

### `unknown dataset` or missing metadata

Use exact spellings: `GOT-10k`, `VOT2018-LT`, `VOT2018`, `LaSOT`, `OTB100`,
`DTB70`, `UAVDT`, `VisDrone`, `UAV123`, `UAV20L`, `NFS30`, and `NFS240` are
common maintained forms. The test entry point constructs data under
`./datasets/<dataset>` relative to the launch directory. A successful
`DatasetFactory` call requires the matching JSON or scanned-directory layout;
creating an empty directory is not enough.

### First image assertion or OpenCV `None`

A wrapper may open the first image while `load_img=False` is passed. Check that
metadata paths are relative to the dataset root, filenames have the expected
case/zero-padding, and every listed frame exists. For scanned wrappers, check
annotation/image ordering and equal frame/ground-truth counts.

### Empty tracker glob

The evaluator requires at least one directory matching
`<tracker_path>/<dataset>/<tracker_name>*`. Confirm that the result producer's
`--save_path` equals the evaluator's `--tracker_path` parent and that the
tracker directory name is not accidentally nested one level deeper. Run the
bundled checker with the exact tracker directory name, not a shell wildcard.

### Partial `--video` result

`bin/test.py --video NAME` intentionally tracks one sequence. The evaluator
still loads the complete dataset and will report missing files or fail during
metrics. Use the offline checker with one explicit expected sequence for a
single-video smoke, and label it partial; do not report it as a dataset score.

## Result-format failures

Run:

```bash
python /path/to/evaluation/scripts/check_result_layout.py \
  --dataset VOT2018 --results-root ./results --tracker-name nanotrack \
  --json
```

The script is standard-library only and has no original-checkout dependency.
Typical failures:

- OPE file is not exactly `<sequence>.txt`, has a wrong row count, or has a
  malformed/non-finite/nonpositive-size box;
- VOT lacks `baseline/<sequence>/<sequence>_001.txt`, uses a marker outside
  `{0,1,2}`, or emits a restart marker at the wrong position;
- VOT-LT lacks confidence or timing companions, or their row counts differ from
  the trajectory;
- GOT-10k lacks `<sequence>_001.txt`/`<sequence>_time.txt`, has inconsistent
  repetition counts, or stores timing columns that do not match repetitions;
- result root is passed as if it were already the dataset directory, creating a
  duplicated `<dataset>/<dataset>` path.

A validator pass does not prove annotations match, boxes track the target, or
metrics are correct. It proves a bounded text/directory contract only.

## Evaluator dispatch defects

### UAVDT or VisDrone NameError

The standalone evaluator calls `UAVDTDataset` and `VisDroneDataset` but the
inspected import list omits them. If this branch raises `NameError`, preserve the
failure in the run record. In a disposable copied runtime, add the missing
imports, rerun the import and synthetic/layout gates, and identify the patch in
the final report. Do not silently substitute UAV123 or OTB.

### VOT2017 mismatch

The evaluator has a VOT2017 branch, but the maintained factory does not create a
VOT2017 dataset. Confirm a compatible JSON/wrapper before launching. Otherwise
stop with a dispatch block rather than changing the dataset label.

### TrackingNet has no evaluation branch

It is accepted by the factory but falls through the standalone evaluator's
conditional chain. Treat it as unsupported by `bin/eval.py` unless an active
runtime adds and verifies a report path.

### GOT-10k custom result root appears ignored

The GOT branch discovers trackers using the CLI path but constructs
`ExperimentGOT10k` with its default result parent. Check the wrapper's actual
`result_dir` and either place results where that wrapper reads them or patch the
call to pass an explicit result directory. Record this as a path decision.

## VOT and long-term semantic failures

- Do not replace VOT `2`/`0`/`1` markers with zero boxes. The benchmark counts
  failure and skipped frames specially.
- Do not make every frame marker `1`; the stock restart semantics use one
  initialization, boxes during success, `2` on loss, four skipped `0` rows, and
  then reinitialization.
- A VOT trajectory file can be syntactically valid yet have a different number
  of rows from the sequence. Require exact counts when sequence lengths are
  known.
- Long-term F1 requires confidence scores aligned to frames. The first
  confidence row is blank by contract and is later represented as NaN. A missing
  `best_score` stream is a producer bug, not a reason to fabricate scores.
- F1 is threshold-selected; report the selected operating point and do not
  compare it to OPE precision at 20 pixels.

## Multiprocessing, memory, and GUI

The evaluator creates separate pools for OPE success, precision, and normalized
precision, and separate pools for VOT accuracy and EAO. Begin with `--num 1` to
expose path/data errors without worker noise. Increase gradually; each worker
may decode images and hold arrays. Avoid sharing a mutable result directory
between concurrent searches.

`--vis` calls OpenCV window APIs. It can hang or fail under SSH/headless
execution. `--show_video_level` prints tables but does not itself open frames;
keep it off for machine-readable logs. The GOT-10k experiment's plotting path
requires a Matplotlib-capable display/backend only when plots are requested.

## Hyperparameter search failure modes

The search script hard-codes GPU visibility to device `0`; do not assume this is
the free GPU selected by a scheduler. It also contains an undefined `video`
reference inside `run_tracker`, so the historical script is not a verified
launch path. In addition:

- Cartesian trial counts grow multiplicatively; calculate them before launch;
- trial names encode floats and can collide if a naming precision is changed;
- the helper writes `Occ` as an occupancy sentinel; it is not a result;
- random shuffling makes interruption/restart order nondeterministic;
- global config mutation can leak between trials in one Python process;
- search output under VOT/GOT has protocol-specific subdirectories and must be
  validated before evaluation.

Use the search script only after a copied, tested correction, or implement a
small external driver that starts a fresh process per trial and writes a manifest
of config, checkpoint, dataset, device, and result path.

## Claim boundary

During construction there were no datasets or checkpoints, and no complete
tracking/evaluation/export run was claimed. The checkout's prebuilt region
extension was explicitly not accepted as an import proof. Carry these limits
forward unless a later verification record supplies stronger evidence.
