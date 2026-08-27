# Single-Image Inference Workflows

This reference is for safe one-image semantic segmentation with the repository's `test.py`. It is intentionally a workflow guide rather than a copy of the full script: the original script loads arbitrary images and checkpoints, may use GPU memory, writes output files, and depends on optional or legacy libraries. The bundled helper only builds and validates dry-run commands.

## What `test.py` does

1. Selects `cuda` if `torch.cuda.is_available()`; otherwise uses CPU.
2. Reads `--img_path` with the legacy SciPy image helper.
3. Parses `model_name` from the checkpoint filename: basename text before the first `_`.
4. Creates a dataset loader with `root=None`, `is_transform=True`, `img_norm=<flag>`, and `test_mode=True`.
5. Reads `loader.n_classes`, `loader.mean`, `loader.img_size`, and eventually calls `loader.decode_segmap(pred)`.
6. Resizes/preprocesses the image as RGB-to-BGR, mean subtraction, optional `[0, 1]` scaling, and NHWC-to-NCHW tensor conversion.
7. Builds the model with `get_model({"arch": model_name}, n_classes, version=<dataset>)`.
8. Loads `torch.load(--model_path)["model_state"]` through `convert_state_dict`, then runs a forward pass.
9. Optionally applies DenseCRF when `--dcrf` is selected.
10. Saves `--out_path` as a colorized dataset-palette segmentation image.

## CLI flags

| Flag | Source default | Use |
| --- | --- | --- |
| `--model_path` | `fcn8s_pascal_1_26.pkl` | Path to a checkpoint whose basename starts with the model id and `_`. |
| `--dataset` | `pascal` | Dataset key used for class count, mean, image size, and palette decoding. |
| `--img_norm` / `--no-img_norm` | `--img_norm` | Whether to divide image values by `255.0` after mean subtraction. Match the checkpoint's training preprocessing. |
| `--dcrf` / `--no-dcrf` | `--no-dcrf` | Optional DenseCRF post-processing. Requires `pydensecrf` and compatible model output semantics. |
| `--img_path` | `None` | Input RGB image. The source script expects a readable image file. |
| `--out_path` | `None` | Output color mask path. Prefer a `.png` suffix, especially when using DenseCRF. |

## Prerequisites before running real inference

- A checkout or installed source path where `test.py` and `ptsemseg` import correctly.
- A trained checkpoint with a top-level `model_state` field. Raw `state_dict` files require a small adaptation before `model.load_state_dict`.
- A checkpoint basename in the pattern `<arch>_<anything>.pkl`, `<arch>_<anything>.pth`, `<arch>_<anything>.pt`, or another extension accepted by `torch.load`.
- A supported architecture prefix: `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, or `frrnB`.
- A dataset key that matches the checkpoint's training dataset and output classes.
- A readable input image and an existing output parent directory.
- For modern Python stacks, either a legacy image-helper environment or a patch replacing `scipy.misc` image helpers with Pillow/imageio/skimage equivalents.

## Build and inspect a command

From this sub-skill directory:

```bash
python scripts/build_inference_command.py \
  --model_path checkpoints/fcn8s_pascal_best_model.pkl \
  --dataset pascal \
  --img_path examples/input.jpg \
  --out_path outputs/input_pascal_mask.png \
  --img_norm \
  --no-dcrf
```

The helper prints the command to run from the repository checkout, for example:

```bash
python test.py --model_path checkpoints/fcn8s_pascal_best_model.pkl --dataset pascal --img_norm --no-dcrf --img_path examples/input.jpg --out_path outputs/input_pascal_mask.png
```

Use `--strict` with the helper when you want missing files, missing output parents, or unsafe checkpoint names to become a non-zero validation result.

## Run inference without DenseCRF

After resolving warnings from the command builder, run the printed command from a working directory where `test.py` is present:

```bash
python test.py \
  --model_path checkpoints/fcn8s_pascal_best_model.pkl \
  --dataset pascal \
  --img_norm \
  --no-dcrf \
  --img_path examples/input.jpg \
  --out_path outputs/input_pascal_mask.png
```

Expected behavior:

- The script prints the input image path.
- The model architecture is inferred from `fcn8s`.
- The Pascal loader supplies `n_classes=21`, a mean vector, image size, and Pascal colors.
- The saved output is a colorized segmentation visualization.
- The script prints `Classes found:` with the predicted class ids before saving.

## ICNet/PSPNet odd-size workflow

For a checkpoint such as `icnetBN_cityscapes_best_model.pkl`, the parsed architecture is `icnetBN`:

```bash
python scripts/build_inference_command.py \
  --model_path checkpoints/icnetBN_cityscapes_best_model.pkl \
  --dataset cityscapes \
  --img_path examples/city.jpg \
  --out_path outputs/city_icnetBN_mask.png \
  --img_norm \
  --no-dcrf
```

Important behavior for `pspnet`, `icnet`, and `icnetBN`:

- The source script first records the original image size.
- It resizes the model input to odd height and width using `orig_size[0] // 2 * 2 + 1` and `orig_size[1] // 2 * 2 + 1`.
- After prediction, it converts the class map to `float32` and resizes it back to the original image size with nearest-neighbor interpolation before palette decoding.
- Odd sizing can increase memory for large images; resize externally or use a smaller image if inference runs out of memory.

Some dataset loaders are more dataset-bound than the `root=None, test_mode=True` inference path suggests. If a `cityscapes`, `nyuv2`, `sunrgbd`, `vistas`, or `mit_sceneparsing_benchmark` run fails during loader construction before image inference, adapt a palette-only loader construction or patch the loader so test mode does not touch dataset directories.

## DenseCRF workflow

Build the command with `--dcrf` only when you intentionally want post-processing:

```bash
python scripts/build_inference_command.py \
  --model_path checkpoints/fcn8s_pascal_best_model.pkl \
  --dataset pascal \
  --img_path examples/input.jpg \
  --out_path outputs/input_pascal_mask.png \
  --img_norm \
  --dcrf
```

DenseCRF notes:

- `pydensecrf` is optional; parser help can work without it, but a real `--dcrf` run needs the module.
- The source import warning is not enough to make `--dcrf` safe. If the import failed, the later `dcrf.DenseCRF2D(...)` access can fail.
- The script builds unary energies with `-np.log(outputs)` and assumes probability-like positive outputs. If your model emits raw logits, adapt the script to apply softmax and clamp small probabilities before `log`.
- DenseCRF saves an additional path derived from `--out_path` by replacing the last four characters with `_drf.png`; prefer an output path ending in `.png`.
- DenseCRF uses the resized RGB image as bilateral guidance and can add memory/time overhead.

## Dataset palette behavior

`decode_segmap` converts integer class ids into dataset-specific colors. The saved mask is a visualization, not a training label map.

| Dataset key | Palette/output notes |
| --- | --- |
| `pascal` | 21-class Pascal VOC colors; commonly safe with `root=None, test_mode=True`. |
| `camvid` | 12-class CamVid color table; commonly safe with `test_mode=True`. |
| `ade20k` | 150-class generated color mapping; commonly safe with `test_mode=True`. |
| `cityscapes` | 19-class Cityscapes colors; loader construction may need a test-mode patch because it can touch dataset directories. |
| `nyuv2` | 14-class generated color map; loader construction can still touch dataset paths. |
| `sunrgbd` | 38-class generated color map; loader construction can still touch dataset paths. |
| `vistas` | 65-class Mapillary colors from `config.json`; palette construction is dataset-bound unless adapted. |
| `mit_sceneparsing_benchmark` | Advertised registry key, but the inspected loader lacks a compatible `decode_segmap`; do not expect unmodified `test.py` output to work for this key. |

Choose the dataset key that matches checkpoint training. A class-count mismatch usually surfaces as checkpoint load errors or nonsensical colors.

## Modern image-helper compatibility

Modern SciPy removed `scipy.misc.imread`, `scipy.misc.imresize`, and `scipy.misc.imsave`. Options:

1. Use a legacy compatibility environment only for running the original script.
2. Patch `test.py` to use Pillow, imageio, or scikit-image helpers.
3. Keep the command builder unchanged; it does not import SciPy or load images.

A Pillow-style adaptation should preserve these semantics:

- Read RGB images as `uint8` arrays.
- Resize image inputs with bicubic/bilinear interpolation as appropriate.
- Resize predicted class maps with nearest-neighbor interpolation.
- When saving `decode_segmap` output in `[0, 1]`, multiply by `255`, clip, and convert to `uint8`.

## Why the full script is not bundled here

The original inference script is useful but not safe as a bundled helper because it loads user-supplied checkpoints, can execute CUDA work, depends on optional `pydensecrf`, relies on removed SciPy image helpers, may instantiate dataset-bound loaders, and writes output images. This sub-skill therefore bundles only a dry-run command builder and records the adaptation requirements above.
