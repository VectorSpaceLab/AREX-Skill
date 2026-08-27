# OpenX RLDS/TFDS-to-LeRobot troubleshooting

Use the first matching symptom, perform only the stated read-only checks until
preflight is complete, and stop at the stated boundary. This guide covers the
local Open X-Embodiment (OXE) RLDS/TFDS-to-LeRobot path. It does not download or
repair source data, run a conversion, render a simulator, launch a cluster,
run Beam, or publish to the Hub.

The converter's interface, path derivation, feature contract, and publication
semantics are summarized in [workflows.md](workflows.md). Exact dataset names,
state keys, encodings, and transform coverage are in
[oxe-configurations.md](oxe-configurations.md). Do not invent a mapping when
neither reference supports it.

## Triage and hard stop rules

Before any writer is created, record the exact local raw directory, derived
`dataset_name`, version, TFDS `data_dir`, OXE configuration, transform, task
field, state/action widths, selected image keys, output child, storage mode,
writer limits, FPS, and robot type. Keep `--push-to-hub` off.

Stop immediately when any of these is true:

- the raw argument is a URL, archive, empty directory, or unverified partial
  tree rather than an existing TFDS build with a usable `train` split;
- the derived dataset name or version is uncertain;
- a state/action/language contract is missing or its shape is repaired only by
  padding, truncating, flattening, or guessing;
- image rank, channel count, color order, or temporal alignment is unverified;
- the selected LeRobot API has not been checked;
- the derived output child is important or already contains data; or
- local review, destination, privacy, and authentication have not separately
  gated a Hub publication.

## Install and import compatibility

### `ModuleNotFoundError: tensorflow` or `tensorflow_datasets`

**Likely cause:** TensorFlow, TFDS, and LeRobot are imported before argument
parsing. Installing LeRobot alone is insufficient, and even `--help` can fail
before usage is printed.

**Recovery/preflight:** In the intended isolated environment, install mutually
compatible `tensorflow` and `tensorflow-datasets` packages, then perform only
these harmless import checks:

```text
python -c "import tensorflow as tf; import tensorflow_datasets as tfds; print(tf.__version__, tfds.__version__)"
python -c "from lerobot.datasets.lerobot_dataset import LeRobotDataset; print(LeRobotDataset)"
```

Confirm that the selected implementation's OXE configuration and transform
modules are installed or bundled with it; they must not be imported from a
vanished or private checkout. Record package versions and platform/backend
information before attempting any data access.

**Stop when:** either import fails, package versions are unpinned or known to
be incompatible, or the only apparent fix is to alter the source path or add a
hidden checkout to `PYTHONPATH`. Do not treat a successful TensorFlow import as
proof that a TFDS builder can be constructed.

### `tensorflow_graphics` is missing while a transform runs

**Likely cause:** Some quaternion-to-Euler standardizers import TensorFlow
Graphics lazily. It is optional for catalog lookup but required by those exact
transforms.

**Recovery/preflight:** Identify the exact transform selected by the exact
`dataset_name`. Install the optional package in the isolated environment and
import-test the required module without reading data, or choose a different
reviewed transform only when source action semantics actually match.

**Stop when:** the transform's optional dependency cannot be imported, the
mapping is uncertain, or someone proposes skipping rotation conversion merely
to make arrays fit. A shape-compatible action with the wrong rotation meaning
is not a valid recovery.

### LeRobot imports but the writer API is incompatible

**Symptoms:** Import-path errors, missing `LeRobotDataset.create`, unexpected
keyword-argument errors, missing `add_frame` or `save_episode`, or a missing
`push_to_hub` method.

**Likely cause:** The distilled path targets a particular LeRobot dataset
writer surface. LeRobot releases can move the class, rename writer arguments,
or change video metadata requirements while remaining importable.

**Recovery/preflight:** Inspect the installed public class and signatures
without creating a dataset. The compatibility check must cover:

- the import used by the candidate (`lerobot.datasets.lerobot_dataset`);
- `LeRobotDataset.create` accepting the selected `repo_id`, `robot_type`,
  `root`, `fps`, `use_videos`, `features`,
  `image_writer_threads`, and `image_writer_processes` semantics;
- `add_frame`, `save_episode`, and their expected frame/episode contracts; and
- `push_to_hub` arguments only if publication is later approved.

If the candidate CLI uses different flags, write down an explicit adapter and
its semantic differences before proceeding. A top-level `lerobot` import or a
successful package installation is not enough.

**Stop when:** a required method/argument is absent, an API adapter has not
been reviewed, or video feature requirements are unclear. Do not claim support
for a newer LeRobot version from import success alone.

### `--help` fails before printing help

**Likely cause:** Eager imports fail, or the entrypoint is not the intended
OpenX converter.

**Recovery/preflight:** Run the package probes above first, verify the
entrypoint's help surface against [workflows.md](workflows.md), and invoke help
without raw-data, output, or publication options. Keep this a parser check;
help success proves neither TFDS access nor writer compatibility.

**Stop when:** imports remain unresolved, the flags differ without a reviewed
mapping, or help requires starting a conversion.

## Raw path, builder, and data validation

### `Dataset ... not found`, `BuilderConfig ... not found`, or an unknown builder

**Likely cause:** The strict final-component rule produced the wrong builder
name, version, or TFDS data root; the path may also contain an incomplete or
foreign cache. The rule is:

- final component matching `^\d+\.\d+\.\d+$`: use its parent as
  `dataset_name`, that component as `version`, and the grandparent as
  `data_dir`;
- otherwise: use the final component as `dataset_name`, use an empty version,
  and use its parent as `data_dir`.

Do not remove suffixes such as `converted_externally_to_rlds`, change case, or
replace hyphens based on a nearby dataset.

**Recovery/preflight:** Print the derived tuple
`(dataset_name, version, data_dir)` before builder construction. Inspect local
TFDS metadata, the exact builder/config registration, the `steps` feature
structure, and the presence of a `train` split. Compare the spelling with the
exact catalog entry in [oxe-configurations.md](oxe-configurations.md).

**Stop when:** the builder cannot be resolved from the verified local tree, a
version is guessed, the path is actually an archive/URL/cache fragment, or the
name is being fuzzy-matched. The route does not fetch or materialize missing
external data.

### The directory exists but TFDS sees no usable data

**Likely cause:** A filesystem directory is not necessarily a TFDS dataset. It
may be a partial extraction, a cache for another version, or a raw RLDS tree
whose layout does not match the registered builder.

**Recovery/preflight:** Validate builder metadata and feature schemas without
creating LeRobot output. Confirm `steps`, `observation`, action data, and a
`train` split; inspect one representative local episode only if the environment
already has the data and the inspection is non-destructive.

**Stop when:** metadata or split validation fails, any required data would have
to be downloaded/repaired, or the source owner has not approved the data
materialization step. Never substitute a fake builder name.

### No OXE configuration and/or no standard transform

#### Name is in neither registry

**Likely cause:** The name is new, misspelled, or outside the reviewed catalog.
The implementation falls back to eight `None` state slots, zero state columns,
10 FPS, and robot type `unknown`.

**Recovery/preflight:** Keep the dataset unsupported. Request a reviewed
mapping containing source state keys, intended eight-wide state layout,
action encoding and semantics, language field, FPS, robot type, image/depth
conventions, and any required transform. Validate it on a synthetic or
read-only schema fixture before writing data.

**Stop when:** the only proposed recovery is accepting all-zero state,
`unknown` robot type, default FPS, or a guessed action convention. That fallback
is diagnostic only and must not be treated as production output.

#### Configuration exists but no standard transform exists

**Likely cause:** The catalog describes state/action metadata but the transform
registry has no exact key. Raw actions may be relative, absolute, inverted,
clipped, quaternion-valued, or otherwise dataset-specific.

**Recovery/preflight:** Inspect raw action units and gripper convention, the
post-standardization language field, and every configured state key. Make an
explicit identity/normalization decision with finite-value, width, and semantic
checks, or add a separately reviewed transform.

**Stop when:** identity is inferred only from transform absence, or action and
gripper semantics cannot be established.

#### Transform exists but configuration does not

**Likely cause:** A transform-only alias, such as `ppgm`, `ppgm_static`, or
`ppgm_wrist`, has standardization code but no reviewed eight-column state
mapping in the catalog.

**Recovery/preflight:** Validate the transformed state keys and define the
state/action contract explicitly. Do not promote the generic eight-zero-column
fallback merely because the transform itself runs.

**Stop when:** no reviewed state mapping exists or the transformed action
meaning is unknown.

#### Configuration and transform names disagree

**Symptom:** A catalogued dataset loads but expected standardization does not
occur; state keys or action widths then fail.

**Likely cause:** Registry lookup is exact. For example, `rh20t` is a
configuration key while the transform registry uses `rh20t_rlds`.

**Recovery/preflight:** Resolve the actual TFDS builder name and the exact
transform key against source evidence. Do not add fuzzy aliases or apply a
nearby robot's transform.

**Stop when:** the exact identity/transform pairing cannot be justified.

## Data, state, action, and task schema failures

### Missing `language_instruction`, undecodable bytes, or empty task

**Likely cause:** The transform did not create the required field, the source
uses another language key, the value is not a byte/string tensor, or an episode
contains malformed/empty text. The writer takes the first task value and uses
it for every frame in that episode.

**Recovery/preflight:** Inspect the post-transform trajectory keys and dtype.
Confirm one decodable task string per episode, including whether a transform
moves text from `observation/natural_language_instruction` or decodes a padded
instruction. Define an explicit policy for a source known to have no language
rather than silently inventing a placeholder.

**Stop when:** `language_instruction` is absent after the selected transform,
bytes cannot be decoded safely, task text is unexpectedly empty, or per-step
instruction changes are being discarded without approval.

### Missing configured state/observation key

**Likely cause:** The wrong exact dataset name selected the transform, the
transform did not create the configured nested key, or the raw schema differs
from the catalog. A catalog `None` is intentional one-column zero padding; it
is not a missing-key error.

**Recovery/preflight:** Compare the transformed observation key set with the
exact row in [oxe-configurations.md](oxe-configurations.md). Check nested
structure, transform execution, numeric dtype, leading time dimension, and the
width expected for every non-`None` key.

**Stop when:** a genuinely absent source component would be replaced with an
unreviewed zero, or the wrong transform/mapping is suspected. Do not use zero
padding except for an intentional catalog `None` slot.

### Proprioception concatenation raises a rank or shape error

**Likely cause:** A state component is not time-leading `(T, width)`, has a
wrong trailing width, is scalar/nested, or is nonnumeric. The implementation
concatenates components; it does not reshape malformed arrays.

**Recovery/preflight:** Assert every configured component is numeric and
`(T, width)` after standardization, assert all time lengths agree, cast numeric
values to float32, and verify the configured widths sum to eight. Preserve the
meaning of quaternions, axis-angle vectors, and joint arrays; do not flatten
or truncate them to satisfy metadata.

**Stop when:** rank, width, or time alignment still fails, or a reshape would
change semantics.

### Missing/invalid action or unexpected action width

**Likely cause:** The raw or transformed trajectory lacks `action`, the action
encoding does not match the transform, or relative/absolute and gripper
polarity conventions were assumed. The reviewed encodings produce width 7 for
`EEF_POS` and width 8 for `JOINT_POS`.

**Recovery/preflight:** Confirm action exists after standardization, is
float-convertible, time-aligned with state/images, finite, and has the exact
catalogued width. Check the transform's documented rotation, gripper, and
relative/absolute behavior on a small synthetic fixture. Record any explicit
FPS override; the implementation casts FPS to `int`, so fractional catalog
frequencies such as 12.5 or 3.75 are silently truncated unless overridden.

**Stop when:** action would be padded, clipped, truncated, or polarity-flipped
without source evidence, or width/time validation fails.

## Image, depth, channel, and rank failures

### No image features are generated

**Likely cause:** Feature selection examines actual observation keys and keeps a
key only when it contains lowercase `image` or `rgb` and does not contain
lowercase `depth`. A camera listed in the catalog may not exist in the builder,
may be nested differently, or may be created under another name by a
transform.

**Recovery/preflight:** Inspect the transformed observation key set and the
builder feature shapes. Use an explicit key mapping only after confirming the
source schema, modality, and color semantics.

**Stop when:** an arbitrary scalar/array is renamed as an image or the expected
camera cannot be proven to exist.

### Depth was expected but disappears

**Likely cause:** The base route intentionally excludes every key containing
lowercase `depth` both when features are declared and when frames are written.
Several catalog entries list depth intent, but that does not change the RGB-only
writer contract. Some transforms also move or squeeze depth into a key that is
then excluded.

**Recovery/preflight:** Decide whether depth is truly required. If not, record
its intentional exclusion. If yes, stop this route and use a separately
reviewed depth-capable implementation with explicit depth dtype, scaling,
shape/rank, feature metadata, and writer tests.

**Stop when:** depth is described as converted by the base route without those
checks. Do not relabel depth as RGB.

### A grayscale, rank, or channel error occurs in image writing

**Symptoms:** LeRobot rejects an image, video encoding fails, colors are
scrambled, or metadata says RGB while frames are 2-D, one-channel, channel-
first, batched, or otherwise inconsistent.

**Likely cause:** The feature metadata names every selected image
`[height, width, rgb]`, but the source shape is copied from TFDS and frame
values are passed through without rank/channel validation. The expected
contract is consistent HWC data with three channels per selected RGB stream.

**Recovery/preflight:** For each selected key, verify a fixed `(height, width,
3)` shape for every timestep, numeric/byte-compatible image values, finite and
consistent dimensions, and channel order. Keep channel reversal only for an
exact standardizer known to correct BGR; unknown names receive no global
correction. A rank-2 grayscale image, one-channel depth-like array,
channel-first array, or `(T, H, W, C)` value passed as one frame needs an
explicit reviewed conversion policy.

**Stop when:** rank/channel/shape or color order is unknown, frames vary within
an episode, or someone proposes blindly reshaping, duplicating channels, or
reversing all images.

### `--use-videos` fails while image mode is acceptable

**Likely cause:** The video codec/torchcodec stack is unavailable, frame shapes
vary, temporary storage is insufficient, or writer concurrency is too high.
The CLI flag is off unless supplied, while the Python API default is on; do not
assume those defaults are equivalent.

**Recovery/preflight:** Verify codec support and consistent HWC RGB frames
without publishing. Compare the requested storage mode with the actual feature
declarations. Reduce writer processes/threads and temporary-storage pressure;
use image mode only as an explicit storage decision after schema validation.

**Stop when:** frames are invalid, codec compatibility is unknown, or changing
storage mode is being used to conceal state/action/schema errors.

## CLI/API misuse and destructive output behavior

### `--raw-dir` or `--local-dir` is rejected or has the wrong meaning

**Likely cause:** The candidate exposes a different interface, a required path
is missing, or a file was supplied where a directory is expected. `--local-dir`
is a parent: the implementation appends a derived child named
`<dataset>_<version>_lerobot`. `--repo-id` is a Hub name, not a local path.

**Recovery/preflight:** Compare the candidate help surface with the options in
[workflows.md](workflows.md), validate paths read-only, and print the derived
output child before any writer call. Map every renamed option and semantic
difference explicitly.

**Stop when:** the candidate cannot be mapped to the contract, or a Hub name
is being substituted for local staging.

### An existing output was deleted

**Likely cause:** The reference behavior appends the derived child to
`--local-dir` and recursively removes that child before constructing the TFDS
builder. It has no resume, backup, or collision-protection mode.

**Recovery/preflight:** Stop the run. Recover from an independent backup if
available, and do not retry against the same important parent. For a future
attempt, precompute the child, require a fresh or explicitly disposable
staging parent, and use a distinct output parent per attempt.

**Stop when:** the destination is not provably disposable or a resume is being
assumed. Never treat deletion followed by a failed builder as a recoverable
conversion state.

### CLI parser accepts unsafe values

**Symptoms:** Nonpositive writer counts, negative/zero FPS, blank identifiers,
or a push request without a repository identifier gets as far as writer
creation.

**Likely cause:** The reference parser does not enforce all operational guards.

**Recovery/preflight:** Add a wrapper or preflight that rejects nonpositive
writer processes/threads, nonpositive effective FPS, blank dataset names, and
`--push-to-hub` without a reviewed nonempty `repo_id`. Keep the exact derived
identity and output path in the preflight record.

**Stop when:** unsafe values cannot be rejected before output creation.

## Writer resources and workflow-specific failures

### Writer runs out of memory, file descriptors, disk, or temporary space

**Likely cause:** Memory and descriptors scale with image-writer processes times
threads. Image mode creates many files; video mode uses encoders and temporary
frames; the input may be much larger than expected.

**Recovery/preflight:** Estimate output and temporary size, use a fresh staging
parent, and choose conservative writer counts. For a later approved execution,
validate a small representative fixture first, then increase limits gradually
while monitoring memory, descriptors, disk, and temp space. Preserve logs and
inspect whether the failure is schema-related rather than resource-related.

**Stop when:** storage or memory headroom is unknown, the destination is shared
or important, or increasing concurrency is being used to hide a writer/API
failure. Do not switch to Ray, a cluster, or Beam as a local-memory workaround.

### Kuka episodes all disappear or filtering raises `success` errors

**Likely cause:** The workflow applies `success` filtering only when the exact
`dataset_name` is `kuka`. A missing, malformed, or unexpectedly false success
field can remove every episode or fail during filtering.

**Recovery/preflight:** Inspect the local builder's `success` field and its
boolean shape before writer creation. Confirm that filtering is intended and
record the retained episode count. Do not silently remove the filter or apply
it to a different dataset.

**Stop when:** the field is absent/malformed, all episodes are removed without
an approved reason, or the dataset identity is uncertain.

### Bridge or another transform changes episode length

**Likely cause:** Standardizers are allowed to remove no-op steps, relabel
movement from neighboring states, discard a final no-action step, or derive
new action/state fields. Raw length equality is therefore not sufficient.

**Recovery/preflight:** Validate transformed action, state, image, and language
lengths together before `add_frame`. For Bridge specifically, verify the first
no-op removal and final relabeling. Reconcile or discard an episode only under a
documented policy; do not let a frame loop fail after partially writing it.

**Stop when:** transformed streams are not aligned or the repair policy is
undocumented.

### Transform executes but produces wrong semantics

**Likely cause:** An exact transform was applied to the wrong dataset name,
relative/absolute action convention was mismatched, BGR handling was assumed,
or an optional rotation dependency was bypassed.

**Recovery/preflight:** Compare the exact dataset identity, transform key,
configuration row, source action/state meanings, gripper polarity, and camera
conventions. Use a small synthetic semantic fixture with expected state/action
values, not only shape assertions.

**Stop when:** semantic expectations cannot be demonstrated. Never accept a
successful tensor operation as proof of a correct OXE standardization.

## Optional Beam distinction

Apache Beam is **not** a dependency, fallback, or acceleration switch for the
OpenX RLDS/TFDS-to-LeRobot conversion described here. The OpenX path is a local
TFDS reader plus a LeRobot writer and has no Beam execution branch.

Beam is an optional dependency in the separate LeRobot-to-RLDS/TFDS export
workflow. Its documented trade-off is possible instability or partial episode
loss in exchange for speed; small or loss-intolerant exports should disable it.
Do not install or enable Beam to cure an OpenX builder, schema, writer-memory,
or import failure. If the intended direction is LeRobot-to-RLDS/TFDS, stop and
route that task separately rather than mixing the two workflows.

**Stop when:** a proposed OpenX recovery launches Beam, a cluster, or a
parallel data job. This route deliberately does not own those operations.

## Hub publication gate

### Push is rejected or targets the wrong repository

**Likely cause:** `repo_id` is missing/blank, authentication or namespace is
wrong, a destination collision was not reviewed, or `--push-to-hub` was enabled
before local inspection. The reviewed publication call is public, pushes video
files, adds dataset tags, and supplies an Apache-2.0 license field.

**Recovery/preflight:** Keep publication disabled. After a successful local
staging review, confirm all of the following separately:

1. The exact `repo_id` namespace and dataset name are correct.
2. Authentication works without exposing credentials in logs.
3. Public visibility is explicitly approved; do not assume a private default.
4. Video upload behavior, tags, license, robot type, and storage cost are
   acceptable.
5. Episode count, frame counts, feature metadata, FPS, state/action values,
   task strings, image channels, and intentional depth omission have been
   reviewed locally.
6. The user has approved the irreversible remote write.

Enable the push option only after these checks and only for the reviewed
output. A successful API call is not evidence that the destination or privacy
choice was correct.

**Stop when:** local review is incomplete, `repo_id` is unverified,
authentication would be logged, public/private semantics are unclear, or Hub
consent is absent. Never claim that a push occurred during troubleshooting.

## Final preflight checklist

Before handing the workflow to an executor, require:

- TensorFlow, TFDS, OXE modules, and the selected LeRobot API import cleanly;
- exact `(dataset_name, version, data_dir)` and a local `train` split are known;
- the configuration/transform pairing is catalogued or explicitly reviewed;
- language, configured state keys, action width, rank, dtype, finite values, and
  post-transform time lengths are validated;
- selected RGB keys have stable HWC three-channel shapes and known color order;
- depth exclusion or an approved depth-capable alternative is recorded;
- output collision behavior and a fresh staging parent are understood;
- FPS truncation/override, robot type, storage mode, and writer limits are
  recorded;
- Beam, clusters, downloads, and Hub publication remain outside this route; and
- the Hub gate is still closed until local review and explicit consent.

If any item is unknown, return to the matching section and stop rather than
letting the writer manufacture plausible-looking but semantically invalid
LeRobot data.
