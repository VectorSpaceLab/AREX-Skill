# API reference

## Core classes

### `FaceBoxes.FaceBoxes`

Constructor: `FaceBoxes(timer_flag=False)`

- Loads the PyTorch detector checkpoint from `FaceBoxes/weights/FaceBoxesProd.pth`.
- `timer_flag=True` prints detector timing information.
- Call form: `face_boxes(img_)`
- Input: `img_` is a BGR `numpy.ndarray` from OpenCV.
- Return value: a list of detection boxes, each shaped like
  `[xmin, ymin, xmax, ymax, score]`.

### `FaceBoxes.FaceBoxes_ONNX`

Constructor: `FaceBoxes_ONNX(timer_flag=False)`

- Loads `FaceBoxes/weights/FaceBoxesProd.onnx` if present, or converts the
  `.pth` checkpoint on demand.
- Same call contract and output shape as `FaceBoxes`.

### `TDDFA.TDDFA`

Constructor: `TDDFA(**kvs)`

Important keys used by the repo:

- `arch`: model factory name, usually `mobilenet`.
- `widen_factor`: width multiplier for MobileNet variants.
- `checkpoint_fp`: PyTorch checkpoint path.
- `bfm_fp`: Basel Face Model pickle path.
- `size`: input crop size, usually `120`.
- `num_params`: number of regressed parameters, usually `62`.
- `gpu_mode`, `gpu_id`: optional CUDA path.
- `shape_dim`, `exp_dim`: BFM shape/expression dimensions.
- `param_mean_std_fp`: normalization statistics path.
- `mode`: model flavor, usually `small`.

Call form: `tddfa(img_ori, objs, **kvs)`

- `img_ori`: BGR image array.
- `objs`: list of face boxes or landmarks.
- `crop_policy`: `"box"` or `"landmark"`.
- Returns `(param_lst, roi_box_lst)`.
- `param_lst` contains one 62D parameter vector per object.
- `roi_box_lst` contains the ROI boxes used for each crop.

Reconstruction form: `tddfa.recon_vers(param_lst, roi_box_lst, **kvs)`

- `dense_flag=False` returns sparse vertices.
- `dense_flag=True` returns dense vertices.
- Returns a list of `3 x N` vertex arrays.

### `TDDFA_ONNX.TDDFA_ONNX`

Constructor: `TDDFA_ONNX(**kvs)`

- Same high-level keys as `TDDFA`.
- Uses ONNX Runtime for the regression model and the BFM decoder.
- Auto-converts missing `.onnx` files from the corresponding `.pth`/`.pkl`
  sources when needed.
- Same call and reconstruction contract as `TDDFA`.

## Rendering and post-processing helpers

### `utils.render.render`

Signature: `render(img, ver_lst, tri, alpha=0.6, show_flag=False, wfp=None, with_bg_flag=True)`

- Overlays one or more face meshes on an image.
- `ver_lst` should contain `3 x N` vertex arrays.
- `tri` is the triangle index array from the BFM model.
- When `wfp` is set, the helper writes the rendered image to disk.

### `utils.depth.depth`

Signature: `depth(img, ver_lst, tri, show_flag=False, wfp=None, with_bg_flag=True)`

- Produces a depth visualization using the renderer backend.

### `utils.pncc.pncc`

Signature: `pncc(img, ver_lst, tri, show_flag=False, wfp=None, with_bg_flag=True)`

- Produces the PNCC view used in the still-image demo.

### `utils.uv.uv_tex`

Signature: `uv_tex(img, ver_lst, tri, uv_h=256, uv_w=256, uv_c=3, show_flag=False, wfp=None)`

- Builds UV texture maps from the input image and reconstructed vertices.
- Requires the UV config assets in `configs/`.

### `utils.pose.viz_pose`

Signature: `viz_pose(img, param_lst, ver_lst, show_flag=False, wfp=None)`

- Draws the pose annotation box and prints yaw/pitch/roll values.

### `utils.serialization.ser_to_ply`

Signature: `ser_to_ply(ver_lst, tri, height, wfp, reverse=True)`

- Writes one or more PLY mesh files.

### `utils.serialization.ser_to_obj`

Signature: `ser_to_obj(img, ver_lst, tri, height, wfp)`

- Writes one or more OBJ mesh files with per-vertex colors.

### `utils.functions.draw_landmarks`

Signature: `draw_landmarks(img, pts, style='fancy', wfp=None, show_flag=False, **kwargs)`

- Matplotlib-based landmark visualization used by `demo.py`.

### `utils.functions.cv_draw_landmark`

Signature: `cv_draw_landmark(img_ori, pts, box=None, color=GREEN, size=1)`

- OpenCV-based landmark visualization used by the video demos.

## Practical notes

- `uv_tex` depends on SciPy and the `BFM_UV.mat` / `indices.npy` assets.
- `render`, `depth`, and `pncc` require the Sim3DR build products.
- `ser_to_ply` and `ser_to_obj` write files next to the selected results path.
- The benchmark and demo helpers expect the repo root on `sys.path` and the
  working directory to be the repo root.
