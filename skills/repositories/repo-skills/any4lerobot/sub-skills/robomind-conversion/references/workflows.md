# RoboMIND workflow and execution reference

## Conversion contract

The source root is a RoboMIND release collection. A requested run selects one
benchmark release and one or more physical embodiments, discovers task
folders, and emits one LeRobot dataset per task. The intended output pattern is:

```text
<output-root>/<benchmark>/<embodiment>/<task>/
```

The source-to-output traversal is conceptually:

```text
<source-root>/<benchmark>/h5_<embodiment>/<task>/success_episodes/train/**/trajectory.hdf5
<source-root>/<benchmark>/h5_<embodiment>/<task>/success_episodes/val/**/trajectory.hdf5
```

The glob allows an episode identifier directory between `train` or `val` and
`trajectory.hdf5`; do not hard-code a single episode-directory spelling. The
source root also contains the shared instruction CSV and a language annotation
JSON directory. See [data formats](data-formats.md) for exact required names.

A task is eligible only when its config-driven data can be loaded and its
resulting frame list has at least 50 frames. The implementation skips shorter
or unreadable episodes and logs a warning. A task with no accepted episodes is
removed by the implementation; a safe equivalent should instead stage or
quarantine an empty result until the operator confirms deletion.

## CLI planning contract

The evidence CLI exposes these arguments:

| Option | Meaning and safe validation |
|---|---|
| `--src-path PATH` | Required RoboMIND source root; must contain the selected release and shared annotations. |
| `--benchmark NAME` | One of `benchmark1_0_release`, `benchmark1_1_release`, `benchmark1_2_release`; default evidence choice is `benchmark1_1_release`. |
| `--output-path PATH` | Required local output root, distinct from source. |
| `--embodiments NAME ...` | One or more of `agilex_3rgb`, `franka_1rgb`, `franka_3rgb`, `franka_fr3_dual`, `tienkung_gello_1rgb`, `tienkung_prod1_gello_1rgb`, `tienkung_xsens_1rgb`, `ur_1rgb`. |
| `--cpus-per-task N` | Positive Ray CPU reservation; evidence default is 2. It has no effect on debug traversal. |
| `--save-depth` | Include configured depth features and read `observations/depth_images`; absent means depth features are removed. |
| `--debug` | Process only the first discovered task for the first selected embodiment without initializing Ray. |

The command shape is a recipe, not a bundled executable:

```text
python <approved-robomind-entry> --src-path <source> --output-path <new-output> \
  --benchmark benchmark1_1_release --embodiments agilex_3rgb franka_1rgb \
  --cpus-per-task 2
```

Resolve `<approved-robomind-entry>` within the user's installed project or
adapted integration. This skill intentionally does not point at or copy a
source-checkout script. Validate all flags before invoking anything, and use
`--debug` for the first approved smoke path.

## Debug versus Ray

Debug calls the task enumerator for the first embodiment, consumes one task,
and runs it synchronously. It is useful for a small, isolated fixture and is the
only evidence-supported no-Ray route. It can fail with no task if the selected
release/embodiment tree is empty, so validate discovery first.

The normal route initializes Ray with environment variables that disable HDF5
file locking and progress bars, creates one remote conversion task per task
folder, and reserves `cpus-per-task` CPUs per task. It may use an existing Ray
cluster depending on the environment. Do not run `ray start`, `ray status`, a
multi-node recipe, Slurm setup, or a Ray job during skill construction. For an
approved production run, the operator must state whether a local Ray runtime or
an owned cluster is intended and how its logs are collected.

Use local/debug for:

- parser and import smoke checks;
- one embodiment and one task;
- investigating annotation, HDF5-key, or image-shape failures.

Use Ray only when:

- the task inventory is known;
- the output roots are isolated and replacement is approved;
- memory is sufficient for concurrent tasks;
- cluster ownership, address, environment propagation, and log collection are
  explicit.

The README evidence recommends roughly two CPU cores per task and about 10 GiB
of memory per task. Treat the memory estimate as a planning lower bound, not a
promise. Bound concurrency from available memory before selecting a larger
embodiment list. A CUDA device is not required by the conversion contract, but
video/image libraries may use optional acceleration.

## Split and annotation behavior

For each task, the converter visits `train` and then `val`. It builds a
per-task instruction from `RoboMIND_v1_2_instr.csv`, then attaches that string
to every frame. It separately loads `h5_<embodiment>.json` when present and
filters records by output task name and split. The selected response is kept as
episode-level `action_config`, normally with task-summary and step metadata.
If the file is absent or no record matches, the fallback is:

```json
{"task_summary": null, "steps": null}
```

The annotation id-to-episode mapping is dependent on the release's directory
naming. Validate that the parent component derived from each JSON `id` matches
the episode component used by the HDF5 path; do not silently attach a response
from a neighboring task. Missing CSV task keys are a hard preflight error,
while an absent JSON response is a recorded metadata gap.

The custom metadata writer updates total episode/frame/task counts, writes train
and validation split ranges, aggregates episode statistics, and stores the
`action_config`. Confirm that validation starts after the final train episode
for the selected task dataset; do not infer split counts from directory names
alone.

## Safe run sequence

1. Read-only inventory the selected release, `h5_<embodiment>` directories,
   task names, split directories, annotation files, and prospective outputs.
2. Parse config schemas and verify required HDF5 keys and equal frame lengths.
3. Resolve every task instruction and classify dirty tasks before scheduling.
4. Run a debug/synthetic smoke plan with no real conversion side effects.
5. Approve a new output root or an explicitly scoped per-task replacement.
6. Run with bounded local or Ray concurrency; retain stdout/stderr and the
   converter's error log.
7. Reopen metadata and compare accepted/skipped episode counts and lengths.
8. Review RGB color order, depth shape/statistics compatibility, split ranges,
   and action-config coverage before publication.

## Error and output logging

Informational logs include processing progress and skip warnings. Ray failures
are appended to `output.txt` relative to the process working directory, not
necessarily under the selected output root. Set a deliberate working directory
or redirect/copy logs after the run. Preserve the original exception and the
source episode path. Concurrent append behavior is not a structured error
store; for production, wrap the invocation with an external per-run log and
reconcile it with the output inventory.

## Synthetic structural case

A safe integration fixture can model one release, one supported embodiment, one
task, `success_episodes/{train,val}`, one annotation CSV row, and one JSON
annotation id without creating `trajectory.hdf5` or LeRobot output. Assert that
benchmark and embodiment validation selects the expected config, output path
is `<output>/<benchmark>/<embodiment>/<task>`, and missing simulation labels are
rejected. A second fixture should model `franka_3rgb` with a BGR RGB payload and
a top-camera raw payload that matches the 480x640 fallback; assert that the
plan requests RGB channel reversal and a single, recorded shape fallback while
Ray remains uninitialized.
