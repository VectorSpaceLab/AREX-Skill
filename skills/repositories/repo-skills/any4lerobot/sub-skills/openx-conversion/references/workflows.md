# OpenX conversion workflows

This reference is a self-contained contract for an Open X-Embodiment RLDS/TFDS
to LeRobot implementation. It is adapted from the reviewed conversion behavior,
not a copy of an executable script. It intentionally contains no downloader,
data writer, Hub client, or source-checkout import.

## 1. Preconditions and a no-data help probe

A real conversion needs all of the following in one compatible environment:

- Python with TensorFlow and TensorFlow Datasets (`tensorflow` and
  `tensorflow-datasets`), plus NumPy.
- A LeRobot installation exposing the dataset writer API used by the selected
  implementation. The relevant API surface is `LeRobotDataset.create`,
  `add_frame`, `save_episode`, and `push_to_hub`.
- The OXE configuration and transform implementation used by the converter.
  These must be installed or bundled by the implementation; they must not be
  imported from a vanished checkout.
- An already materialized local TFDS data tree with a compatible builder and
  `train` split. A URL, cache hint, or empty directory is not sufficient.

For a parser-only `openx-help` case, first run harmless package probes such as:

```text
python -c "import tensorflow as tf; import tensorflow_datasets as tfds; print(tf.__version__, tfds.__version__)"
python -c "from lerobot.datasets.lerobot_dataset import LeRobotDataset; print(hasattr(LeRobotDataset, 'create'))"
```

Then run the **candidate entrypoint's** `--help` without `--raw-dir`,
`--local-dir`, or any write/push option. Because the reference implementation
imports TensorFlow, TFDS, LeRobot, and its OXE modules before parsing, missing
imports can prevent help output; diagnose that as an environment failure, not
as an invalid CLI invocation. Do not launch the conversion merely to test it.

## 2. Path identity and TFDS builder lookup

Resolve a raw path without normalizing or guessing names:

| Raw path shape | `dataset_name` | `version` | TFDS `data_dir` |
| --- | --- | --- | --- |
| `/data/droid/1.0.0` | `droid` | `1.0.0` | `/data` |
| `/data/droid` | `droid` | empty | `/data` |
| `/data/my_dataset/2.1.3/extra` | `extra` | empty | `/data/my_dataset/2.1.3` |

The version test is the strict pattern `^\d+\.\d+\.\d+$` on the final
component. A version-like directory with a fourth component is not detected.
The builder lookup is conceptually:

```text
tfds.builder(dataset_name, data_dir=data_dir, version=version)
```

Inspect the builder's `info.features["steps"]["observation"]` before creating
LeRobot metadata. A valid builder should expose a `steps` structure with an
observation mapping, action data, language after standardization, and a train
split. Ensure all expected pieces are time-aligned.

The output child is derived as:

```text
<local-dir>/<dataset_name>_<version>_lerobot
```

When `version` is empty, the separator remains part of the formatted name
(e.g. `droid__lerobot`). Treat that as an observable compatibility behavior;
an implementation may choose a cleaner name only if it records the difference.
The reference behavior removes this child recursively before calling the
builder. It does not offer a resume or backup flag.

## 3. Interface contract

The reviewed CLI surface is:

| Option | Required/default | Meaning and guard |
| --- | --- | --- |
| `--raw-dir PATH` | required CLI | Existing TFDS raw dataset path or version directory; no download is initiated. |
| `--local-dir PATH` | required CLI | Parent under which the derived LeRobot child is created. Use a new staging parent. |
| `--repo-id NAME` | optional | Hub identifier; required if publishing. Do not treat it as a local output path. |
| `--push-to-hub` | off | Explicit publication request. Keep off during validation. |
| `--robot-type TEXT` | inferred | Overrides the catalog robot type. Normalize inferred values to lowercase with spaces and hyphens replaced by underscores. |
| `--fps INTEGER` | inferred | Overrides the catalog control frequency. The writer receives an integer. |
| `--use-videos` | off at CLI | Store selected RGB streams as video features instead of image features. The Python API's default is on, so check the caller's default. |
| `--image-writer-process INTEGER` | 5 | Number of image-writer processes. It is singular in the flag but passed as `image_writer_processes`. |
| `--image-writer-threads INTEGER` | 10 | Threads per image-writer process. |

The Python API also accepts `keep_images` with a default of true, but the
reviewed CLI does not expose it and the save helper does not use that keyword
to change behavior. Do not promise that setting it preserves or removes image
files without checking the actual LeRobot writer version.

Before invoking any implementation, reject nonpositive writer counts, negative
FPS, a blank dataset name, and a Hub push without a repository ID. The reference
parser does not enforce all of these guards, so a safer wrapper should.

## 4. Transform and frame pipeline

The intended per-episode order is:

1. Batch all steps of an episode into a time-leading trajectory.
2. Apply the exact standardization transform when `dataset_name` is present in
   the transform registry.
3. Look up `state_obs_keys` for the exact dataset configuration. For an
   unconfigured name, use eight `None` placeholders only as a diagnostic
   fallback; do not publish it.
4. For every configured state key, cast the transformed observation to float32;
   for `None`, append a float32 column of zeros with one value per timestep.
5. Concatenate pieces into `proprio`, move `language_instruction` to `task`,
   and cast `action` to float32.
6. Select image keys from the transformed observation mapping, excluding keys
   containing `depth` and retaining keys containing `image` or `rgb`.
7. For every timestep, emit selected image arrays, `observation.state`,
   `action`, and the episode task string; then save the episode.

The transform registry is dataset-specific rather than a generic normalization
switch. Examples of semantics represented by the reviewed transforms include
relative-to-absolute gripper conversion, clipping or inversion, Bridge first
step removal and reached-state relabeling, DROID action/state construction,
BGR-to-RGB channel reversal for known datasets, quaternion-to-Euler conversion,
and dataset-specific action truncation or zero padding. Do not apply these
operations by name alone to an unknown dataset.

A transform may alter time length. Bridge transforms discard an initial
no-op and then relabel movement from successive states, discarding the final
no-action timestep. Validate action, state, image, and language lengths after
the transform rather than comparing them only to raw lengths.

The Kuka path additionally filters episodes using `success`; all other paths
use the train split without that filter. If a Kuka episode lacks a compatible
success field, stop and fix the input rather than silently retaining it.

## 5. Feature construction

The image feature contract is derived from actual TFDS shapes:

```text
observation.images.<key>:
  dtype: video when --use-videos, otherwise image
  shape: builder.info.features["steps"]["observation"][key].shape
  names: [height, width, rgb]
```

The generated state feature is float32 with a one-dimensional shape equal to
the number of generated state names (normally eight), and names under
`motors`. The action feature is float32 with a one-dimensional shape equal to
the generated action names (normally seven for `EEF_POS`, eight for
`JOINT_POS`) and names under `motors`. A feature declaration is not a reshape:
source arrays must already have compatible widths.

The LeRobot writer receives the inferred or overridden FPS and normalized robot
type. The source catalog contains fractional `12.5` and `3.75` frequencies, but
the reference call converts FPS to `int`, so relying on those defaults silently
produces 12 or 3. Set an explicit integer FPS and record that decision when the
source frequency is nonintegral.

## 6. Writer and storage controls

Start with a small local validation run and conservative writer settings. The
writer process/thread product multiplies memory and file-descriptor pressure;
`5 x 10` is a reference default, not a hardware recommendation. Video output
usually reduces disk usage and can improve loading, but requires a working
video codec stack and makes cleanup/inspection less transparent.

Do not start with `--push-to-hub`. After a local run, inspect:

- the metadata version, FPS, normalized robot type, and feature declarations;
- state/action widths and finite numeric values;
- episode count and per-episode frame counts;
- task strings for empty, undecodable, or unexpectedly duplicated values;
- RGB dimensions, channel order, and whether depth was intentionally omitted;
- image/video files and writer temporary files; and
- the exact output path before any deletion or publication step.

A local review should be repeatable from a copied input or a separate output
parent. Never use a second run as a repair mechanism against an existing
important output because the derived child is deleted first.

## 7. Guarded Hub publication

A publication request must pass all local checks and separately confirm:

1. `repo_id` has the intended namespace and dataset name.
2. Authentication resolves without exposing a token in logs.
3. The dataset may be public. The reviewed behavior sets `private=False`.
4. Video files should be uploaded (`push_videos=True`) when videos are used.
5. The proposed tags, license (`apache-2.0`), and robot type are correct.
6. The user explicitly accepts an irreversible remote write and its storage cost.

The source behavior asserts that `repo_id` is not `None` only when publishing;
it does not validate namespace, authentication, privacy, or destination
collisions. A guarded wrapper should perform those checks and show the exact
remote target before adding the push option.

## 8. Synthetic feature-mapping contract

A safe unit-level fixture can avoid TensorFlow data downloads and large writes.
Represent one episode as time-leading arrays with `T >= 2`, one language string,
and an observation mapping. For a known POS_EULER configuration, provide a
six-wide EEF state key, one-wide gripper key, one missing slot, and an action of
shape `(T, 7)`; assert a state of `(T, 8)`, action `(T, 7)`, finite float32
values, and task preservation after the selected transform. For a JOINT
configuration, provide the configured joint array and gripper array and assert
that every declared pad column is exactly zero.

A second fixture should include RGB, uppercase `Depth`, lowercase `depth`, and
a non-image scalar key. Assert that only keys containing lowercase `image` or
`rgb` and no lowercase `depth` are emitted. The uppercase case exposes the
case-sensitive behavior and should be handled by explicit input validation,
not silently treated as a valid depth convention. Keep these fixtures in the
verification artifact area, not in this runtime directory.
