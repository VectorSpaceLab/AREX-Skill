# RLDS export workflows

This reference is a self-contained operating recipe for planning a LeRobot to
RLDS/TFDS export. It preserves the observable behavior of the evidence exporter
without copying its conversion wrapper or making the source checkout a runtime
dependency.

## 1. Plan the output

Capture these values before launching a writer:

| Field | Required decision | Guardrail |
|---|---|---|
| Source | Local LeRobot dataset root | Must contain readable LeRobot metadata and episode records |
| Destination | New TFDS/RLDS directory | Do not reuse an unrelated or partially written tree |
| Builder name | `task-name` | Use a stable identifier; it is not a source-task filter |
| Version | `x.y.z` | Increment when the output schema or content contract changes |
| Image encoding | `jpeg` or `png` | PNG is lossless; JPEG is smaller but lossy |
| Citation/homepage | Optional provenance | Keep values stable and text-safe |
| Descriptions | Optional catalog text | Supply `overall-description` and `description` intentionally |
| Runner | Direct or Beam | Direct is the safe default; Beam requires explicit approval |

The output is built with an RLDS dataset configuration and TFRecord file format.
The source workflow exposes one `train` split. Do not call the output complete
until the generated metadata and counts have been inspected.

## 2. Direct mode (recommended first)

Use direct mode when the dataset is small, episode preservation matters, or the
source has not yet been validated. The conceptual invocation is:

```text
<rlds-exporter> \
  --src-dir <local-lerobot-root> \
  --output-dir <new-rlds-root> \
  --task-name <builder-name> \
  --version <x.y.z> \
  --encoding-format <jpeg-or-png> \
  [--citation <text>] [--homepage <url-or-text>] \
  [--overall-description <text>] [--description <text>]
```

`<rlds-exporter>` is deliberately a placeholder: this skill does not ship a
full wrapper. Run an approved equivalent implementation only after preflight
and a destination review.

The direct path should:

1. Load source metadata once to derive a schema.
2. Walk source steps in episode order.
3. Start a new `steps` list for each source episode.
4. Emit an episode when the next episode index is observed.
5. Mark the final step of the final episode before returning.
6. Call TFDS preparation with local output settings and no GCS download.

Direct grouping needs explicit validation. The evidence implementation assumes
ordered episode indices starting at zero and uses a current episode accumulator.
A source with missing, reordered, or nonzero-first episode ids can be grouped
incorrectly unless the implementation instead groups by metadata episode keys.
Treat that as a preflight failure, not as a reason to silently relabel data.

## 3. Beam DirectRunner mode (optional)

Enable Beam only when the user accepts the possibility of incomplete output and
has a dataset large enough to benefit from parallel episode processing:

```text
<rlds-exporter> \
  --src-dir <local-lerobot-root> \
  --output-dir <new-rlds-root> \
  --task-name <builder-name> \
  --enable-beam \
  --beam-run-mode multi_processing \
  --beam-num-workers <positive-count>
```

The evidence workflow creates a Beam collection from source metadata episode
keys and processes one episode per Beam element with a TFDS `DirectRunner`.
Its accepted run modes are `multi_processing` and `multi_threading`; the
observed defaults are `multi_processing` and five workers. Keep worker count
below the available CPU and memory budget, especially when multiple image
streams are decoded.

Operational rules:

- Install Apache Beam only for this route. A direct export must not fail merely
  because Beam is absent.
- Start with `multi_processing`. The source workflow warns that threading can
  have sharding and saving issues.
- Record the exact mode, worker count, source episode ids, and output episode
  ids. Compare them after writing.
- A warning about possible episode loss is a correctness warning, not a benign
  performance note. If one episode is absent, discard the Beam result and rerun
  direct; do not merge partial outputs.
- Do not attach a remote runner, Ray cluster, or Hub push to this workflow.
  Beam here means TFDS DirectRunner controls only.

## 4. Metadata customization

The exporter derives an RLDS configuration from source features and adds:

- `citation`
- `homepage`
- `overall_description`
- `description`

All default to an empty string in the evidence implementation. Keep citation
and homepage provenance truthful. Use descriptions to state the source robot,
task scope, frame rate if known, image encoding, and any filtering. Do not claim
that `is_terminal` represents a simulator termination reason unless the source
contains such a field and the schema was intentionally extended.

`task-name` and `version` become builder metadata. They are not the same as the
per-step task text. A dataset containing multiple task strings should retain
the per-step text and use a builder name that describes the output collection.

## 5. Small-dataset Beam decision case

For a three-episode synthetic or real dataset, choose direct mode even if Beam
is installed. The acceptance record should say:

- Beam is disabled because episode loss is unacceptable and parallel overhead is
  unnecessary.
- Each episode has one `is_first`, one `is_last`, and one `is_terminal` marker.
- Output episode ids and lengths equal the source metadata.
- The task string appears as `language_instruction` on every step where the
  source provides it.

If the user insists on Beam for this case, require a direct baseline first,
write Beam into a separate destination, and compare ids, lengths, schemas, and
representative tensors before using it.

## 6. Retry and handoff

For a failed direct run, preserve logs and the partial tree outside the planned
final destination, then validate the source again before retrying. For a Beam
run, always treat a missing episode, truncated step list, or inconsistent count
as a failed conversion. The final handoff should include:

- source and output identifiers (not private absolute paths in reusable notes),
- builder name and version,
- encoding and metadata values,
- runner mode and worker count,
- source/output episode and step counts,
- schema and boundary-marker checks,
- known omissions or unresolved compatibility gates.

The source script is **adapted/reference-only**. No conversion script is copied
because it imports version-sensitive LeRobot/TFDS APIs and performs potentially
large output writes.
