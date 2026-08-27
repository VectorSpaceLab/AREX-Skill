# GeoSeg data-preparation troubleshooting

Use this page after reading [data-formats.md](data-formats.md) and
[workflows.md](workflows.md). Diagnose one dataset family and one processed
output tree at a time. The bundled converters and splitters are linked from the
[data-preparation skill](../SKILL.md); they pair by stem, validate labels and
shapes, and write atomically.

## 1. Install and import failures

### Symptom: `ModuleNotFoundError: PIL`, `numpy`, or `cv2`

**Likely cause:** the command is running under a different Python interpreter
than the one where the packages were installed, or a minimal environment lacks
the package. Pillow provides the `PIL` import, NumPy provides `numpy`, and
OpenCV provides `cv2`. The bundled preparation scripts require Pillow and
NumPy. OpenCV is only needed if a separate inspection or downstream data
loader explicitly imports it.

**Recover:** verify the interpreter and imports in the same shell:

```bash
python -c "import sys; print(sys.executable); import PIL, numpy; print(PIL.__version__, numpy.__version__)"
python -c "import cv2; print(cv2.__version__)"
```

Install the missing package into that exact interpreter using the environment's
normal package manager, then repeat the probe. If OpenCV is not used by the
selected preparation command, do not install the full training stack merely to
run a bundled script. Run the scripts with `python`, or with the explicitly
verified interpreter, and use `python <script> --help` to confirm the command.

**Stop:** stop before conversion or tiling when the Pillow/NumPy probe fails,
when the interpreter is not the intended environment, or when package
installation reports an unresolved binary/ABI error. Do not work around an
import failure by changing label values or by silently switching interpreters.
A successful preprocessing import does not prove that training dependencies,
CUDA, or optional model packages are available.

### Symptom: importing a dataset/config fails before a loader is created

**Likely cause:** a downstream dataset module may construct a validation
 dataset during import and therefore requires the complete validation tree.
This is not required for the dependency-light conversion and splitting scripts.

**Recover:** finish and validate data preparation without importing the
training stack. If a downstream import is required, provide both validation
domain trees with their expected image and converted-mask directories, then
retry the import. Keep environment diagnosis separate from file conversion.

**Stop:** stop and hand off the environment issue to the training or
model/config workflow when the failure is Torch, CUDA, an optional accelerator,
or another training-only dependency. Do not claim the data is invalid from
that error alone.

## 2. Missing directories and wrong roots

### Symptom: `directory does not exist`, `must be existing directories`, or
`no ... found`

**Likely cause:** a path is misspelled, has the wrong case, points to a parent
rather than the required leaf directory, or the dataset was not staged. Flat
ISPRS inputs are read directly from the supplied image and mask directories;
UAVid requires one level of sequence directories. The scripts do not download
data or recursively discover arbitrary layouts.

**Recover:** inspect the intended tree before running a command:

```bash
find <dataset-root> -maxdepth 4 -type d | sort
find <dataset-root> -maxdepth 5 -type f | sort | head -n 40
```

Use the dataset-specific layouts in [data-formats.md](data-formats.md):
LoveDA has per-split/per-domain `images_png` and source or converted mask
folders; Vaihingen and Potsdam use flat image/mask folders; UAVid uses
`<sequence>/Images` and `<sequence>/Labels`. Pass the actual leaf directories
or the actual UAVid parent to the matching script. Check readability and
writability as well as existence.

**Stop:** stop when the acquisition is incomplete, when a required `Images`,
`Labels`, `images_png`, or mask directory cannot be identified, or when files
are not directly discoverable under the documented layout. Do not create empty
placeholder directories, infer a dataset from filenames alone, or continue
with a partial split.

## 3. Image/mask pairing, counts, stems, and shapes

### Symptom: missing paired masks, stem mismatch, unequal counts, or a loader
reports files but examples are wrong

**Likely cause:** an image has no exact-stem partner, a suffix flag selected a
different product, one domain was combined with another, or two independently
sorted lists were zipped. Equal counts are not sufficient: a loader can report
equal counts while pairing the wrong samples.

**Recover:** compare stem sets before conversion or tiling. Account for the
format-specific suffixes; compare `Path.stem` after removing only the expected
product suffix where applicable:

```bash
python - <<'PY'
from pathlib import Path

def stems(directory, suffixes):
    return {p.stem for p in Path(directory).iterdir()
            if p.is_file() and p.suffix.lower() in suffixes}

images = stems('<image-dir>', {'.png', '.tif', '.tiff'})
masks = stems('<mask-dir>', {'.png', '.tif', '.tiff'})
print('images:', len(images), 'masks:', len(masks))
print('missing masks:', sorted(images - masks)[:20])
print('missing images:', sorted(masks - images)[:20])
assert images == masks
PY
```

For LoveDA, compare each Urban/Rural and Train/Val directory independently;
do not compare the combined two-domain image count with one mask directory.
For UAVid, check every sequence's `Images` and `Labels` stem sets. Restore or
rename files only when the naming change is known to reflect the official
pairing; never pair by directory order.

Then compare dimensions for representative files and every pair if practical:

```bash
python - <<'PY'
from pathlib import Path
from PIL import Image
for image_path in sorted(Path('<image-dir>').iterdir()):
    if image_path.suffix.lower() not in {'.png', '.tif', '.tiff'}:
        continue
    mask_path = Path('<mask-dir>') / image_path.name
    if not mask_path.exists():
        continue
    with Image.open(image_path) as image, Image.open(mask_path) as mask:
        print(image_path.name, image.size, mask.size)
        assert image.size == mask.size
PY
```

**Stop:** stop before writing patches when any expected stem is missing, a
pair's height/width differs, or the correct partner cannot be established with
certainty. Do not resize only one side, use a different tile's mask, or accept
an equal-count directory as proof of correctness. A mismatch after an intended
joint `--val-scale` still requires checking the generated pair and effective
scale.

## 4. Suffixes and `--eroded`, `--gt`, and RGB flags

### Symptom: no images found, missing paired files, or a command succeeds but
the output is unusable for training

**Likely cause:** the CLI flag does not match the acquired product:

- Vaihingen images are `<stem>.tif`; ordinary masks are `<stem>.tif`, while
  `--eroded` selects `<stem>_noBoundary.tif`.
- Potsdam `--rgb-image` selects `<stem>_RGB.tif`; without it the script selects
  `<stem>_IRRG.tif`. Ordinary masks are `<stem>_label.tif`, and `--eroded`
  selects `<stem>_label_noBoundary.tif`.
- `--gt` intentionally writes RGB visualization masks (and an `origin` copy),
  not the single-channel indexed masks expected by the training loaders.
- LoveDA conversion expects source grayscale label PNGs in `masks_png` and
  writes indexed masks beside an RGB visualization directory; the RGB copy is
  not a training mask.

**Recover:** list actual filenames and select flags from the product that is
present. Use a separate output directory for eroded versus ordinary masks and
for `--gt` visualization. For a training run, rerun without `--gt` into a clean
indexed-mask directory and verify that ordinary output masks are single-channel
PNG files. For Potsdam, do not rename an `_IRRG` file to `_RGB` (or vice versa)
to silence the search; select the true image product and ensure its paired label
set has the same base stem.

**Stop:** stop when the official product type is unknown, when an eroded mask
is missing, when RGB and IRRG imagery are mixed, or when a training loader is
pointed at a GT/RGB directory. Do not treat a suffix error as a label-conversion
problem.

## 5. LoveDA labels and ISPRS/UAVid colors

### Symptom: `unsupported LoveDA label values`, `unsupported ... mask colors`,
or output labels look shifted, all background, or all ignore

**Likely cause:** the input is a visualization/palette/RGB mask instead of the
required encoding, it was compressed or color-corrected, or it belongs to a
different dataset. Validation must use exact values/colors; near matches are
invalid.

**Recover:** inspect one or more raw masks without modifying them:

```bash
python - <<'PY'
from pathlib import Path
import numpy as np
from PIL import Image
for path in sorted(Path('<mask-dir>').glob('*'))[:3]:
    with Image.open(path) as image:
        data = np.asarray(image)
    print(path.name, data.shape, data.dtype, np.unique(data, axis=0)[:12])
PY
```

For LoveDA, source masks must be single-channel and contain only values `0..7`.
The converter maps source `0` to GeoSeg ignore `7`, and source `1..7` to
stored classes `0..6`. Restore the original source mask if values outside
`0..7` occur. Never modulo, clip, cast RGB channels to grayscale, or guess a
palette.

For Vaihingen/Potsdam, use the exact seven RGB colors and class mapping in
[data-formats.md](data-formats.md). For UAVid, use its exact eight class colors
plus white `(255,255,255)` as ignore/boundary. Preserve labels as lossless PNG
or TIFF; JPEG, color correction, palette reinterpretation, or a channel-order
conversion can invalidate every pixel.

**Stop:** stop and reacquire/restore the mask when any unsupported value or
color remains, when a supposed indexed output is RGB, or when all pixels map to
a suspicious single class without evidence that the source really is uniform.
Do not proceed on a visually plausible but numerically unvalidated mask.

## 6. Output overwrite and partial-run safety

### Symptom: `refusing to overwrite`, duplicate-looking patches, or a rerun
leaves a mixed directory

**Likely cause:** the destination already contains files from an earlier run,
or the same destination is being reused for a different dataset, mode, tile
size, stride, suffix, or label representation. The refusal is a safety gate.
Atomic file writes protect individual files but cannot make a mixed experiment
semantically correct.

**Recover:** prefer a new, empty destination whose name records dataset,
split, flags, tile size, stride, and mode. Inspect existing files before any
rerun. Use `--overwrite` only when the input contract and all output settings
are intentionally identical and replacement is approved. If a run stopped
midway, remove or quarantine the partial destination and rerun cleanly rather
than assuming its counts are complete. Validate stems, shapes, and label values
afterward; do not rely on the printed count alone.

**Stop:** stop when the destination contains unknown or mixed provenance,
when overwrite approval is absent, when outputs from different domains or
encoding modes are present, or when an overwrite would conceal an earlier
validation failure. Never write processed files into the read-only raw tree.

## 7. Mode, stride, tile size, scaling, and padding failures

### Symptom: unexpected patch counts, missing edge tiles, non-square outputs,
or black/boundary-looking margins

**Likely cause:** `--mode`, tile size, stride, or scale does not match the
intended workflow. The splitters pad only the bottom and right edges, emit full
tiles, and skip windows that do not fit. In Vaihingen/Potsdam, `train` emits
source, horizontal-flip, and vertical-flip variants; non-train modes emit one.
UAVid's mode changes output naming only and adds no augmentation. `--val-scale`
is applied only outside train mode by the ISPRS splitters, with bicubic image
and nearest-neighbor mask resizing.

**Recover:** record and verify all four geometry values before rerunning:
`split-size` (or height/width), `stride` (or height/width), `mode`, and
`val-scale`. Tile sizes and strides must be positive. Use square `1024` tiles
and the downstream layout when an unmodified GeoSeg configuration expects
that contract; rectangular UAVid tiles are valid only when the consumer is
configured for them. A stride larger than the tile can leave gaps; a stride
smaller than the tile creates overlap. Choose the stride deliberately and use a
new output root for changed geometry.

Black image margins and boundary/ignore mask margins at the bottom/right are
expected padding. A whole black patch or whole ignore patch is not automatically
valid: inspect its source pair, coordinate, and source dimensions. If edge
coverage is required, choose dimensions/stride that cover it and verify output
shapes; do not crop or fill class masks by copying neighboring labels.

**Stop:** stop when any tile or mask has an unexpected shape, when a required
edge region is silently omitted, when stride/tile settings cannot be recovered,
or when the consumer cannot accept the selected rectangular geometry. Stop
before training if padding dominates a patch or if padding has been mistaken
for a real class.

## Final recovery gate

Before handing data to [training](../../training/SKILL.md), confirm the source
layout, exact command and effective paths, pair and patch counts, exact stem
sets, sample shapes, label values/colors, selected suffix and flags, mode,
stride, tile size, padding, and any rejected or skipped files. Use
[model-and-config](../../model-and-config/SKILL.md) for consumer/configuration
mismatches and [evaluation-inference](../../evaluation-inference/SKILL.md) for
visualization or inference output issues. If a stop condition above applies,
report the unresolved evidence and do not claim the dataset is ready.
