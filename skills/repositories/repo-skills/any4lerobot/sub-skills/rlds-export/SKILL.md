---
name: "rlds-export"
description: "This skill exports LeRobot datasets to RLDS/TFDS with feature
  mapping, image and depth normalization, episode boundaries, metadata, and
  optional Apache Beam controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LeRobot → RLDS/TFDS export

Use this route when a user needs a local LeRobot dataset represented as an
RLDS/TFDS dataset for an RLDS consumer such as an offline-RL, imitation-learning,
or VLA pipeline. It covers the exporter contract and safe planning; it does not
ship or execute a full data-conversion wrapper.

## Boundary and routing

- **Input:** a readable local LeRobot dataset root with metadata, episodes, and
  the feature columns required by the requested RLDS schema.
- **Output:** a TFDS/RLDS dataset directory, normally with a `train` split and
  TFRecord storage, plus the requested dataset metadata.
- **Not covered:** RLDS/TFDS or Open X-Embodiment data converted *to* LeRobot.
  For that reverse direction, route to [openx-conversion](../openx-conversion/SKILL.md).
- Do not infer missing images, depth, state, action, episode lengths, or task
  text. Stop for a schema decision when a required field is absent or ambiguous.
- Treat an output directory as disposable until the plan confirms it is empty or
  separately approved for replacement. Never push to a Hub from this route.

Read the linked references before choosing flags:

- [Workflows and runner controls](references/workflows.md)
- [RLDS schema and feature mapping](references/data-formats.md)
- [Troubleshooting and recovery](references/troubleshooting.md)

## Required preflight

1. Confirm the source and destination are different, writable local paths. Keep
   the source unchanged and make a backup or new destination for retries.
2. Inspect LeRobot metadata without iterating frames: feature keys, shapes,
   dtypes, image/depth layouts, action cardinality, episode keys and lengths,
   and whether every frame has a task string.
3. Confirm the exporter-compatible LeRobot API. The evidence implementation
   imports `LeRobotDataset` and `LeRobotDatasetMetadata` from
   `lerobot.datasets.lerobot_dataset`; other LeRobot versions may expose these
   symbols elsewhere. Resolve this import before any conversion attempt.
4. Install TensorFlow and TensorFlow Datasets for TFRecord/RLDS generation. Keep
   Apache Beam optional unless the user explicitly accepts its trade-offs.
5. Decide direct versus Beam before writing. Direct mode is the default and the
   required choice for small datasets or lossless episode preservation.
6. Choose a valid TFDS builder name (`--task-name`) and semantic version
   (`--version`, `x.y.z`). Record the encoding and all descriptive metadata.

If any preflight item is unknown, produce a validation plan rather than starting
an export. Do not use a successful import as evidence that a real dataset maps
correctly.

## CLI contract

Use these arguments with the project’s equivalent exporter entry point; this
sub-skill intentionally does not provide a wrapper that performs large writes:

- `--src-dir PATH`: local LeRobot dataset root; required.
- `--output-dir PATH`: TFDS output directory; required and should be new.
- `--task-name NAME`: RLDS/TFDS dataset or builder name; required.
- `--version X.Y.Z`: dataset version; default `0.1.0` in the evidence workflow.
- `--encoding-format {jpeg,png}`: image encoding; default `jpeg`.
- `--citation TEXT`, `--homepage TEXT`: optional provenance metadata.
- `--overall-description TEXT`, `--description TEXT`: optional dataset
  descriptions; keep the distinction if downstream catalog tooling uses both.
- `--enable-beam`: opt into Beam; absent means direct generation.
- `--beam-run-mode {multi_threading,multi_processing}`: Beam DirectRunner mode;
  evidence default is `multi_processing`.
- `--beam-num-workers N`: Beam DirectRunner worker count; evidence default is 5.

Validate paths, version syntax, encoding choice, and positive worker count before
invoking the exporter. `--task-name` is metadata, not a filter for source task
strings; use a distinct name when the output is a differently scoped dataset.

## Conversion procedure

1. **Plan:** freeze source metadata, output path, schema decisions, metadata
   fields, and runner mode. Note whether a retry may reuse partial output.
2. **Build the schema:** map supported LeRobot observation image, depth, state,
   action, and task fields as described in `data-formats.md`. Reject unhandled
   feature kinds instead of silently dropping them.
3. **Normalize each step:** convert ordinary images to `uint8` HWC from LeRobot
   CHW values in `[0, 1]`; squeeze only a documented singleton depth channel;
   preserve state/action numeric dtype and shape; map task text to
   `language_instruction`.
4. **Group episodes:** use source episode identity and metadata lengths. Emit
   `is_first` on the first frame, and set both `is_last` and `is_terminal` on
   the final frame only. `is_terminal` here means “episode ended at the last
   available frame,” not a separately observed environment termination signal.
5. **Write:** use TFDS/RLDS metadata and TFRecord output in a new destination.
   Direct mode should be the first smoke path. Inspect counts and representative
   shapes before considering a larger run.
6. **Review:** verify the output split, episode count, step counts, metadata,
   image encoding, depth rank, and boundary flags. Only then publish or hand the
   directory to downstream tooling.

## Runner choice and recovery

- **Direct runner:** deterministic episode traversal, no Beam dependency, and the
  recommended path for small datasets. It is easier to diagnose because the
  regular generator walks the LeRobot dataset once and closes each episode when
  the episode index changes.
- **Beam DirectRunner:** optional parallel episode processing using
  `multi_processing` or `multi_threading` and a bounded worker count. Use only
  after a successful direct smoke test and when throughput justifies it.
- The evidence workflow warns that Beam can lose episodes while sharding or
  saving. Treat any Beam run as potentially incomplete: compare episode ids and
  counts, and rerun in direct mode if they differ. `multi_threading` has an
  additional sharding/saving warning; prefer `multi_processing` when Beam is
  approved.
- A failed or partial run is not a valid dataset. Move it aside, remove it only
  after confirming it is the intended output, and rerun from a clean destination.
  Do not “repair” missing episodes by editing boundary flags.

## Safe verification

Before a real export, perform only safe checks:

- **Help-only:** invoke the equivalent CLI with `--help`; confirm all listed
  flags and defaults without opening a dataset or creating output.
- **Import-only:** import TensorFlow, TFDS, and the selected LeRobot metadata API;
  import Apache Beam only when Beam is selected. Do not download datasets or
  instantiate a conversion builder during this check.
- **Synthetic mapping:** feed a tiny in-memory feature map and one or two
  synthetic step records to a mapping implementation. Assert image CHW→HWC and
  `[0,1]`→`uint8`, singleton depth behavior, state/action key mapping, task to
  `language_instruction`, and exactly one first/last/terminal marker per episode.
- **No native conversion:** do not run a real conversion, Beam job, download,
  Hub push, or large write as part of skill drafting or help verification.

Source basis: the Any4LeRobot LeRobot-to-RLDS README and its exporter module.
The source module is adapted into this contract and references only; no source
file, checkout path, or source script is a runtime dependency.
