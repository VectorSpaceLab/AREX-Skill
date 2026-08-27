# RoboMIND troubleshooting and recovery

Use this as a stop-and-diagnose guide. Preserve the source, planned output,
configuration snapshot, and logs. Do not retry by deleting a broad output root
or by changing feature shapes until the underlying evidence is recorded.

## Install and import failures

| Symptom | Likely cause | Safe response |
|---|---|---|
| `h5py`, OpenCV, NumPy, pandas, or PyArrow import fails | Incomplete inspection/runtime environment | Install into an isolated environment, then repeat import-only checks. Do not start data work while imports are unresolved. |
| LeRobot symbols cannot be imported from `lerobot.datasets` or `dataset_writer` | Source imports target a different LeRobot API layout | Check the installed version and resolve the compatible `LeRobotDataset`, metadata, writer, stats, and feature-validation APIs before conversion. Do not patch imports by guessing. |
| Depth statistics fail validation | Installed LeRobot expects three-channel image statistics | Verify whether the version supports one-channel depth statistics. Use a reviewed, version-specific compatibility change or omit depth explicitly; never falsify depth as RGB. |
| Video encoding fails after images load | Missing/unsupported codec or torch/video stack | Record codec and library versions, test the writer on an approved tiny fixture, and keep the episode unaccepted until encoded videos and stats can be inspected. |

The evidence environment facts are not a guarantee for another installation.
Python, LeRobot, OpenCV, h5py, PyArrow, torchcodec, Ray, and DataTrove versions
must be recorded per run. Ray and DataTrove are optional for the debug/local
planning path; their absence is not a reason to launch an unowned cluster.

## Optional dependencies and resources

- **Ray unavailable:** use `--debug` for the first task or an explicitly
  approved local equivalent. Do not silently fall back to a multi-process
  implementation whose memory behavior is unknown.
- **Ray starts an unexpected cluster:** stop before scheduling work. Confirm
  `--debug` is actually active, inspect Ray environment/address settings, and
  use a clean local runtime or an owned cluster only after approval.
- **Out of memory or worker eviction:** reduce task concurrency and/or
  `--cpus-per-task`, but size from the approximately 10 GiB per-task evidence
  estimate. CPU reservations alone do not cap image arrays. Resume only from a
  reviewed clean or intentionally partial output.
- **HDF5 file-lock errors:** the evidence Ray runtime disables HDF5 file locking
  for its workers. Apply that setting only when the filesystem and operator
  approve it; do not use it to hide concurrent writes to the same source file.
- **Slow conversion:** first confirm no task is being processed twice and that
  output/video encoding is the bottleneck. More Ray workers can increase memory
  pressure and does not guarantee linear speedup.

## Source and config validation

- **Benchmark rejected:** use exactly `benchmark1_0_release`,
  `benchmark1_1_release`, or `benchmark1_2_release`. Check spelling and that the
  release directory exists below the source root.
- **Embodiment rejected or empty config:** use one of the eight physical names
  in [embodiments](embodiments.md). Reject `sim_franka_3rgb` and
  `sim_tienkung_1rgb`; placeholders in a registry are not supported schemas.
- **Missing `h5_<embodiment>`:** the selected release does not contain that
  embodiment, or the source root is one directory too high/low. Fix the source
  selection, not the output path.
- **Missing task instruction:** confirm the CSV has `task` and `instruction`,
  normalize duplicates, and require an exact task match. Do not substitute the
  task folder name as language.
- **Missing JSON annotation:** preserve the null `action_config` fallback and
  report it. If a JSON record exists but its id is ambiguous, stop rather than
  attach a neighboring response.
- **Missing HDF5 key:** compare the config-derived paths under
  `observations/rgb_images`, `observations/depth_images`, `puppet`, and `master`.
  Do not add a camera or state field solely because another embodiment has it.
- **Unequal lengths:** reject or quarantine the episode. The evidence loader
  derives length from the first state and can fail later when another stream is
  indexed; a successful partial write is not valid.
- **Too-short episode:** fewer than 50 decoded frames is skipped by the source
  behavior. Record the path and length; do not pad it without an explicit
  dataset policy.

## Image, color, and shape failures

- **OpenCV returns `None`:** inspect the raw array dtype and byte count. Accept
  only the documented RGB counts 2,764,800 or 921,600 and depth counts 921,600
  or 307,200. Anything else is corrupt, differently encoded, or requires a
  new schema decision.
- **Colors look swapped:** check the embodiment-specific BGR policy. Reverse
  only RGB channels for Franka 1/3 RGB, dual Franka, and UR; never reverse depth
  and do not apply the policy to AgileX/TienKung by default.
- **Franka writer shape error:** first compare decoded top-camera shape against
  720x1280 and 480x640 alternatives. A safe plan can make one logged fallback,
  changing top depth with it. It must not resize pixels or recursively retry an
  unrelated writer error.
- **Left/right camera mismatch after fallback:** the top fallback does not
  alter Franka left/right declarations. Inspect those payloads independently.
- **Depth shape/stat error:** verify channel expansion to HWC `(H,W,1)`, the
  config shape, dtype, and LeRobot depth-stat compatibility. Omit depth only if
  the operator accepts that loss and the metadata records it.

## CLI and API misuse

- **No tasks in debug:** the first embodiment has no discoverable task or its
  success-episode tree is absent. Run a read-only inventory before selecting
  debug; do not call `next()` on an unverified task iterator.
- **`--cpus-per-task` is zero/negative:** reject before Ray initialization.
  Ensure total requested CPUs and memory fit the owned runtime.
- **Source equals output:** stop. The task writer removes existing per-task
  output directories and the custom dataset creation path also clears roots.
  Use a new destination or obtain explicit, narrowly scoped replacement
  approval after a backup.
- **Unexpected metadata import/API error:** confirm the exact LeRobot version
  and the location/signatures of dataset creation, video writer, stats,
  episode-validation, and metadata APIs. This converter uses custom subclasses;
  a superficially compatible import may still be unsafe.
- **Action config appears empty:** verify the JSON `id` filter, split token,
  task token, and parent-name mapping against the actual episode path. Empty
  config is a documented fallback, not proof that an annotation was found.

## Workflow-specific failure modes

- **Episode exception triggers repeated shape retries:** the source behavior
  recursively reruns the whole task after toggling the top shape. Stop and
  replace it with a bounded one-retry policy so an unrelated action/config or
  video error cannot loop indefinitely.
- **No accepted episodes deletes a task:** quarantine the empty output and
  preserve the skip list before cleanup. Never allow a typo in an annotation
  or key to look like a valid empty task.
- **Ray error log is missing:** remember that `output.txt` is relative to the
  process working directory, not necessarily the output root. Locate it from
  the run manifest and combine it with external stdout/stderr.
- **Train/validation ranges are wrong:** recount accepted episodes in traversal
  order. The metadata writer updates the train count as train episodes are
  saved and computes validation after it; partial or reordered retries can make
  ranges misleading.
- **Dirty task requested:** warn before conversion and require a policy: exclude
  it, include with a prominent caveat, or produce a separately named review
  dataset. Do not silently “correct” language or action order.

## Dirty-task caveats

The documented dirty list includes task ids such as
`3_eggplantOven`, `3_eggplantoven_2`, `5_eggoven_2`, `10_packplate`,
`10_packplate_2`, `11_brushcup`, `12_packcup`, `13_packbowl`,
`35_putcarrot`, `36_putpepper`, `37_putegg`, `39_puttomato`, `40_putavocado`,
`41_putplum`, `42_putkiwifruite`, `43_packplate`,
`44_putbluebowlongreenplate`, `45_putgreenbowlonblueplate`,
`46_putredbowlonwhiteplate`, `48_putpotatogreenplatefromsteam_2`,
`52_holdercup`, and `53_stackcup`. Reasons include missing instructions,
wrong action order, duplicate/missing objects or markers, a typo, and a
left/right-arm mismatch. The list is explicitly open-ended (“to be
continued”); absence from this list is not a cleanliness guarantee.

Record dirty-task selection separately from technical conversion success. A
successful LeRobot write does not make a semantically dirty demonstration
correct.

## Recovery and handoff

For a failed task, preserve the exception, episode path, config, decoded shape,
annotation decision, and output state. Retry only after changing one identified
cause, with a new or quarantined destination. Before handoff, report accepted
and skipped episode counts, dirty-task policy, output replacement status,
feature/color/depth checks, split ranges, action-config coverage, executor and
resource settings, and unresolved API or codec limitations.
