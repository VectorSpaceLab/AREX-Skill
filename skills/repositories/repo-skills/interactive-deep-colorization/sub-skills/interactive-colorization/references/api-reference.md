# Interactive colorization API reference

This reference distills the local-hints colorization surfaces used by the GUI and notebook-style workflow. It intentionally avoids depending on GUI imports, Caffe imports, or downloaded model weights.

## Source module map

| Module | Runtime role | Notes |
| --- | --- | --- |
| `data.colorize_image` | Image/Lab preprocessing, Caffe and PyTorch local-hints wrappers, output helpers, recommendation sampling. | Safe to import for source inspection when image-stack dependencies are present; Caffe is imported only inside Caffe `prep_net` methods. |
| `data.lab_gamut` | RGB/Lab one-pixel conversions, gamut snapping, and ab-grid visualization helpers. | `qcolor2lab_1d` expects a Qt color object; non-Qt helpers work with NumPy arrays. |
| `models.pytorch.model` | PyTorch `SIGGRAPHGenerator` architecture for local hints and optional distribution output. | Requires PyTorch but not model weights for architecture construction and tiny random-weight forwards. |
| `ui.*` | PyQt GUI layout, drawing pad, color gamut, palettes, result view, and user edit state. | Importing these modules requires Qt bindings. Treat GUI source semantics as distilled facts unless the setup/model gate verifies GUI execution. |

## Verified signatures

| Object | Signature | Purpose |
| --- | --- | --- |
| `ColorizeImageBase` | `ColorizeImageBase(Xd=256, Xfullres_max=10000)` | Common image loading, Lab conversion, full-resolution helpers, and output getters. |
| `ColorizeImageTorch` | `ColorizeImageTorch(Xd=256, maskcent=False)` | PyTorch local-hints colorization wrapper. |
| `ColorizeImageTorchDist` | `ColorizeImageTorchDist(Xd=256, maskcent=False)` | PyTorch distribution/recommendation wrapper. |
| `ColorizeImageCaffe` | `ColorizeImageCaffe(Xd=256)` | Caffe local-hints colorization wrapper. |
| `ColorizeImageCaffeDist` | `ColorizeImageCaffeDist(Xd=256)` | Caffe distribution/recommendation wrapper. |
| `ColorizeImageCaffeGlobDist` | `ColorizeImageCaffeGlobDist(Xd=256)` | Caffe wrapper that also accepts a global histogram; route full global-histogram use to the sibling global workflow. |
| `ColorizeImageTorch.prep_net` | `ColorizeImageTorch.prep_net(self, gpu_id=None, path='', dist=False)` | Builds `SIGGRAPHGenerator(dist=dist)`, loads a PyTorch state dict, optionally moves to CUDA, and switches to eval mode. |
| `SIGGRAPHGenerator` | `SIGGRAPHGenerator(dist=False)` | PyTorch generator architecture. |
| `SIGGRAPHGenerator.forward` | `SIGGRAPHGenerator.forward(self, input_A, input_B, mask_B, maskcent=0)` | Forward pass over L, ab hints, and mask. |

Additional source signatures useful for integration:

- `ColorizeImageCaffe.prep_net(self, gpu_id, prototxt_path='', caffemodel_path='')` chooses Caffe CPU for `gpu_id == -1`, otherwise selects a Caffe GPU device, loads a `caffe.Net`, then initializes cluster-center and upsampling parameters when present.
- `ColorizeImageCaffeDist.prep_net(self, gpu_id, prototxt_path='', caffemodel_path='', S=.2)` delegates to `ColorizeImageCaffe.prep_net` and sets the Caffe softening scale layer to `S`.
- `ColorizeImageCaffeGlobDist.net_forward(self, input_ab, input_mask, glob_dist=-1)` accepts either no global histogram (`-1`) or a 313-bin global distribution plus a mask channel in the Caffe blob.

## Backend wrapper choices

| Choice | Wrapper classes | Best use | Construction verification status |
| --- | --- | --- | --- |
| PyTorch local hints | `ColorizeImageTorch`, `ColorizeImageTorchDist`, `SIGGRAPHGenerator` | Headless API experiments, architecture inspection, and systems where converted PyTorch weights are available. | Source imports and tiny random-weight eval forwards were verified; downloaded weight inference was not verified. |
| Caffe local hints | `ColorizeImageCaffe`, `ColorizeImageCaffeDist` | Repository-official SIGGRAPH 2017 model path when PyCaffe and Caffe model files are installed. | Source facts only; PyCaffe/model-weight execution was not verified. |
| GUI | `ui.gui_design.GUIDesign` with color and distribution models | Full user-guided colorization UI with drawing pad, ab gamut, suggestions, recent colors, and result view. | Source semantics only; PyQt/display execution was not verified. |

The Caffe model is documented by the repository as the official SIGGRAPH 2017 backend, while PyTorch is a reimplementation/converted-weight backend. Route dependency and model-file details to [../../setup-and-models/SKILL.md](../../setup-and-models/SKILL.md).

## `ColorizeImageBase` image and output helpers

`ColorizeImageBase` owns shared state used by both Caffe and PyTorch wrappers.

| Method | Contract |
| --- | --- |
| `load_image(input_path)` | Reads an image with OpenCV, stores the full-resolution RGB copy, converts full-resolution Lab, resizes to `Xd x Xd`, stores resized RGB/Lab/L/ab arrays, and mean-centers Lab state. |
| `set_image(input_image)` | Uses an already loaded RGB array as both full-resolution and working image. In GUI distribution use, this array is already resized to `Xd x Xd`; callers should preserve that convention unless they also control all matching tensors. |
| `net_forward(input_ab, input_mask)` | Base validation and normalization: requires `img_l_set` and `net_set`, stores `input_ab`, computes `input_ab_mc = (input_ab - ab_mean) / ab_norm`, stores `input_mask`, and computes `input_mask_mult = input_mask * mask_mult`. Subclasses perform actual inference. |
| `get_img_gray()` / `get_img_gray_fullres()` | Return RGB grayscale images from the L channel and zero ab values at working or full resolution. |
| `get_img_forward()` | Returns the most recent `output_rgb`. |
| `get_img_fullres()` | Bilinearly upsamples `output_ab` to the full-resolution L shape and converts Lab to RGB. Requires `output_ab` to be set by a prior colorization forward. |
| `get_input_img()` / `get_input_img_fullres()` | Convert the stored user `input_ab` plus image L channel into an RGB visualization at working or full resolution. |
| `get_img_mask()` / `get_img_mask_fullres()` | Render the stored binary mask as a white/black RGB mask at working or full resolution; full-resolution mask uses nearest-neighbor upsampling. |
| `get_sup_img()` / `get_sup_fullres()` | Visualize user hints by combining `50 * input_mask` as L with user `input_ab`. |
| `get_result_PSNR(result=-1, return_SE_map=False)` | Computes PSNR against the working RGB image, optionally returning the squared-error map. |

`lab2rgb_transpose(img_l, img_ab)` expects `img_l` as `1 x X x X` in `[0, 100]` and `img_ab` as `2 x X x X` in approximately `[-100, 100]`; it returns `X x X x 3` `uint8` RGB. `rgb2lab_transpose(img_rgb)` expects `X x X x 3` RGB and returns `3 x X x X` Lab.

## PyTorch local-hints model

`ColorizeImageTorch.__init__` sets `l_norm=1`, `ab_norm=1`, `l_mean=50`, `ab_mean=0`, `mask_mult=1`, and `mask_cent=.5` only when `maskcent=True`; otherwise `mask_cent=0`. It also creates a 529-point `pts_in_hull` grid over `a,b` values from `-110` to `110` in steps of `10`.

`ColorizeImageTorch.net_forward(input_ab, input_mask)`:

1. Delegates to `ColorizeImageBase.net_forward` for state validation and normalization.
2. Calls `self.net.forward(self.img_l_mc, self.input_ab_mc, self.input_mask_mult, self.mask_cent)`.
3. Takes the first batch element `0`, converts predicted ab to NumPy, combines it with `self.img_l`, stores `output_rgb`, derives `output_ab`, and returns `output_rgb`.

`SIGGRAPHGenerator.forward(input_A, input_B, mask_B, maskcent=0)` converts NumPy inputs to tensors, adds a batch dimension, subtracts `maskcent` from `mask_B`, and concatenates `input_A / 100`, `input_B / 110`, and the centered mask. The construction smoke verified these tiny eval-forward shapes:

- `SIGGRAPHGenerator(dist=False)` returns `(1, 2, H, W)`.
- `SIGGRAPHGenerator(dist=True)` returns a tuple whose regression branch has `(1, 2, H, W)` and whose distribution branch has `(1, 529, H, W)`.

Use spatial sizes divisible by the model's downsample/upsample schedule, with `Xd=256` as the repository default.

## Distribution wrappers and color suggestions

`ColorizeImageTorchDist` and `ColorizeImageCaffeDist` add distribution state and recommendation helpers:

- `dist_ab_set` is false until a distribution forward succeeds.
- `pts_grid` is the full 529-point `23 x 23` ab grid.
- `dist_ab_full` has shape `529 x Xd x Xd`.
- `dist_ab_grid` has shape `23 x 23 x Xd x Xd`.
- `dist_entropy` has shape `Xd x Xd`.

Backend differences:

- PyTorch distribution output uses all 529 grid points (`in_hull` is all true in the wrapper).
- Caffe distribution output is a 313-channel in-gamut distribution that is placed back into the 529-point full grid using the `in_hull` mask.

`get_ab_reccs(h, w, K=5, N=25000, return_conf=False)` must be called after `net_forward`. It samples `N` ab points from the cumulative distribution at pixel `(h, w)`, clusters samples with K-means, sorts clusters by occupancy, and returns the top `K` cluster centers as recommended ab colors. With `return_conf=True`, it also returns occupancy fractions. GUI suggestion code converts these Lab colors at the selected pixel's L value to RGB and prepends the current model output color at that pixel.

## Lab gamut helpers

| Helper | Behavior |
| --- | --- |
| `rgb2lab_1d(in_rgb)` | Converts one RGB triplet to a flat Lab triplet. |
| `lab2rgb_1d(in_lab, clip=True, dtype='uint8')` | Converts one Lab triplet to RGB, optionally clipping to display gamut and returning `uint8`. |
| `snap_ab(input_l, input_rgb, return_type='rgb')` | Iteratively keeps the requested RGB color's ab intent while forcing lightness to `input_l`, round-tripping through RGB/Lab up to 20 times until the color is in gamut. Returns snapped RGB by default or snapped Lab when `return_type='lab'`. |
| `abGrid(gamut_size=110, D=1)` | Builds a dense ab grid and converts it to a masked RGB gamut map for a supplied L value. |
| `abGrid.ab2xy(a, b)` / `abGrid.xy2ab(x, y)` | Convert between Lab ab coordinates and gamut-widget x/y coordinates by offsetting with `gamut_size`. |

## GUI source semantics

`GUIDesign(color_model, dist_model=None, img_file=None, load_size=256, win_size=256, save_all=True)` lays out these widgets:

- `GUIGamut(gamut_size=160)` for the top-left ab color gamut.
- `GUIPalette(grid_sz=(10, 1))` for suggested colors.
- `GUIPalette(grid_sz=(10, 1))` for recently used colors.
- `GUIDraw(color_model, dist_model, load_size, win_size)` for the drawing pad.
- `GUI_VIS(win_size, scale=win_size / load_size)` for the result view.

Key signal flow:

- Drawing-pad color changes update the current color swatch and gamut crosshair.
- Gamut and palette selections call `GUIDraw.set_color` and recompute the result.
- The drawing pad emits `suggest_colors` from the distribution model and `used_colors` from `UIControl`.
- Drawing-pad result updates are displayed by `GUI_VIS.update_result`.

`GUIDraw` is point-oriented in the implemented source. `UIControl.addStroke` is a placeholder, so do not promise freehand stroke behavior beyond point patches.

## GUI CLI parser facts

The main GUI parser exposes these options. The bundled script [../scripts/inspect_cli_defaults.py](../scripts/inspect_cli_defaults.py) prints the same distilled facts as JSON or a table without importing GUI dependencies.

| Option | Destination | Default in root GUI | Default in Docker GUI | Notes |
| --- | --- | --- | --- | --- |
| `--win_size` | `win_size` | `512` | `512` | Main GUI window size; runtime truncates to a multiple of 4 after parsing. |
| `--image_file` | `image_file` | `test_imgs/mortar_pestle.jpg` | `test_imgs/mortar_pestle.jpg` | Initial input image. |
| `--gpu` | `gpu` | `0` | `0` | GPU id; `--cpu_mode` later sets `gpu=-1`. |
| `--cpu_mode` | `cpu_mode` | `False` | `False` | Store-true flag to disable GPU use. |
| `--color_prototxt` | `color_prototxt` | `./models/reference_model/deploy_nodist.prototxt` | same | Caffe colorization prototxt. |
| `--color_caffemodel` | `color_caffemodel` | `./models/reference_model/model.caffemodel` | same | Caffe colorization weights. |
| `--dist_prototxt` | `dist_prototxt` | `./models/reference_model/deploy_nopred.prototxt` | same | Caffe distribution prototxt. |
| `--dist_caffemodel` | `dist_caffemodel` | `./models/reference_model/model.caffemodel` | same | Caffe distribution weights. |
| `--color_model` | `color_model` | `./models/pytorch/caffemodel.pth` | same | PyTorch model path used by both PyTorch wrappers. |
| `--dist_model` | `color_model` | `./models/pytorch/caffemodel.pth` | same | Quirk: same destination as `--color_model`; no `args.dist_model` exists. |
| `--backend` | `backend` | `caffe` | `pytorch` | Backend selector. |
| `--pytorch_maskcent` | `pytorch_maskcent` | `False` | `False` | Store-true flag; subtracts `.5` from the mask before PyTorch forward when enabled. |
| `--load_size` | `load_size` | `256` | `256` | Deprecated in parser comment but still drives wrapper `Xd`. |

The parser prints argument values before the source main routine applies the `--cpu_mode` and `win_size` post-processing changes. For PyTorch backend construction, both `ColorizeImageTorch.prep_net(path=args.color_model)` and `ColorizeImageTorchDist.prep_net(path=args.color_model, dist=True)` use the same parsed `color_model` destination.
