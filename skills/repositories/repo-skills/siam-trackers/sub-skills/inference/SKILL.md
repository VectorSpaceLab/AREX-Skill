---
name: inference
description: "Build and run NanoTrack V1/V2/V3 for stateful image or video
  inference with safe model, config, device, frame, box, and output handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# NanoTrack Inference

Use this sub-skill for headless, single-object NanoTrack inference on an image
sequence or decoded video frames. It covers V1, V2, and V3 model construction,
checkpoint loading, tracker state, CPU/CUDA placement, and safe adaptation of a
demo loop.

## Route First

- Dataset protocols, benchmark runners, result files, metrics, or hyperparameter
  search: route to [evaluation](../../sub-skills/evaluation/SKILL.md).
- Training datasets, augmentation, losses, resume, or distributed launches:
  route to [training](../../sub-skills/training/SKILL.md).
- ONNX, NCNN, model splitting, latency, or deployment performance: route to
  [export](../../sub-skills/export/SKILL.md).
- SiamFC, SiamBAN, Ocean, or any snapshot other than the maintained NanoTrack
  workflow: route to
  [variant-catalog](../../sub-skills/variant-catalog/SKILL.md).

Do not use this sub-skill to claim benchmark quality, training recovery, export
correctness, or speed. Those require different assets and verification.

## Read By Need

- Public classes, config fields, variant matrix, and input/output contracts:
  [API reference](references/api-reference.md)
- Complete model setup and headless frame-loop patterns:
  [workflows](references/workflows.md)
- Failure diagnosis and safe recovery:
  [troubleshooting](references/troubleshooting.md)
- Deterministic preflight/config generator:
  [`nanotrack_demo_check.py`](scripts/nanotrack_demo_check.py)

## Non-Negotiable Inference Order

1. Choose exactly one variant: `v1`, `v2`, or `v3`.
2. Start a fresh Python process when changing variants. NanoTrack uses one
   mutable module-global `cfg`; merges are not isolated.
3. Merge the matching YAML before constructing `ModelBuilder()`.
4. Select the matching `ban_v1`, `ban_v2`, or `ban_v3` head implementation.
   YAML alone does not select the head implementation.
5. Resolve one device, set `cfg.CUDA` from that choice, and move the model to
   the same device.
6. Construct `ModelBuilder()` with no arguments, load the matching checkpoint,
   call `.to(device).eval()`, then call `build_tracker(model)`.
7. Validate a BGR `numpy.ndarray` frame and a zero-based `[x, y, w, h]` box.
8. Call `tracker.init(first_frame, box)` once, then call
   `tracker.track(next_frame)` in temporal order.
9. Consume `result["bbox"]` and `result["best_score"]`; validate them before
   drawing, serializing, or feeding another system.

Never copy a demo's unconditional `.cuda()`, implicit current-directory paths,
GUI creation, webcam access, warm-up frame skipping, or output writer side
effects into a library/server workflow.

## Fast Preflight

The bundled checker does not import NanoTrack, download weights, decode video,
or open a window. Its default is a deterministic CPU synthetic case:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py
```

Validate explicit inputs:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py \
  --variant v3 \
  --frame-shape 720 1280 3 \
  --bbox 410 180 120 96 \
  --device cpu \
  --config /path/to/config.yaml \
  --checkpoint /path/to/nanotrackv3.pth \
  --require-checkpoint --json
```

Generate a self-contained inference-only YAML rather than copying historical
training configuration:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py \
  --variant v2 --write-config ./nanotrack-v2-inference.yaml
```

Generation is explicit and refuses to overwrite by default. It writes no
checkpoint and performs no network access.

## Variant Decision

- Choose **V1** only with a V1 checkpoint and `ban_v1` head.
- Choose **V2** only with a V2 checkpoint and `ban_v2` head.
- Choose **V3** only with a V3 checkpoint, `ban_v3` head, 96-channel
  backbone/neck/head configuration, and output size 15.
- V1 and V2 both use the 64-channel backbone path and output size 16, but their
  head code, checkpoints, and tracking hyperparameters are not interchangeable.
- All maintained variant YAMLs use point stride 16. The core default is stride
  8 and is not the effective maintained variant setting.

See the exact values in [the variant matrix](references/api-reference.md#variant-matrix).

## Stateful Lifecycle

`NanoTracker(model)` owns position, target size, channel mean, Hanning window,
and point-grid state. `init` also calls `model.template(...)`, which stores the
template feature on the model itself. Consequences:

- `track` before `init` is invalid.
- Reinitialize for a new target, seek, scene cut, or new video.
- Preserve chronological frame order; the returned box updates the next search.
- Two trackers that share one `ModelBuilder` are not independent because the
  most recent `init` overwrites the model's template feature. Use one model per
  concurrent target or explicitly serialize and restore templates.
- Do not mutate geometry fields after tracker construction; its point grid and
  window were already derived from config.

## Frame And Box Gate

Accept frames only when all of these hold:

- `numpy.ndarray`, shape `[height, width, 3]`, nonempty, finite dimensions;
- BGR channel order, normally contiguous `uint8` from OpenCV;
- the same channel convention and compatible resolution across the sequence.

Accept initialization boxes only when they are four finite numbers in
zero-based `[x, y, width, height]` form with positive width and height. Prefer a
box fully inside the first frame. For a deliberately partial box, require a
nonempty intersection and make clipping policy explicit before `init`.

The returned box is a four-element floating-point `[x, y, w, h]` list. Internal
center/size clipping does not guarantee that every returned corner is inside
the image, so clip only at the consumer boundary when required. `best_score` is
the selected foreground softmax score; treat it as a confidence-like ranking
signal, not as a calibrated probability or benchmark metric.

## Device Contract

`cfg.CUDA` controls whether tracker crops call `.cuda()`. Model placement is
separate. They must agree:

```python
device = torch.device("cuda" if requested_cuda and torch.cuda.is_available() else "cpu")
cfg.CUDA = device.type == "cuda"
model = load_pretrain(ModelBuilder(), checkpoint_path)
model = model.to(device).eval()
```

If CUDA was explicitly required and unavailable, fail instead of silently
changing the experiment. If CPU fallback is allowed, set `cfg.CUDA = False`
before `init`; changing only the model device is insufficient.

## Evidence Limits

No checkpoint or dataset is bundled. The checker proves argument, profile,
config, frame-shape, box, and device-selection behavior only. Full tracking
requires a compatible checkpoint and real decoded frames. A backend
preparation smoke is not evidence of model/checkpoint compatibility or
end-to-end accuracy.
