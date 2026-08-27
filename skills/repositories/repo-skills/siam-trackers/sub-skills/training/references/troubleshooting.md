# Training Troubleshooting

Use the smallest bounded probe that reproduces the symptom. Do not repeatedly
start the long training entry point as a diagnostic.

## Symptom Matrix

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| Default config file not found | Entry-point default names a config that is not guaranteed to exist | Pass an explicit copied YAML with `--cfg`; validate it first |
| `train_dataset` referenced before assignment | `BAN.BAN` is false | Select a matched BAN-enabled variant; do not just toggle it without channel/head checks |
| Model has no `ban_head` | `BAN.BAN` false or head construction mismatch | Confirm BAN config and variant implementation through **variant-catalog** |
| Annotation file missing | Relative path anchored to wrong cwd, empty inherited path, or absent data | Launch from project root; set every active dataset path; rerun checker with `--project-root` |
| `KeyError` for a padded frame | Annotation frame keys are not six-digit strings | Regenerate/copy the annotation index with six-digit keys; do not rename data in place without a migration plan |
| `NoneType`/shape error near bbox extraction | `cv2.imread` returned `None` for a missing/corrupt crop | Build exact `<frame6>.<track>.x.jpg`; decode one file before dataset construction |
| Dataset load hangs or is huge | Very large JSON/index plus high `NUM_USE`/`VIDEOS_PER_EPOCH` | Probe one dataset and lower worker count; use a deliberate small copied config for bounded diagnosis |
| `num_per_epoch` zero or division failure | Too few samples for batch × world size | Increase valid epoch sample count or reduce per-process batch; validate divisibility |
| DataLoader worker exited | Annotation/crop error, shared-memory limit, OpenCV issue, or excessive workers | Set `NUM_WORKERS=0`, reproduce one index, then increase gradually |
| `np.float` attribute missing | Legacy augmentation uses removed NumPy alias | In a maintained runtime, replace the deprecated alias with an explicit supported float dtype and verify crop numerics; do not downgrade blindly |
| CUDA unavailable despite `CUDA: true` | Driver/runtime mismatch or no assigned GPU | Run allocation smoke; solve against actual driver/hardware; stock training has no CPU fallback |
| All jobs use GPU 0 | Multiple stock processes ignore local rank | Stop duplicates; use one exposed GPU, or build and verify a real distributed adaptation |
| CUDA out of memory | Batch too large, competing process, variant footprint, worker pinning | Confirm ownership, lower batch in copied config, restart cleanly; revisit LR only as an explicit experiment |
| Head/neck channel mismatch | Config profile does not match selected backbone/head implementation | Route to **variant-catalog**; restore matched channels and imports as one unit |
| Classification or localization shape mismatch | Wrong `OUTPUT_SIZE`, stride, base size, or variant implementation | Compare complete variant geometry; heuristic mismatch alone does not justify editing V3 |
| Loss is NaN/Inf/greater than `1e4` but loop continues | Invalid boxes, extreme augmentation, numerical issue, bad weights/LR | Stop; inspect real batch, labels, component losses, gradients, and boxes. The loop silently skips updates |
| No backbone gradients | Expected before `BACKBONE.TRAIN_EPOCH`, wrong layer names, or unsafe resume at transition | Check epoch/layer existence and optimizer groups; use post-transition checkpoint or migrate explicitly |
| LR restarts or is wrong after resume | Scheduler not in checkpoint or YAML `START_EPOCH` mismatches | Set start epoch before scheduler construction; compare first resumed LR against recorded run |
| Optimizer group mismatch on resume | Architecture/toggle changed or transition checkpoint captured pre-unfreeze optimizer | Restore original config; prefer next boundary after unfreeze; otherwise perform a reviewed migration |
| Missing final expected checkpoint | Epoch boundary inference, interruption, output path, or completion assumption | Inspect logs and snapshot directory; do not infer completion from last visible batch |
| Logs/snapshots overwritten | Reused relative output directories or multiple rank-0 impostors | Stop, isolate output paths, preserve evidence, and relaunch only after collision review |

## Configuration Errors

### Empty inherited dataset paths

The default active dataset list is broad, while only the GOT record has
non-empty default paths. A YAML that omits `DATASET.NAMES` can inherit all names
and fail on an empty annotation path. A V2/V3-style list also requires the
operator to provide roots/annotations for every non-GOT dataset.

Recovery:

1. Decide the intended dataset mix; do not infer it from available disk names.
2. Set `DATASET.NAMES` explicitly.
3. Supply all four fields for each enabled record.
4. Validate with project-root path checks.
5. Probe one record and crop for each dataset, including cross-dataset negative
   sampling.

### BAN disabled

This is not an optional training toggle in the maintained control flow. The
loader is assigned only when BAN is enabled, and the model forward requires a
BAN head. Select a matched profile rather than changing a lone boolean.

### Geometry warning

The checker reports the historical formula:

```text
(SEARCH_SIZE - EXEMPLAR_SIZE) / STRIDE + 1 + BASE_SIZE
```

Base defaults and V1/V2 match it; V3's maintained output size is one smaller.
Do not "fix" V3 to 16 without proving the actual model outputs. Conversely, do
not suppress a mismatch in a custom architecture without a bounded forward
shape check.

### Unknown or misspelled keys

The runtime config system rejects many unknown fields, while dataset mappings
are more permissive. A misspelled dataset key can therefore survive until file
or attribute access. Use the checker, preserve case, and treat warnings as
errors in automation after expected warnings are resolved.

## Data and Augmentation Failures

### Annotation shape

Expected nesting is `video -> track -> frame -> box`. The loader adds an
internal `frames` list after loading. Do not place unrelated metadata beside
frame keys within a track unless the loader has been deliberately extended;
non-digit keys are ignored during frame selection but may interact with other
logic.

Four-coordinate boxes are interpreted as corners and filtered on positive
width/height. Two-value boxes are interpreted as width/height. Other lengths
can pass initial filtering and fail later, so validate schema before launch.

### Crop naming

For frame integer `1` and track `00`, the exact filename is:

```text
000001.00.x.jpg
```

It lives below the video key's relative directory under the configured crop
root. Mismatches in padding, track formatting, video slashes, or suffix cause
OpenCV to return no image.

### Point labels are mostly ignored

`-1` means ignored, not negative. A malformed or tiny box can leave too few
selected points. Inspect counts of `-1/0/1`, target width/height, and finite
localization distances from a real sample. For an explicit negative pair,
positive count should be zero.

### Augmentation appears too strong

Shift and scale alter both crop and target; color offset is applied whenever its
probability succeeds; blur kernels can be as large as 45; flip mirrors the box.
Use a copied diagnostic config with probabilities reduced, seed fixed, and one
sample. Never modify dataset files to make one random sample pass.

## CUDA and Memory Failures

### Environment history is not an install recipe

Old dependency guidance was written for obsolete PyTorch/CUDA/Python-era
packages. It is useful for identifying package families, not safe pins.
Construct a modern environment from hardware/driver compatibility, then prove:

1. package consistency;
2. imports needed by training;
3. CUDA allocation on the assigned device;
4. model construction;
5. one real batch forward/backward.

A construction-time Python 3.13/PyTorch CUDA overlay passed allocation on one
free A100-class device, but no full training was run. Do not generalize that
probe to another driver, GPU, or package build.

### OOM after first batches

Check competing processes first. Then distinguish persistent parameter/optimizer
memory from transient activation spikes. Lower `BATCH_SIZE` in a copied config
and rerun bounded forward/backward. Because batch size changes optimization
semantics, record it and decide whether LR changes are an experiment; do not
apply an automatic scaling rule as fact.

### CPU fallback requested

Stock training cannot satisfy it: model and data use unconditional `.cuda()`.
A CPU port requires maintained code changes and bounded verification. Do not
claim that changing `CUDA: false` is sufficient.

## Loss and Optimization Failures

### Silent invalid-loss skipping

The loop accepts a loss only if it is finite and at most `1e4`. Otherwise it
skips backward and optimizer step without terminating. Diagnose by adding
external monitoring of step count or by a bounded harness; visible throughput
and TensorBoard time values do not prove updates occurred.

Check, in order:

1. decoded images and finite boxes;
2. class label counts and localization distance ranges;
3. raw head output shapes/ranges;
4. component losses;
5. loaded weight compatibility;
6. configured LR and loss weights;
7. gradient finiteness before clipping.

### Backbone never unfreezes

Before `BACKBONE.TRAIN_EPOCH`, this is expected. At the transition, every name in
`TRAIN_LAYERS` is accessed as an attribute of the backbone. Empty or wrong names
leave layers frozen or raise an attribute error. The optimizer is rebuilt only
at the exact transition in an uninterrupted run.

On resume, align `START_EPOCH` before optimizer/scheduler construction. The
checkpoint saved exactly at the transition precedes optimizer rebuilding; use a
later boundary when possible.

### Warmup/scheduler index errors

Require `0 <= START_EPOCH < EPOCH` and `0 <= LR_WARMUP.EPOCH < EPOCH` when
warmup is enabled. Scheduler keyword start/end learning rates must be positive.
For step schedules, ensure `step` is positive. Resume reconstructs this schedule
from YAML, so preserve it exactly.

## Checkpoint Recovery

Never load an untrusted Torch checkpoint: deserialization can execute pickle
payloads. In an isolated environment, verify the checkpoint contains `epoch`,
`state_dict`, and `optimizer`; record key overlap and parameter-group counts.

If recovery fails:

- **File assertion:** fix copied config path/cwd; do not rename an unrelated
  checkpoint into place.
- **No used model keys:** wrong architecture or prefix transformation; return to
  matched variant.
- **Optimizer groups differ:** config or trainability changed; use model-only
  initialization for a deliberate new run, or build a reviewed optimizer-state
  migration.
- **LR differs:** set `START_EPOCH` to checkpoint epoch before startup and match
  original LR/warmup fields.
- **Transition epoch:** prefer `checkpoint_e<TRAIN_EPOCH+1>` if it exists and is
  valid, because its optimizer should include post-unfreeze groups.

Do not call a model-only load a resume. It restores neither optimizer nor epoch.

## Distributed Failure or Request

The presence of distributed utility classes is not proof of a distributed
entry point. Stock startup hardcodes one rank/world size, and local rank is
unused. Symptoms include duplicated batches, all processes writing one log,
all processes saving the same checkpoint, or all allocating logical GPU 0.

Stop all duplicate processes and preserve outputs separately. Continue only as
single-process, or send a distributed adaptation through implementation review
with rank/device initialization, sampler behavior, reduction semantics, epoch
math, and two-rank verification. Do not improvise a launcher flag around the
stock program.

## When to Route Elsewhere

- Successful training but poor benchmark metrics: **evaluation**.
- Checkpoint works in training but not frame tracking: **inference**.
- ONNX conversion, speed, FLOPs, or mobile deployment: **export**.
- Unsure which profile, head implementation, channels, or historical tracker to
  train: **variant-catalog**.
