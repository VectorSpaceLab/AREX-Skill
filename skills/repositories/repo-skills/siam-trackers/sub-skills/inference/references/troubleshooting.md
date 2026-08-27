# NanoTrack Inference Troubleshooting

Start with the bundled deterministic checker. It separates argument/config/asset
failures from model execution:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py \
  --variant v2 --config /path/to/config.yaml \
  --checkpoint /path/to/model.pth --require-checkpoint \
  --frame-shape 480 640 3 --bbox 100 80 90 120 --device cpu --json
```

## Symptom matrix

| Symptom | Likely cause | Diagnose | Recovery |
|---|---|---|---|
| Config or checkpoint `FileNotFoundError` | Implicit current directory or missing asset | Print the caller-resolved path; run checker with the same explicit path | Supply an existing path. Do not download or guess a default. Generate inference YAML with `--write-config` if only config is missing. |
| `load NONE from pretrained checkpoint` | No overlapping state-dict keys | Inspect checkpoint top-level shape and key prefixes; verify selected variant | Pair V1/V2/V3 config, head, and checkpoint. Do not bypass the assertion. |
| Many missing/unused keys but load returns | `strict=False` permits partial load, wrong head/version, or checkpoint wrapper mismatch | Capture loader logs and compare model/checkpoint key sets | Treat unexpected architecture keys as failure; correct the pairing and rebuild in a fresh process. |
| CPU model with CUDA input, or inverse | `cfg.CUDA` and model placement disagree | Print `cfg.CUDA`, parameter device, and requested device before `init` | Set `cfg.CUDA = (device.type == "cuda")`, then `model.to(device)`. Recreate tracker. |
| `.cuda()` raises on a CPU host | Demo behavior was copied unchanged | Search adaptation for unconditional `.cuda()` | Replace with explicit device resolution and `.to(device)`; set `cfg.CUDA=False` on CPU. |
| CUDA requested but unavailable | Runtime/backend mismatch | Check `torch.cuda.is_available()` and framework build | If CUDA is required, fail clearly. If fallback is allowed, choose CPU before construction. |
| `AttributeError` involving `zf`, `center_pos`, `size`, or `channel_average` | `track` called before `init`, or state discarded | Log lifecycle events and tracker identity | Call `init` once on the actual first frame/box; do not call `track` until it succeeds. |
| Tensor/channel/shape error in head | Config and head variant mismatch | Check head module, backbone type, neck/head channels, output size | V1: `ban_v1`/64/16; V2: `ban_v2`/64/16; V3: `ban_v3`/96/15. Restart and rebuild. |
| Window/point vector and prediction sizes differ | Wrong `TRACK.OUTPUT_SIZE`, stale config, or config mutated after tracker creation | Compare prediction spatial side with tracker output size, point count, and window length | Use 16 for V1/V2, 15 for V3. Start fresh and set config before `NanoTracker`. |
| Result jumps after initializing another target | Trackers share one model and therefore one `model.zf` | Check object identity of `tracker_a.model` and `tracker_b.model` | Use a separate model per simultaneous target or implement locked template restoration. |
| Poor/erratic tracks despite valid tensors | RGB passed as BGR, wrong box convention, skipped first video frames, or wrong checkpoint | Validate channel provenance, box, frame ordering, and asset pairing | Convert color explicitly, use `[x,y,w,h]`, initialize on first yielded frame, and fix asset pairing. |
| OpenCV assertion during crop/resize | Empty/invalid frame, malformed dimensions, extreme/invalid box | Check decode result, HWC shape, dtype, finiteness, and box intersection | Reject the input before tracker calls. Do not pass `None`, grayscale, CHW, or zero-area arrays. |
| Box appears off by width/height | Corners supplied as size, or one-based coordinates | Compare input semantics with `[x,y,w,h]`, zero-based | Convert explicitly at the boundary and reinitialize. |
| Negative output top-left near an edge | Tracker clips center and size, then derives top-left | Check `x`, `y`, `x+w`, `y+h` | Preserve raw float output for records; clip the visualization rectangle at the consumer boundary. |
| GUI/webcam/video writer appears unexpectedly | Interactive demo side effects were copied | Search for OpenCV window/camera/writer calls | Keep decode, display, and save behind explicit flags; headless inference should consume arrays only. |
| Config change has no effect or mixes versions | YACS global config was merged repeatedly; imports/registry are stale | Print effective profile and head class module | Use one variant per fresh process. Patch head registry before model construction. |

## Missing weights

No maintained inference can produce meaningful boxes without trained weights.
The safe behavior is:

1. validate the requested variant and config;
2. require an explicit checkpoint path;
3. verify the file exists and comes from a trusted source;
4. pair it with the same version's head/config;
5. load on CPU storage, inspect key-overlap logs, then move the model;
6. run a one-init/one-track fixture before application integration.

Do not silently continue with random `ModelBuilder()` parameters. The code can
execute but outputs have no useful tracking meaning. Do not make the checker or
application download weights automatically.

## CPU/CUDA mismatch

There are two independent device controls:

- `cfg.CUDA`: crop tensors call `.cuda()` when true;
- `model.to(device)`: parameters and stored template features follow the model.

Correct setup:

```python
if requested == "cuda" and not torch.cuda.is_available():
    raise RuntimeError("CUDA required but unavailable")
device = torch.device("cuda" if requested == "cuda" else "cpu")
cfg.CUDA = device.type == "cuda"
model = load_pretrain(ModelBuilder(), checkpoint_path).to(device).eval()
tracker = build_tracker(model)
```

For `auto`, resolve once and log the decision. Do not move the model after
`init`; that can leave cached template state inconsistent. Rebuild and
reinitialize when device policy changes.

A successful generic CUDA operation proves backend preparation only. It does
not prove a checkpoint, selected architecture, crop path, or complete frame
loop.

## Invalid frame

Reject before `init` or `track` when any holds:

- decoder returned `None`;
- rank is not 3 or channel count is not 3;
- height or width is zero;
- layout is CHW instead of HWC;
- dtype/range conversion is implicit or lossy;
- color provenance is RGB/unknown rather than BGR;
- frame belongs to a different stream or is out of temporal order.

The crop implementation uses a `uint8` padding buffer. A non-`uint8` frame can
be truncated during edge padding even if a centered crop appears to work.
Normalize/scale deliberately, cast to `uint8`, make contiguous, and document the
color conversion before inference.

## Invalid initialization box

Reject NaN/infinity, fewer or more than four values, non-positive width/height,
and boxes with no intersection with the frame. Prefer a fully in-frame box.

If the caller supplies corners:

```python
x1, y1, x2, y2 = corners
if x2 <= x1 or y2 <= y1:
    raise ValueError("invalid corner box")
xywh = [x1, y1, x2 - x1, y2 - y1]
```

If partial boxes are allowed, clip corners first, then derive positive width and
height. Never clamp width/height independently while leaving a completely
outside top-left coordinate.

## Stale imports and global config

Variant selection has two stateful parts:

1. the mutable global `cfg` merged from YAML;
2. the module-level `BANS` registry populated by a head implementation.

Historical V1/V2 YAML relies on core `TRACK.OUTPUT_SIZE=16`, while V3 sets 15.
Merging V3 and then V1 in one process can leave 15 because an absent YAML key
does not restore a default. Similarly, importing another head module does not
necessarily replace already registered classes.

The reliable recovery is a fresh process, then:

1. merge one variant YAML;
2. explicitly update both BAN registry entries from that variant's module;
3. set device flags;
4. build and load one model;
5. build one tracker.

Avoid attempts to delete selected entries from `sys.modules`; dependent modules
and the global config can remain stale.

## Output validation

After every `track`, check:

- mapping contains `bbox` and `best_score`;
- box has four finite numeric values;
- width and height are positive;
- score is finite and in `[0,1]`;
- frame index and stream identity are the expected next state transition.

A low score does not automatically define a lost-target condition. Choose any
reinitialization or suppression threshold for the target domain and validate it
on owned data; do not present `best_score` as calibrated.

## Video and image sequence mistakes

- A file-video warm-up loop discards frames and shifts the initial box. Do not
  warm up a file decode unless explicitly seeking.
- Sorting names by `int(stem)` crashes on nonnumeric stems. Require a naming
  contract or use stable lexicographic ordering with zero padding.
- Failed decode should stop with the exact offending input; yielding `None`
  defers the error into crop logic.
- Webcam access, display, ROI selection, and output writing are separate UI/I/O
  features. Keep all off by default.
- Release capture and writer resources in `finally` or context-managed code.

## Geometry/output mismatch diagnostics

For V1/V2, output side 16 implies 256 score points; for V3, side 15 implies 225.
At runtime, inspect only shapes and counts, not tensor values:

```python
expected = cfg.TRACK.OUTPUT_SIZE ** 2
assert tracker.points.shape == (expected, 2)
assert tracker.window.shape == (expected,)
```

If raw `cls` or `loc` spatial dimensions disagree with output size, stop. Likely
causes are a wrong head/backbone/checkpoint pair or stale geometry config.

## Dependency and ABI scope

Inference needs the Python NanoTrack modules, PyTorch, NumPy, OpenCV, YACS, and
a compatible checkpoint. A native evaluation extension is not part of the
ordinary `NanoTracker.init/track` path. Do not treat an unrelated prebuilt
native binary as inference proof, and do not route extension import failures
into model/device debugging. Benchmark-extension issues belong to evaluation.

Historical pinned dependency files document an old environment; they are
compatibility evidence, not an instruction to downgrade a working modern
runtime blindly. Resolve the smallest compatible environment for the requested
backend and verify the one-init/one-track fixture.
