# RLDS export troubleshooting

Use this matrix to classify failures before retrying. Keep the source read-only
and move partial outputs aside rather than appending to them.

## Installation and import

| Symptom | Likely cause | Safe response |
|---|---|---|
| `No module named tensorflow_datasets` | TFDS is not installed | Install `tensorflow-datasets` in the selected environment; verify import only, then retry |
| `No module named tensorflow` or TensorFlow runtime error | TensorFlow is absent or incompatible | Install a TensorFlow/TFDS pair supported by the environment; do not begin a conversion until both import |
| `No module named apache_beam` with Beam disabled | Optional dependency missing | No action; direct mode does not require Beam |
| `No module named apache_beam` with `--enable-beam` | Beam route selected without its extra | Install Apache Beam or remove `--enable-beam`; prefer direct mode for the first run |
| `cannot import LeRobotDataset*` | LeRobot API layout/version mismatch | Inspect the installed package and use the exporter-compatible metadata imports; do not patch by importing from the source checkout |
| TFDS/RLDS symbols differ | TFDS version drift | Pin a tested TensorFlow/TFDS pair in the environment and rerun help/import checks; record the compatibility gate |
| CUDA or GPU warnings during import | Optional accelerator probe or TensorFlow runtime setup | Export is CPU-oriented; disable or ignore GPU use only if the installed stack remains functional |

Never “fix” an import error by adding checkout-relative `sys.path` entries or
copying the original script into a runtime skill.

## Data and configuration validation

| Symptom | Likely cause | Safe response |
|---|---|---|
| Metadata cannot be read | Wrong root, incomplete LeRobot dataset, or incompatible format | Confirm the path points at the dataset root and inspect metadata files; stop if incomplete |
| Required feature is absent | Dataset lacks image, depth, state, action, or task data expected by the consumer | Decide whether the downstream schema allows omission; do not synthesize zeros without approval |
| Duplicate RLDS names | Different dotted keys collapse to one suffix name | Rename through an explicit schema adapter or reject the export |
| Image shape assertion fails | Source is HWC, missing channel, alpha/multichannel mismatch, or wrong metadata | Identify the actual layout and choose an explicit conversion policy; never transpose blindly |
| Image values are outside `[0,1]` | Already quantized or differently normalized source | Confirm source dtype/range, then adapt once; do not multiply arbitrary values by 255 |
| Depth squeeze fails or rank is wrong | Depth channel is not singleton `(1,H,W)` | Preserve a documented alternate schema or stop; do not squeeze a non-singleton axis |
| Depth is visibly saturated | Ordinary-image scaling was incorrectly applied | Restore depth as float32 tensor with source units; rerun from a clean output |
| State/action shape mismatch | Metadata and frame records disagree | Quarantine the source/output and inspect the first failing record; no silent reshape |
| Empty task text | Source task is missing, null, or not a string | Decide whether empty text is valid for the consumer; document it and validate all episodes |
| Nonzero or reordered episode ids | Direct grouping assumption does not hold | Use metadata-key grouping in an approved implementation or reject; do not relabel blindly |
| Episode length disagreement | Stale metadata or truncated frame files | Revalidate source integrity and compare counts before export |
| Empty episode emitted | Source contains zero-length episode or grouping bug | Reject unless the target consumer explicitly accepts empty episodes |

## CLI and API misuse

- A missing `--src-dir`, `--output-dir`, or `--task-name` is a plan error. Supply
  a readable source, a new destination, and a stable builder name.
- Keep `--version` in `x.y.z` form. Do not use a date, Git SHA, or LeRobot code
  version as a TFDS dataset version unless the builder explicitly accepts it.
- Use only `jpeg` or `png` for `--encoding-format` as exposed by the evidence
  parser. Encoding is not a resolution or color-space option.
- `--task-name` names the generated builder/dataset. It does not filter source
  frames by their `task` field. Filter before export only through a separately
  validated dataset operation.
- `--beam-num-workers` must be a positive, resource-appropriate integer. More
  workers can increase memory pressure from simultaneous image decoding.
- `--beam-run-mode` is a DirectRunner control and accepts only
  `multi_processing` or `multi_threading` in the evidence interface. It does not
  select a Ray runner or a remote Beam service.
- Do not pass a Hub id where a local `--src-dir` is expected. Materialize and
  validate a local LeRobot dataset first, subject to the user’s data policy.
- Do not treat `--description` or `--citation` as arbitrary shell syntax. Quote
  values safely and record them in the run plan.

## Workflow-specific failures

### Episode loss with Beam

The exporter warns that some episodes can be lost due to Apache Beam sharding
or saving behavior. Compare source and output episode ids, lengths, and total
steps. If any differ, mark the Beam result invalid, preserve diagnostics, and
rerun direct into a clean destination. For a small dataset, disable Beam rather
than tuning workers.

### Partial output after interruption

TFDS preparation may leave files and metadata in the destination. Do not resume
by assuming the partial tree is consistent. Rename it as a failed attempt or
remove it after confirming ownership, recreate the destination, and rerun the
preflight. Never mix episodes from direct and Beam attempts.

### Final-frame flags are wrong

Check whether records are ordered by episode and frame, whether `frame_index`
starts at zero, and whether metadata episode lengths are current. In direct mode,
verify the transition logic closes the previous episode and separately closes
the final accumulator. In Beam mode, verify each episode was loaded with the
correct metadata key. A final flag is not a substitute for recovering missing
frames.

### Unexpected JPEG artifacts

JPEG is lossy by design. If exact pixel values are needed, rerun with
`--encoding-format png` and compare output shapes and sample pixels. Neither
choice fixes a source that was already scaled or transposed incorrectly.

### TFDS attempts external access

The evidence flow disables GCS download attempts for preparation. If an
implementation tries to download data or contact GCS, stop and inspect its
configuration. This route expects local source data and does not authorize
network downloads during safe verification.

### Output appears valid but is semantically wrong

Shape checks can pass while camera names, task text, action alignment, depth
units, or terminal meaning are wrong. Compare representative source and output
records, retain feature names/docs, and ask the downstream consumer owner to
approve any schema semantic changes.

## Stop conditions

Stop rather than retrying when:

- LeRobot metadata and frame files disagree;
- a required backend is missing for the chosen strict route;
- a non-singleton depth channel has no approved target schema;
- episode ids or lengths cannot be reconciled;
- the destination is not owned or may contain an unrelated dataset;
- Beam loss is observed and the user still requests Beam-only output;
- the implementation would need source-checkout imports, Hub pushes, downloads,
  or a large unreviewed write.

Record the unresolved item, attempted safe checks, and the chosen recovery path.
The source exporter is reference-only/adapted; there is intentionally no bundled
conversion script to conceal these side effects.
