---
name: "openx-conversion"
description: "It guides Open X-Embodiment RLDS/TFDS-to-LeRobot conversion, OXE
  transform selection, and guarded Hub publication."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Open X-Embodiment to LeRobot

Use this route to plan, validate, or run a **local** conversion from an Open
X-Embodiment (OXE) RLDS/TFDS dataset into a LeRobot dataset. It covers raw
path identity, OXE standardization, state/action schema selection, RGB/depth
handling, writer settings, and a separately approved Hub publication.

## Route here when

- The input is an RLDS dataset readable by TensorFlow Datasets (TFDS), not an
  existing LeRobot dataset.
- The task mentions Open X-Embodiment, OXE, RLDS, TFDS, a named OXE dataset,
  standard transforms, or conversion to LeRobot.
- The user needs to choose an OXE configuration, explain padding or feature
  names, troubleshoot TensorFlow/TFDS, or review `--use-videos` controls.

## Do not use this route when

- Exporting **from LeRobot to RLDS/TFDS**; choose the `rlds-export` route.
- Designing a reusable multi-source aggregation pipeline; choose the
  `generic-conversion` route.
- The source is HDF5, AgiBot, RoboMIND, LIBERO, or RoboCasa rather than an
  RLDS/TFDS builder; use its dataset-specific route.
- The request is to download OpenX data, create a Beam/Ray job, or push an
  unreviewed dataset. This guide deliberately does none of those things.

## Operating boundaries

The conversion behavior distilled here was designed for a LeRobot API that
provides `LeRobotDataset.create`, `add_frame`, `save_episode`, and
`push_to_hub`. Confirm that those methods and their arguments exist in the
selected environment before a real run. A successful import of a newer
LeRobot package is not proof of converter compatibility.

Treat the local destination as destructive: the reference behavior derives a
specific child directory under `--local-dir` and recursively removes that child
if it already exists. Never point `--local-dir` at an irreplaceable directory,
and do not use it as a resume mechanism. Use a distinct, empty staging parent.

This is an operating guide, not a bundled data converter. It never requires the
source checkout to remain available. A user who needs execution must supply or
write an implementation that satisfies the self-contained conversion contract
in [workflows.md](references/workflows.md). Do not assume a command named by a
repository example is installed.

## Fast route

1. **Classify the input.** Verify that a local TFDS/RLDS build is already
   present and that it has a `train` split. Do not treat a dataset URL, archive,
   or a partial download as a ready raw directory.
2. **Derive identity from the path.** If the raw basename is a strict
   `major.minor.patch` version, use its parent as `dataset_name`; otherwise use
   the basename as `dataset_name`. This exact spelling controls both TFDS
   builder lookup and OXE lookup.
3. **Look up the exact dataset name.** Read
   [oxe-configurations.md](references/oxe-configurations.md). It provides the
   catalogued state/action encoding, default frequency, robot type, state-key
   plan, and transform coverage. Do not invent an alias.
4. **Inspect a representative decoded step before writing.** Check task,
   action, configured state keys, time dimension, and RGB candidate keys. For a
   known configuration, the transform must run before state keys are read.
5. **Freeze the feature contract.** Write `observation.state` with eight
   float32 values. Choose the action shape from the configured action encoding,
   and include only supported RGB-like observations. Depth needs an explicit
   alternative plan because the distilled converter excludes it.
6. **Choose storage deliberately.** `--use-videos` changes every selected RGB
   feature to video storage; without it, features are images. Size writer
   processes and threads conservatively, then make a local-only staging run.
7. **Review locally before publication.** Inspect episode count, feature names,
   shapes, FPS, robot type, a few decoded frames, and task text. Only then make
   a separate, explicit decision to push to the Hub.

See [workflows.md](references/workflows.md) for the full data and CLI/API
contract. See [troubleshooting.md](references/troubleshooting.md) at the first
failed preflight rather than guessing an OXE mapping.

## Required preflight record

Before a conversion writes frames, record all of the following:

| Item | Required decision |
| --- | --- |
| Raw directory | Existing local TFDS data root and whether its final component is a strict semantic version |
| Dataset name | Exact derived TFDS/OXE identifier; no inferred spelling changes |
| Configuration | Catalogued entry, or an explicit unsupported-dataset decision |
| Standardizer | Exact OXE transform or an explicit statement that none exists |
| Modalities | Available RGB-like keys, excluded depth keys, expected height/width/channels |
| State/action | Transformed state-key availability, expected time length, state width 8, action width |
| Metadata | Explicit or catalogued FPS and normalized robot type |
| Output | New staging parent, derived child destination, storage mode, writer concurrency |
| Publication | Local review owner; `repo_id` and Hub consent only if publishing is approved |

If any row is unknown, stop before output creation. An unrecognised dataset
falls back to all-zero state, unknown robot type, and 10 FPS in the distilled
behavior; that fallback is diagnostic, not an acceptable production default.

## Dataset identity and configuration

For a raw path ending in `droid/1.0.0`, the identity is `droid` at version
`1.0.0`; the TFDS data root is the directory above `droid`. For a path ending in
`droid`, identity is `droid` with no version and the TFDS data root is its
parent. The derived output child uses `<dataset>_<version>_lerobot`, including
the empty-version separator when no version was detected.

A configuration maps one exact dataset name to state-key pieces, state/action
encoding, control frequency, and robot type. It is not merely descriptive: the
state builder concatenates configured state pieces and inserts a zero column for
each `None` placeholder. Standard transforms are a separate registry. A name
can be configured without a transform, transformed without a configuration, or
in neither registry; treat each case explicitly.

## Feature and modality decisions

The contract selects observations whose key contains lowercase `image` or
`rgb`, excluding any key containing lowercase `depth`. It preserves the TFDS
feature shape and labels selected channels as RGB. Therefore:

- Do not claim depth conversion merely because an OXE configuration lists a
  depth observation. The reference path does not create a LeRobot depth
  feature or write depth frames.
- Do not assume every listed configuration camera is emitted. Feature selection
  is based on actual builder observation keys and a case-sensitive name filter.
- Verify channel order. Some OXE standardizers reverse BGR observations to RGB;
  an unknown dataset receives no such correction.
- Each selected image feature is either `video` or `image` according to the
  chosen storage mode, with shape taken from the builder.

## State, action, and task invariants

The state output is always an eight-wide float32 vector. For a known mapping,
each configured observation key contributes its transformed array; a `None`
entry contributes a one-wide zero column. The concatenation only produces width
eight if the source pieces have the expected widths. Validate rank, width, and
time length before writing.

The current catalog uses 7-wide end-effector actions (`EEF_POS`) or 8-wide
joint-position actions (`JOINT_POS`). Action values are standardized first when
a transform exists and then cast to float32; the conversion path does not pad,
truncate, or otherwise repair action arrays. Task text is taken from
`language_instruction`; it must exist after standardization and be decodable.

Detailed encoding names, padding behavior, catalog entries, and catalog
asymmetries are in [oxe-configurations.md](references/oxe-configurations.md).

## Safe interface check (`openx-help`)

When assessing a candidate converter without processing data, invoke its help
mode only after confirming imports can resolve. Its interface should expose
`--raw-dir`, `--local-dir`, `--repo-id`, `--push-to-hub`, `--robot-type`,
`--fps`, `--use-videos`, `--image-writer-process`, and
`--image-writer-threads`. Help success establishes parser surface only; it does
not prove TFDS access, data validity, LeRobot compatibility, or output safety.

Do not silently substitute a candidate whose flags differ. Map its API or CLI
to the contract in [workflows.md](references/workflows.md), and record every
semantic difference, especially output deletion, modality selection, and Hub
privacy defaults.

## Publication gate

`--push-to-hub` must remain absent until the local dataset passes review. A
push requires a nonempty repository identifier and valid authentication, but
those facts do not make publishing safe. The distilled behavior publishes
publicly, pushes videos, applies an Apache-2.0 license field, and uses tags that
include `LeRobot`, the dataset name, `rlds`, and sometimes `openx`/robot type.
Confirm those publication semantics independently before enabling it.

## Evidence basis and limits

This guide distills the repository's OpenX README, RLDS-to-LeRobot entrypoint,
OXE configuration catalog, standard-transform registry, and transform utility
rules. The catalog contained 70 configuration entries and 73 transform entries
when reviewed. No conversion, data download, writer run, simulator, cluster,
or Hub operation was performed while constructing this guide.

The guide does not establish that every external dataset is obtainable, that
all configurations work with a current TFDS release, or that a present LeRobot
release is API-compatible. Keep those as runtime verification tasks.
