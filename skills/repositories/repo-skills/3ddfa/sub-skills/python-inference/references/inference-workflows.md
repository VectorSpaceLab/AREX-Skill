# Inference Workflows

## Mental Model

Image inference follows this sequence:

1. Load the hard-coded checkpoint `models/phase1_wpdc_vdc.pth.tar` into `mobilenet_1(num_classes=62)`.
2. Build one or more face rectangles either from dlib detection or from `<image>.bbox`.
3. Convert each rectangle or dlib landmark set into a square-ish ROI box.
4. Crop the source image, resize the crop to `120x120`, convert to tensor, and normalize with mean `127.5` and std `128`.
5. Run a single MobileNet forward pass to produce a 62-float parameter vector.
6. Decode the parameter vector to 68 landmarks; if `--bbox_init=two`, recompute the crop from those landmarks and run one more forward pass.
7. Optionally decode dense vertices and downstream artifacts: PLY, OBJ, vertex `.mat`, pose box, depth, PNCC, PAF, and landmark visualization.

The model forward itself is lightweight; most fragility comes from startup imports, bbox/sidecar preparation, Cython render availability, GUI display, and output file expectations.

## Recommended Still-Image Flow

### 1. Preflight without native inference

From this sub-skill directory, run the diagnostic script first and point it at the 3DDFA checkout:

```bash
python scripts/inspect_3ddfa_inference.py --repo-root /path/to/3DDFA
```

Then run the MobileNet-only shape smoke:

```bash
python scripts/smoke_mobilenet_forward.py --repo-root /path/to/3DDFA --arch mobilenet_1 --num-classes 62
```

The smoke script imports only `mobilenet_v1` and `torch`, creates random `1x3x120x120` input, and checks that the forward output shape is `(1, 62)`. It does not load the checkpoint, dlib, rendering utilities, or the native image CLI.

### 2. Prefer bbox-driven no-detector inference when a bbox exists

For a user-provided or fixture bbox sidecar, use:

```bash
python main.py -f <image> --mode cpu --dlib_bbox=false --dlib_landmark=false --bbox_init=two --show_flg=false
```

This path avoids:

- running the dlib frontal face detector;
- loading `models/shape_predictor_68_face_landmarks.dat`;
- crop initialization from dlib landmarks.

It still requires the Python `dlib` module because the native image CLI imports `dlib` at top level before parsing arguments. It also requires the render Cython extension in an unmodified checkout because render utilities are imported at startup.

### 3. Use the dlib detector/landmark path only when model files are present

The default path (`--dlib_bbox=true --dlib_landmark=true`) needs:

- Python `dlib` module importable;
- dlib frontal detector available from the module;
- `models/shape_predictor_68_face_landmarks.dat` downloaded separately;
- all regular model/config/render resources.

Use this path for unknown images only if no bbox sidecar exists and the dlib landmark model is available.

## Output Selection Patterns

### Minimal landmark visualization

To reduce artifact volume while preserving the 68-landmark result:

```bash
python main.py -f <image> --mode cpu --dlib_bbox=false --dlib_landmark=false --show_flg=false \
  --dump_res=true --dump_pts=true --dump_ply=false --dump_obj=false --dump_vertex=false \
  --dump_pose=false --dump_depth=false --dump_pncc=false --dump_paf=false
```

Caveat: the native CLI still imports render code at startup, so disabling render outputs does not bypass a missing Cython extension unless the CLI is patched or wrapped.

### Dense geometry and mesh files

Use default `--dump_ply=true --dump_obj=true` or set `--dump_vertex=true` when the task needs dense vertices. Dense prediction is derived from the same 62 parameters and ROI box.

- `.ply`: ASCII mesh using triangle indices from `visualize/tri.mat`.
- `.obj`: OBJ vertices with sampled source-image colors.
- `.mat`: dense vertices under key `vertex`.

For low-level interpretation of vertex coordinate transforms, triangle indexing, texture sampling, or render internals, route to the geometry/rendering owner.

### Pose, depth, PNCC, and PAF

- Pose boxes are drawn once per image from all predicted faces.
- Depth and PNCC are per-image renders over all dense face meshes and require the Cython render path.
- PAF is per-face and writes both a crop and PAF image. PAF uses a kernel size such as `3`; legacy `np.int` usage can fail on modern NumPy.

## GPU Requests and CPU Fallback

The native CLI treats `--mode gpu` as the only CUDA path. It does not check CUDA availability before calling `.cuda()`. For GPU-related requests:

1. Run the bundled MobileNet smoke on CPU first to verify architecture/import basics.
2. If CUDA is available and the user explicitly asks for it, run the smoke script with `--device cuda` to validate only the model forward device path.
3. Do not claim native GPU inference is verified from CPU-only results.
4. If CUDA is unavailable, report a CPU-only verification and keep any GPU claim as unverified.

## Video Workflow Caveats

The video demo is an interactive PNCC overlay demo, not a production video writer.

Important caveats:

- It uses dlib detector and dlib landmark predictor on the first frame, then updates landmarks from subsequent predictions.
- It always uses PNCC rendering, so dense prediction, `visualize/tri.mat`, and the Cython render extension must work.
- It calls OpenCV GUI functions and writes no video file.
- Its `--video` argument is cast with `int(args.video)` before capture creation. Non-numeric file paths can fail before OpenCV sees them, and nonzero camera indexes may be passed as strings rather than integers.
- For headless or file-output video tasks, treat the demo as a behavioral template and use the command/reference facts here rather than assuming it is directly runnable.

## Native Candidate Checks for Verification Planning

Difficult cases worth testing after integration:

1. A bbox-only multi-face image where `<image>.bbox` has multiple rows, `--dlib_bbox=false`, `--dlib_landmark=false`, `--bbox_init=two`, and render-heavy outputs disabled. This checks the no-detector path, multi-face indexing, and two-pass ROI update without the dlib landmark model.
2. A user asks for GPU inference on a CPU-only host. The expected behavior is a clear CPU-only smoke verification plus an explicit unverified-GPU note, not a false success claim.
