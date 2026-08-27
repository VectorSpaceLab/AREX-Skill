# Cross-Cutting Troubleshooting

Use the nearest sub-skill troubleshooting file first. This page covers failures
that span multiple Any4LeRobot routes.

## Import and version mismatch

**Symptoms:** `ImportError: cannot import name 'LeRobotDataset' from
'lerobot.datasets'`, `No module named lerobot.datasets.dataset_writer`, missing
`lerobot.common.datasets.*`, or a writer signature rejecting arguments.

**Cause:** Any4LeRobot is not packaged and its scripts were written against a
particular LeRobot source layout. Current releases may expose the class only at
`lerobot.datasets.lerobot_dataset`, and historical v2 scripts require different
modules than v3 scripts.

**Recovery:** create a clean route-specific environment; inspect
`from lerobot.datasets.lerobot_dataset import LeRobotDataset,
LeRobotDatasetMetadata`, inspect `LeRobotDataset.create` and `add_frame`/save
methods, then use the LeRobot revision documented for the target direction. Do
not mix v2 and v3 packages or edit metadata paths until the API is matched.

## Missing optional dependencies

- `datatrove` missing: generic/AgiBot/LIBERO shared pipeline imports can fail
  even for local execution. Install a compatible DataTrove release or choose a
  route-specific implementation that does not use the shared pipeline.
- `ray` missing: use `executor=local` or a dataset's debug path first. Install
  the Ray/DataTrove Ray extras only when distributed execution is intentional.
- `tensorflow`/`tensorflow-datasets` missing: OpenX and RLDS export cannot read
  or write TFDS. Do not substitute an arbitrary dataset library.
- `apache-beam` missing: keep RLDS export in direct mode; Beam is optional and
  can lose episodes according to the repository guidance.
- `ffmpeg` missing: v2.1↔v3.0 video migration cannot split or concatenate video.
  Preflight the executable before touching a dataset.
- RoboCasa/LIBERO simulator packages/assets missing: do not claim rerender,
  depth, segmentation, or success-filtered output. Use conversion-only if its
  input schema already contains the required fields.

## Layout and schema failures

**Symptoms:** no tasks found, missing HDF5 key, mismatched image/state/action
lengths, invalid feature shape, missing language text, or episodes silently
skipped.

**Recovery:** stop writing; list the exact source tree and inspect a small set of
HDF5 groups, TFDS feature keys, or LeRobot metadata. Compare against the owning
route's `data-formats.md`. Keep a machine-readable skip reason for every
excluded episode. Do not pad, reshape, or rename fields without an explicit
schema decision and downstream consumer check.

## Output deletion and retry hazards

Several source-derived converters remove an existing `local_dir`, final output,
temporary task output, or version-migration destination. Before retrying:

1. compare source and output resolved paths;
2. identify what will be deleted or renamed;
3. take a backup/checksum or use a new staging root;
4. remove only a known partial output after confirming ownership;
5. validate metadata and counts before reusing a resume log.

A resume directory from a different task manifest or source root is not safe.

## Ray, Beam, and resource failures

Use local/debug with bounded workers first. For Ray, verify shared filesystem
paths, worker-visible imports, CPU/memory reservations, and cluster ownership;
never treat Ray availability as proof of a working cluster. For Beam, compare
episode IDs/counts against direct mode and rerun direct when data loss is
possible. HDF5/video conversion can need many GiB per task; reduce task
parallelism before changing schema or deleting inputs.

## Hub, Git-LFS, and credentials

Keep `push_to_hub`, Hub deletion/tagging, `snapshot_download`, Git-LFS clone,
commit, and push disabled during preflight. If a route needs them, use a test
branch or disposable repository, verify authentication and destination
ownership, and record the revision. A successful local conversion does not
authorize public upload or replacement.

## Video and modality failures

Check ffmpeg/codec support, exact camera names, frame count, channel order,
depth units, and timestamps. A missing depth stream is not equivalent to a
zero depth map. A 128x128 source is not a 256x256 feature. Simulator rerendering
may drop unsuccessful episodes and is not lossless; preserve the original HDF5.

## When to stop

Stop and report rather than guessing when the required LeRobot API cannot be
matched, a required source layout is absent, a version is ambiguous, output
ownership is unclear, credentials or external assets are required, or a route's
optional capability would be falsely represented as verified. Record the
observed error, route, environment/version, attempted safe checks, and the next
viable environment or data requirement.
