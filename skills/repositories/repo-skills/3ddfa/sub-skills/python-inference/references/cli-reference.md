# 3DDFA Python Inference CLI Reference

This reference distills the Python image and video inference command surface so a future agent does not need to inspect source files.

## Image Inference Entrypoint

The image inference CLI accepts one or more images, builds a 120x120 crop for each detected/provided face rectangle, runs a MobileNet-V1 regressor, and writes selected artifacts beside each input image.

### Core image flags

| Flag | Default | Meaning and notes |
|---|---:|---|
| `-f`, `--files` | none | One or more input image paths. The native loop expects this to be present. |
| `-m`, `--mode` | `cpu` | Use `gpu` to move the model/input to CUDA. Any value other than exact `gpu` follows the CPU path. |
| `--show_flg` | `true` | Whether landmark visualization should call interactive display after saving. Use `false` in headless runs. |
| `--bbox_init` | `one` | `one` runs a single bbox/landmark crop pass. `two` runs a second crop pass from predicted 68 landmarks for more accurate bbox initialization. |
| `--dlib_bbox` | `true` | If true, uses the dlib frontal face detector. If false, reads `<image>.bbox`. The Python `dlib` module is still imported at startup. |
| `--dlib_landmark` | `true` | If true, uses the dlib 68-landmark predictor to initialize the crop from a detected/provided rectangle. If false, initializes the crop from bbox only. |

Boolean flags are parsed with `true/false`, `yes/no`, `t/f`, `y/n`, or `1/0` strings.

### Output flags

| Flag | Default | Output pattern | Notes |
|---|---:|---|---|
| `--dump_res` | `true` | `<stem>_3DDFA.jpg` | Landmark visualization over the image. |
| `--dump_pts` | `true` | `<stem>_<face_index>.txt` | 68 predicted 3D landmarks, one text file per face. |
| `--dump_ply` | `true` | `<stem>_<face_index>.ply` | Dense mesh in ASCII PLY. Requires `visualize/tri.mat`. |
| `--dump_obj` | `true` | `<stem>_<face_index>.obj` | Textured OBJ using sampled source-image colors. Requires dense vertices and `visualize/tri.mat`. |
| `--dump_vertex` | `false` | `<stem>_<face_index>.mat` | Dense face vertices saved in MATLAB format under key `vertex`. |
| `--dump_roi_box` | `false` | `<stem>_<face_index>.roibox` | Final ROI box used for the face crop. Useful for debugging bbox initialization. |
| `--dump_pose` | `true` | `<stem>_pose.jpg` | Pose box visualization for all faces in the image. |
| `--dump_depth` | `true` | `<stem>_depth.png` | Depth image rendered from dense vertices. Uses Cython render path. |
| `--dump_pncc` | `true` | `<stem>_pncc.png` | PNCC feature image. Uses Cython render path and writes RGB swapped for OpenCV. |
| `--dump_paf` | `false` | `<stem>_<face_index>_paf.jpg`, `<stem>_<face_index>_crop.jpg` | PAF feature plus crop image. |
| `--paf_size` | `3` | affects PAF dimensions | Kernel size used by PAF generation. Legacy NumPy may be needed unless `np.int` use is patched. |

With default output flags, a two-face image writes two `.ply`, two `.txt`, two `.obj`, plus one pose image, one depth image, one PNCC image, and one landmark visualization.

## BBox File Format

When `--dlib_bbox=false`, the image CLI reads a sidecar file named exactly `<image path>.bbox`.

Expected format:

```text
<number_of_faces>
<face_id> <left> <top> <right> <bottom>
<face_id> <left> <top> <right> <bottom>
...
```

The first line is skipped after read. Each later line is split on spaces; the first column is ignored and the next four integers are passed to a `dlib.rectangle` constructor. A sampled sidecar in the repo follows this pattern with three faces.

For no-detector inference, use both bbox and landmark switches:

```bash
python main.py -f samples/emma_input.jpg --mode cpu --dlib_bbox=false --dlib_landmark=false --bbox_init=two --show_flg=false
```

This avoids the detector and landmark predictor model, but the unmodified native CLI still imports the Python `dlib` module at process startup.

## Video Demo Surface

The video demo has a much smaller flag surface:

| Flag | Default | Meaning and caveats |
|---|---:|---|
| `-v`, `--video` | `0` | Intended to be a video file path or camera index, but the implementation casts the argument with `int(args.video)` before opening, so non-numeric file paths can fail before OpenCV receives them. |
| `-m`, `--mode` | `cpu` | Same exact-`gpu` CUDA behavior as image inference. |

Video behavior:

- Opens a capture source, reads frames, and displays a PNCC-masked frame in an OpenCV window.
- On the first usable frame, runs dlib face detection and dlib landmark prediction; later frames update the previous 68-point landmarks from model predictions.
- Always depends on dlib detector, dlib landmark predictor, dense prediction, PNCC rendering, and the Cython render extension.
- Does not write an output video; it is an interactive display demo.
- Is unsuitable for headless validation unless wrapped to replace `cv2.imshow`/`cv2.waitKey` and to handle file-path video sources.

## Safe Commands to Prefer During Diagnosis

These bundled scripts do not invoke image/video inference. Run them from this sub-skill directory and point `--repo-root` at the 3DDFA checkout you are diagnosing:

```bash
python scripts/inspect_3ddfa_inference.py --repo-root /path/to/3DDFA
python scripts/smoke_mobilenet_forward.py --repo-root /path/to/3DDFA --arch mobilenet_1 --num-classes 62
```

Use their output to decide whether native inference can be run safely in the target checkout.
