# Interactive local-hints workflows

This reference describes the local-hints colorization workflows without requiring a notebook, GUI import, Caffe import, or model-weight execution during reading.

## Workflow selection

| Task | Use this workflow | Route elsewhere when |
| --- | --- | --- |
| Explain the full local-hints GUI | [GUI interaction semantics](#gui-interaction-semantics) | The task is mainly dependency/model setup; use [../../setup-and-models/SKILL.md](../../setup-and-models/SKILL.md). |
| Recreate the notebook local-hints flow in code | [Notebook-style API recipe](#notebook-style-api-recipe) | The task asks for global histogram/reference-image transfer; use [../../global-histogram-transfer/SKILL.md](../../global-histogram-transfer/SKILL.md). |
| Inspect parser defaults safely | [CLI defaults workflow](#cli-defaults-workflow) | The task requires actually launching the GUI; first satisfy setup/model/display prerequisites. |
| Interpret saved local-hints outputs | [Saved result artifacts](#saved-result-artifacts) and [data formats](data-formats.md) | The directory came from a different tool or a training pipeline. |

## GUI interaction semantics

The local-hints GUI combines a drawing pad, a predicted-result pane, an ab gamut map, a suggested-color palette, a recent-color palette, and load/save/restart controls.

### Controls

| Interaction | Source behavior |
| --- | --- |
| Add a point | Left-click inside the drawing pad. The click is converted from window coordinates to the `load_size x load_size` working grid, a square patch is written into the user input image/mask, and the colorization result is recomputed. |
| Move a point | Left-click an existing point and drag it. If the click falls inside the current patch width, the existing `PointEdit` is selected and updated rather than creating a new one. |
| Change a point color | Select a point, then choose a recommended color, a recent color, or a color from the ab gamut. The color is snapped to the selected pixel's L value before being written. |
| Remove a point | Right-click a point. `UIControl.erasePoint` removes the first matching edit and recomputes the result. |
| Change patch size | Mouse wheel changes `brushWidth`, clamped between zero-ish and about `4.05 * scale`. The notebook recipe uses patch half-width `p`; the GUI stores window-scaled brush width and converts it back to the working grid. |
| Toggle gray display | The Gray checkbox or `G` key toggles whether the drawing pad displays the grayscale input or the current result under the hint markers. |
| Load image | The Load button or `L` key asks for a new input image and reinitializes local-hints state. |
| Restart | The Restart button or `R` key clears points, palettes, result view state, and current color. |
| Save | The Save button or `S` key saves local-hints arrays and visualizations. The `Q` key saves before quitting. |
| Quit | The Quit button closes the GUI; `Q` saves first, then closes. |

### Color update flow

1. When a point is selected, the GUI reads the selected pixel's L value from the working Lab image.
2. The ab gamut widget is regenerated for that L value.
3. If a distribution model is present, `get_ab_reccs(h, w, K=9, N=25000, return_conf=True)` proposes colors at the point.
4. Suggested ab colors are converted to RGB at the selected L value; the current model output color at that pixel is prepended to the suggestion list.
5. Palette or gamut selection updates the active user color, snaps it through `lab_gamut.snap_ab`, updates the selected `PointEdit`, and recomputes the result.
6. Recently used colors are sorted by most recent edit and de-duplicated by exact RGB equality before being displayed.

`UIControl.addStroke` is not implemented, so model the shipped GUI as point/patch editing rather than a freehand brush system.

## Notebook-style API recipe

The notebook local-hints demo can be represented as a compact API recipe. The Caffe version is the repository's original demonstration; the PyTorch wrapper follows the same `input_ab`/`mask` convention once weights are prepared.

### 1. Initialize a local-hints wrapper

Choose one colorization wrapper and, when recommendations are needed, the matching distribution wrapper:

```python
from data import colorize_image as CI

Xd = 256

# Caffe colorization, if Caffe and model files are available.
color_model = CI.ColorizeImageCaffe(Xd=Xd)
# color_model.prep_net(gpu_id, color_prototxt, color_caffemodel)

dist_model = CI.ColorizeImageCaffeDist(Xd=Xd)
# dist_model.prep_net(gpu_id, dist_prototxt, dist_caffemodel)

# PyTorch alternative, if PyTorch weights are available.
color_model = CI.ColorizeImageTorch(Xd=Xd, maskcent=False)
# color_model.prep_net(gpu_id=None, path=pytorch_model_path, dist=False)

dist_model = CI.ColorizeImageTorchDist(Xd=Xd, maskcent=False)
# dist_model.prep_net(gpu_id=None, path=pytorch_model_path, dist=True)
```

Model-file acquisition and backend setup are intentionally delegated to [../../setup-and-models/SKILL.md](../../setup-and-models/SKILL.md).

### 2. Load or set an image

Use `load_image(input_path)` when starting from an image file: it preserves a full-resolution copy, resizes the working image to `Xd x Xd`, and prepares Lab state.

Use `set_image(input_rgb)` when the caller already owns an RGB array. For consistency with GUI distribution use, pass an `Xd x Xd x 3` RGB array unless all downstream tensor shapes are controlled by the caller.

### 3. Build local-hint tensors

Initialize empty local hints:

```python
import numpy as np

input_ab = np.zeros((2, Xd, Xd), dtype=np.float32)
mask = np.zeros((1, Xd, Xd), dtype=np.float32)
```

Add square point patches in working-grid coordinates `(h, w)`:

```python
def put_point(input_ab, mask, loc, p, val):
    """Add a square local-hints patch.

    input_ab: 2 x Xd x Xd ab values.
    mask:     1 x Xd x Xd binary mask.
    loc:      (h, w) working-grid coordinate.
    p:        half-patch size, so patch side is 2*p + 1.
    val:      (a, b) Lab chroma value.
    """
    h, w = loc
    input_ab[:, h - p:h + p + 1, w - p:w + p + 1] = np.array(val)[:, None, None]
    mask[:, h - p:h + p + 1, w - p:w + p + 1] = 1
    return input_ab, mask
```

Notebook-derived examples use a blue patch near the cup at `loc=(135, 160)`, `p=3`, `val=(23, -69)`, followed by a neutral gray patch at `loc=(100, 160)`, `p=3`, `val=(0, 0)` to suppress color leakage.

Guard patch writes in production code: clip `h - p:h + p + 1` and `w - p:w + p + 1` to `[0, Xd)` so edge clicks do not silently create empty or wrapped slices.

### 4. Run the color model and retrieve images

```python
img_out = color_model.net_forward(input_ab, mask)  # returns Xd x Xd x 3 RGB for color wrappers
img_gray_fullres = color_model.get_img_gray_fullres()
img_input_fullres = color_model.get_input_img_fullres()
img_mask_fullres = color_model.get_img_mask_fullres()
img_out_fullres = color_model.get_img_fullres()
```

`get_img_fullres()` and `get_input_img_fullres()` upsample ab or mask state to the original full-resolution L channel. They require prior image setup and, for output, a prior successful color forward.

### 5. Request recommended colors

Use the distribution model after setting the same image and forwarding the current hints:

```python
dist_model.set_image(color_model.img_rgb)
dist_model.net_forward(input_ab, mask)
ab, confidence = dist_model.get_ab_reccs(h=135, w=160, K=5, N=25000, return_conf=True)
```

The returned `ab` array is `K x 2`. Confidence values are cluster occupancy fractions from the sampled distribution, not calibrated probabilities of final image quality. Convert recommended ab values to RGB using the selected pixel's L value before showing them as palette colors.

## CLI defaults workflow

Use the bundled parser-inspection script when a task only needs option facts:

```bash
python sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py --json
```

The script is static and does not import PyQt, qdarkstyle, Caffe, model files, or source GUI modules. It reports both parser variants:

- root GUI parser: default `--backend caffe`.
- Docker GUI parser: default `--backend pytorch`.

Important parser quirk: both parser variants define `--dist_model` with `dest='color_model'`. There is no independent `args.dist_model`; both PyTorch model initializations use `args.color_model`. If both `--color_model` and `--dist_model` are provided, ordinary argparse ordering decides the single final `color_model` value.

## Safe helper smoke workflow

Use the bundled smoke helper to check safe source APIs in a checkout without GUI/Caffe/model-weight execution:

```bash
python sub-skills/interactive-colorization/scripts/smoke_core_helpers.py --repo-root <repo-root> --size 8 --json
```

Expected safe coverage:

- `data.colorize_image`, `data.lab_gamut`, and `models.pytorch.model` imports.
- Signature checks for the verified wrappers and `SIGGRAPHGenerator`.
- `lab_gamut` one-pixel conversions, `snap_ab`, and `abGrid` coordinate round-trips.
- `ColorizeImageTorch.set_image`, grayscale/full-resolution helper shapes, and random-weight tiny PyTorch forwards.
- Distribution wrapper state shapes and a small `get_ab_reccs` call.

The helper deliberately avoids PyQt modules, Caffe `prep_net`, downloaded Caffe/PyTorch model files, and native notebooks/examples.

## Saved result artifacts

The GUI saves into a new directory next to the input image, named from the input image stem, the GUI method label (`with_dist` in source), and a timestamp. The saved contents are:

| File | Meaning |
| --- | --- |
| `im_l.npy` | Working L channel from the colorization model, shape `1 x Xd x Xd`. |
| `im_ab.npy` | User-provided ab tensor, shape `2 x Xd x Xd`. |
| `im_mask.npy` | User mask tensor, shape `1 x Xd x Xd`; true/one where hints are present. |
| `input_mask.png` | Display mask image derived from `im_mask.npy`. |
| `ours.png` | Working-resolution RGB colorization result converted through BGR for OpenCV writing. |
| `ours_fullres.png` | Full-resolution colorization from `get_img_fullres()`. |
| `input_fullres.png` | Full-resolution visualization of the user hints over the grayscale image. |
| `input.png` | Working-resolution visualization of the user hints over the grayscale image. |
| `input_ab.png` | Working-resolution support visualization from `get_sup_img()`. |

When analyzing a saved directory, prefer the `.npy` arrays for exact local-hints data and the `.png` files for visualization or user-facing reports.

## Fixture names

Known fixture image names in the checkout include `mortar_pestle.jpg`, `parrot.jpg`, `park.jpg`, `bird_gray.jpg`, `balls_gray.JPEG`, and reference-image subdirectories for the global histogram workflow. Treat fixture names as examples only; do not depend on bundled image bytes inside this runtime skill.
