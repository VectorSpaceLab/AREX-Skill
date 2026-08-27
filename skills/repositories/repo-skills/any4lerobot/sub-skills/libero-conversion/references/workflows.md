# LIBERO workflow recipes

## 1. Inventory and preflight

Accept one or more source directories. The converter's task loader scans each
source directory's immediate children with the glob `*.hdf5`; it does not
recursively discover nested task files. Record the resolved directory list and
sort or otherwise freeze the file order before a run so that a resume has the
same task set.

Supported filename extraction is equivalent to these ordered patterns:

1. `_SCENE<digits>_<task>_demo.hdf5`
2. `<task>_demo.hdf5`

The extracted task text has underscores replaced by spaces. A file matching
neither pattern is skipped, not assigned an arbitrary task name. Inspect the
skipped list before proceeding. The task metadata is attached to every frame
from that HDF5 task file.

Use a read-only preflight to check:

- the file opens and contains a `data` group;
- each member of `data` is a demo group, preferably with a stable name such as
  `demo_0`;
- every demo contains `obs/agentview_rgb`, `obs/eye_in_hand_rgb`,
  `obs/ee_states`, `obs/joint_states`, `obs/gripper_states`, and `actions`;
- all required arrays have the same leading frame count;
- images are RGB arrays with shape `(T, 256, 256, 3)` and an appropriate
  unsigned 8-bit or otherwise explicitly supported image dtype;
- state/action arrays are numeric, finite, and have widths 6, 7, 2, and 7 for
  ee state, joint state, gripper state, and action respectively.

A preflight that sees empty demos, missing keys, inconsistent `T`, NaNs, or a
non-RGB image should stop before invoking the converter. Do not repair source
files in place during this check.

## 2. Core conversion plan

The source HDF5 contract is described in [data-formats](data-formats.md). For
each task file, the converter creates a task-level conversion unit and emits
one frame record for each row in each `data/<demo>` group. Each record carries
the filename-derived instruction.

The per-frame transformations are:

```text
combined_state = concatenate(ee_states[t], gripper_states[t])  # 6 + 2 = 8
converted_action = concatenate(
    actions[t, :6],
    [1 - clip(actions[t, 6], 0, 1)],
)  # 6 + 1 = 7
```

The two image arrays become `observation.images.image` and
`observation.images.wrist_image`; the separate state arrays remain available
under their names. The canonical metadata is 20 FPS, robot type `franka`, and
LIBERO tags. Check the emitted metadata rather than assuming a writer accepted
an override.

A representative guarded invocation is:

```text
python <libero-converter-entrypoint> \
  --src-paths <suite-dir> [<second-suite-dir> ...] \
  --output-path <new-output-root> \
  --executor local \
  --cpus-per-task 1 \
  --workers 1
```

`<libero-converter-entrypoint>` is an environment-owned entry point; this skill
intentionally does not copy a checkout-relative script or hide its imports.
Use a new, explicitly named output root for the first run.

## 3. Multi-source merge

Pass multiple `--src-paths` values when combining task files from suites such
as a spatial and an object collection. The final aggregate is the requested
`--output-path`; per-task temporary outputs are staged beside it in the
converter's temporary aggregation area, conventionally `<output-name>_temp`,
then cleaned by the shared pipeline after successful aggregation.

Before merging, compare source directory basenames and task filenames. Two
identical basenames can collide in a temporary namespace, and two files can
carry different data under the same instruction. Preserve source provenance
and use distinct staging/output names when collisions exist. If aggregation
fails, retain logs and inspect the temporary area before any cleanup; do not
manually delete it until recovery or forensic review is complete.

## 4. Execution controls

| Flag | Meaning and safe use |
|---|---|
| `--executor local\|ray` | Local is the default and the safe baseline. Ray requires the DataTrove Ray extra and a deliberately managed cluster. |
| `--cpus-per-task N` | CPU allocation requested per conversion task; use a positive value supported by the runtime. |
| `--tasks-per-job N` | Ray scheduling batch/concurrency control; it has no effect for local execution. |
| `--workers N` | Number of concurrent jobs; `-1` means runtime default/all available according to the shared executor. Start small for HDF5/video workloads. |
| `--resume-dir PATH` | Existing conversion log directory. Verify it belongs to the same source set, output, and code/schema before resuming. |
| `--debug` | Small smoke mode: first two tasks, local execution, and Hub upload disabled. Treat this as structural validation, not a full result. |
| `--repo-id NAME/NAME` | Local aggregate identifier and, when pushing, the destination identifier. It is not permission to upload by itself. |
| `--push-to-hub` | Upload request; require an explicit repo id, credentials, review of metadata, and user approval. Keep off during preflight/debug. |

Do not start a Ray cluster merely because the flag is available. For a Ray
run, verify that all workers can read the same source paths and write the
planned staging/output paths, that the installed Ray/DataTrove versions are
compatible, and that the user owns the cluster. A local run can validate the
same LIBERO transformation semantics without Ray.

## 5. Resume and completion review

A resume is valid only when source directories, task discovery, filename-derived
instructions, output root, feature schema, and converter version are unchanged.
If any changed, create a fresh log/output plan instead. On completion, compare
source demo counts with emitted episode/frame/task counts, inspect all feature
shapes, confirm action inversion on a known row, and check that temporary
staging cleanup did not remove unrelated paths. Push only after this review.

## 6. Regeneration boundary (reference-only)

Regeneration replays demonstrations in an external LIBERO/robosuite
OffScreenRenderEnv. It is not a converter fallback that can be run on ordinary
Python plus h5py. The prerequisites are:

- a matching LIBERO task-suite installation and its BDDL files/assets;
- robosuite transform utilities and a functioning off-screen renderer;
- the original raw HDF5 directory and a separate target directory;
- enough disk space for rewritten HDF5 files and a metainfo JSON;
- explicit approval for simulator execution and output creation.

The documented suite choices are `libero_spatial`, `libero_object`,
`libero_goal`, `libero_10`, and `libero_90`. The replay seeds the environment,
sets the first original simulator state, performs settling no-op steps, and
replays each action. It drops a transition when the first six action values are
near zero and (except at the first retained transition) the gripper value is
unchanged from the previous action. It keeps only episodes whose replay ends
successfully. It records regenerated 256x256 images after a 180-degree image
rotation, plus state/action/reward/done data. The converter itself should not
rotate those frames again.

Treat an existing regeneration target as protected. The reference workflow can
ask to overwrite it; the safe operating procedure is to use a new target or a
verified backup, never to answer an overwrite prompt automatically. If a task
produces no successful episodes, expect its output file to be removed by that
reference workflow; record this as a deliberate side effect, not a conversion
failure to hide.
