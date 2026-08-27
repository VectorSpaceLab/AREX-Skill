# Output formats and palettes

## Indexed versus RGB masks

The default output of Vaihingen, Potsdam, and LoveDA tile evaluation is a
single-channel `uint8` PNG containing the predicted class id at each pixel.
Use this representation for metric tooling and any downstream code expecting
class ids. Passing `--rgb` converts ids to a three-channel color mask before
writing.

UAVid sequence inference has no `--rgb` switch: it always writes color masks
under `<output>/<sequence>/Labels/`. Huge-image inference also has no indexed
switch: every supported `-d` value is converted to color before writing. The
input filename extension is preserved by huge/UAVid inference; tile evaluators
append `.png` to the dataset image stem.

OpenCV writes BGR arrays. The source writer functions intentionally compensate
for this in different ways. The tables below describe the intended RGB colors
on disk, followed by the class ids and names. Do not copy an array literal from
a function into a PIL/RGB writer without checking whether that function calls
`cv2.cvtColor`.

## Vaihingen and Potsdam (`pv`)

Both datasets use the same six semantic classes and canonical RGB palette from
the dataset modules:

| Id | Class | RGB on disk |
|---:|---|---|
| 0 | ImSurf | `(255, 255, 255)` white |
| 1 | Building | `(0, 0, 255)` blue |
| 2 | LowVeg | `(0, 255, 255)` cyan |
| 3 | Tree | `(0, 255, 0)` green |
| 4 | Car | `(255, 204, 0)` yellow |
| 5 | Clutter | `(255, 0, 0)` red |

The tile evaluator's `label2rgb` fills BGR-equivalent arrays and writes them
with `cv2.imwrite`, so the resulting file has the canonical RGB colors above.
The huge-image `pv2rgb` function follows the same OpenCV convention. Use
`--rgb` for tile evaluation or `-d pv` for huge-image inference.

## LoveDA

LoveDA's seven classes are:

| Id | Class | RGB on disk |
|---:|---|---|
| 0 | background | `(255, 255, 255)` white |
| 1 | building | `(255, 0, 0)` red |
| 2 | road | `(255, 255, 0)` yellow |
| 3 | water | `(0, 0, 255)` blue |
| 4 | barren | `(159, 129, 183)` mauve |
| 5 | forest | `(0, 255, 0)` green |
| 6 | agricultural | `(255, 195, 128)` peach |

`loveda_test.py --rgb` converts the RGB palette to BGR before OpenCV write, so
these are the colors a normal RGB viewer should see. The evaluator's default
indexed output remains ids 0 through 6.

## UAVid (`uavid`)

The eight-class palette used by both `inference_uavid.py` and the huge-image
`-d uavid` branch is:

| Id | Class | RGB on disk |
|---:|---|---|
| 0 | Building | `(128, 0, 0)` |
| 1 | Road | `(128, 64, 128)` |
| 2 | Tree | `(0, 128, 0)` |
| 3 | LowVeg | `(128, 128, 0)` |
| 4 | Moving_Car | `(64, 0, 128)` |
| 5 | Static_Car | `(192, 0, 192)` |
| 6 | Human | `(64, 64, 0)` |
| 7 | Clutter | `(0, 0, 0)` |

The sequence script calls `cv2.cvtColor` after building this palette. The
huge-image branch does likewise. Both therefore write the same canonical RGB
colors on disk.

## Other huge-image mappings

These mappings are available only through `inference_huge_image.py`:

### `-d landcoverai`

| Id | RGB on disk |
|---:|---|
| 0 | `(233, 193, 133)` |
| 1 | `(255, 0, 0)` |
| 2 | `(0, 255, 0)` |
| 3 | `(255, 255, 255)` |

The source maps ids 0/1/2/3 to soil/building/grass/other-like colors, but this
checkout does not include a LandCoverAI dataset module; confirm the external
label convention before using it.

### `-d building`

| Id | RGB on disk |
|---:|---|
| 0 | `(255, 255, 255)` white |
| 1 | `(0, 0, 0)` black |

## Shape and file checks

For every output, check that:

- indexed tile masks have dtype-compatible values in `0..num_classes-1`;
- RGB masks have exactly three channels and only the selected palette colors
  (apart from an all-zero color if a model emits an unmapped class id);
- huge/UAVid outputs have exactly the source image height and width after
  cropping; and
- filenames remain paired with the intended input stem/sequence.

A palette mismatch can look like a successful segmentation while silently
swapping classes. Compare a tiny known id mask against this table before
submitting RGB results.

## Synthetic verification cases

- **Exact padded restoration:** use a synthetic source shape `(5, 7)` and patch
  `(3, 4)`. Bottom/right padding produces `(6, 8)` and the source crop
  `output_mask[-5:, -7:]` must restore exactly `(5, 7)`. Also test an exactly
  divisible shape such as `(6, 8)`; it must not lose a row or column.
- **Wrong dataset/RGB mapping:** use a tiny indexed mask containing ids `0`
  through `5` and render it once as `pv` and once as `uavid`. The outputs must
  differ in both class count assumptions and colors (for example, PV id 1 is
  blue `(0,0,255)` while UAVid id 1 is road `(128,64,128)`). A run that uses
  `-d uavid` with a six-class PV checkpoint, or treats an RGB mask as indexed
  labels, is a deliberate negative case even if a PNG is written successfully.
