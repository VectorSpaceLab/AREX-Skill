# Python Inference Troubleshooting

## `main.py -h` fails before showing help

The native image CLI imports heavy optional modules at top level before argument parsing. If `dlib` or the Cython render extension is unavailable, even `-h` can fail.

Use the bundled diagnostic instead of probing help directly. From this sub-skill directory:

```bash
python scripts/inspect_3ddfa_inference.py --repo-root /path/to/3DDFA
```

Known startup blockers:

- Python `dlib` module missing.
- Cython render extension `mesh_core_cython` not built for the active Python.
- Required `train.configs` files missing.
- `visualize/tri.mat` missing.
- Torch/torchvision/OpenCV/scipy imports unavailable.

## No-dlib bbox inference still complains about dlib

`--dlib_bbox=false --dlib_landmark=false` disables use of the detector and landmark predictor, but the unmodified native CLI still imports the Python `dlib` package at process startup and uses `dlib.rectangle` to hold sidecar bbox rows.

Implications:

- You do not need `models/shape_predictor_68_face_landmarks.dat` for bbox-only inference.
- You still need the Python `dlib` module unless the CLI is wrapped or patched to replace `dlib.rectangle`.
- If the user cannot install dlib, report that bbox-only inference is blocked for the unmodified native CLI rather than claiming the flags remove all dlib dependency.

## Missing dlib landmark predictor

Default inference uses `--dlib_landmark=true`, which loads `models/shape_predictor_68_face_landmarks.dat`. That file is not bundled with the small default model checkpoint and must be obtained separately.

Workarounds:

- If a bbox sidecar exists, set both `--dlib_bbox=false` and `--dlib_landmark=false`.
- If no bbox exists, either provide one or install the predictor model before using the default detector/landmark path.

## BBox sidecar not found or malformed

When `--dlib_bbox=false`, the sidecar must be named exactly `<image path>.bbox`. For an image named `face.jpg`, the sidecar is `face.jpg.bbox`, not `face.bbox`.

Expected rows after the first count line:

```text
<face_id> <left> <top> <right> <bottom>
```

Common mistakes:

- Using commas or tabs instead of spaces.
- Omitting the ignored face-id column.
- Swapping top/right values because source variable names are misleading. Treat the four bbox columns as left, top, right, bottom.
- Supplying floats; the native parser expects integers.

## Cython render extension missing

Depth, PNCC, and the video demo use the Cython mesh render core. The unmodified native image CLI also imports render utilities during startup, so a missing extension can block even non-render commands.

Expected built artifact pattern:

```text
utils/cython/mesh_core_cython*.so
```

Build command from the repo documentation:

```bash
cd utils/cython && python setup.py build_ext -i
```

After switching Python versions, rebuild the extension because compiled suffixes are ABI-specific.

## Required `train.configs` resources missing

Landmark, dense vertex, PNCC, and PAF decoding import files from `train.configs`. Missing files can fail at import time or during decoding.

Check at least:

- `keypoints_sim.npy`
- `w_shp_sim.npy`
- `w_exp_sim.npy`
- `u_shp.npy`
- `u_exp.npy`
- `param_whitening.pkl`
- `Model_PAF.pkl`
- `pncc_code.npy`

Run the diagnostic script to list missing entries.

## GPU mode fails

`--mode gpu` directly calls `.cuda()` on the model/input. It does not auto-fallback inside the native CLI.

Safe handling:

1. Verify CPU architecture forward first with the bundled smoke script.
2. If CUDA is available and requested, run the smoke script with `--device cuda`.
3. If CUDA is unavailable, report CPU-only verification and leave native GPU inference unverified.

## Output files are missing or overwritten

Outputs are written beside each input image using the input stem. Re-running the same command overwrites the same paths. Multi-face outputs use face indexes starting at `0`.

If only some outputs appear:

- confirm each `--dump_*` flag;
- check whether an exception occurred after earlier artifacts were written;
- confirm `visualize/tri.mat` for mesh/render outputs;
- disable GUI display with `--show_flg=false` in headless sessions.

## PAF fails with modern NumPy

PAF generation uses the deprecated alias `np.int`. NumPy 1.24+ removed this alias. If `--dump_paf=true` fails with an `AttributeError` mentioning `np.int`, use a compatible older NumPy or patch the alias to builtin `int`/`np.int64` in a controlled local change.

## Video demo does not open a file or hangs in headless mode

The video demo is GUI-oriented and casts `--video` through `int(args.video)` before OpenCV capture creation. Non-numeric file paths can fail immediately, and headless environments can hang or error at `cv2.imshow`.

For video tasks:

- Use camera index `0` only for a quick interactive check on a host with display support.
- Treat file-path video inference as requiring a small wrapper or patch.
- Do not claim the demo writes output video; it displays PNCC-masked frames only.

## Checkpoint or architecture mismatch

The default checkpoint expects `mobilenet_1(num_classes=62)`. Other MobileNet widths or output dimensions require matching checkpoints. If `load_state_dict` reports size mismatches, revert to the default architecture/checkpoint pair or provide a compatible trained state dict.
