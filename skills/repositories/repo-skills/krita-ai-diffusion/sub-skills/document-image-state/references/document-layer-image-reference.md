# Document, Layer, Image, and Mask Reference

This reference covers data structures that bridge Krita document state and
workflow payloads.

## Geometry helpers

`ai_diffusion.image` defines lightweight geometry named tuples:

- `Extent(width, height)`: image size. Helpers include `multiple_of`,
  `is_multiple_of`, aspect-preserving scaling, pixel count, longest/shortest
  side, `from_qsize`, and arithmetic operations.
- `Point(x, y)`: coordinate with arithmetic and `clamp(bounds)`.
- `Bounds(x, y, width, height)`: rectangle with `offset`, `extent`, `area`,
  `from_extent`, `from_points`, `pad`, `clamp`, `restrict`, `expand`,
  `intersection`, `union`, `relative_to`, and Qt conversion helpers.

Use these helpers instead of ad-hoc tuples when explaining selection, region,
mask, crop, tile, or canvas coordinates.

## Image helpers

`Image` wraps a Qt `QImage` and provides:

- loading/creating/copying/scaling/cropping/flattening,
- bytes/base64 conversion,
- packed Krita byte conversion,
- WebP/PNG/JPEG output through `ImageFileFormat`,
- mask operations and average/pixel comparison,
- PNG metadata writing,
- conversion to pixmap/icon/PIL/NumPy where supported.

`DummyImage` represents extent-only placeholder images for tests or dry runs.
`ImageCollection` stores image batches and can serialize/deserialize image
collections with offsets.

## Mask helpers

`Mask(bounds, data)` stores bounds plus grayscale data. Useful constructors and
operations include:

- `Mask.transparent(bounds)`,
- `Mask.rectangle(bounds, context)`,
- `Mask.load(path)`,
- `Mask.crop(mask, bounds)`,
- `mask.value(x, y)`,
- `mask.to_image(extent=None)`.

In inpaint workflows, mask extent must match the image/crop extent used by the
request. If a selection appears shifted, compare `Bounds.relative_to` and crop
origin carefully.

## Krita document and layer state

Document/layer modules wrap Krita objects and expose operations for:

- active document/layer discovery,
- layer type identification,
- bounds and pixel extraction,
- creating/applying generated layers or masks,
- restoring active layer state,
- collecting selection masks and region masks,
- maintaining layer groups and transparency masks.

Outside Krita, tests rely on mock Krita classes. Do not assume real Krita UI is
available during headless package inspection.

## Regions and control layers

Region state ties prompts and masks to parts of the canvas. Important concepts:

- `RootRegion` and `Region` store background/region prompts and masks.
- `RegionLink`: `direct`, `indirect`, `any` for linking layers/regions.
- `process_regions` and `get_region_inpaint_mask` build region masks for
  workflow payloads.
- `ControlLayer` stores control mode, layer ID, preset strength, custom
  strength, and active range.

Route to `inference-workflows` once regions have been converted into
`ConditioningInput.regions` and `ControlInput` objects.

## Apply behavior after generation

Apply settings decide where generated results go:

- modify active layer,
- new layer on top,
- new layer above active,
- replace/update region layers,
- layer group,
- layer group plus transparency mask,
- layer group without hiding.

If a user reports wrong layer ordering or hidden/missing region outputs, inspect
apply behavior settings and layer/group operations, not just `WorkflowInput`.

## Common geometry debugging pattern

For selection/inpaint/crop bugs, collect:

1. Canvas `Extent`.
2. Selection or region `Bounds` in canvas coordinates.
3. Padded/clamped context bounds.
4. `ImageInput.extent.input/initial/desired/target`.
5. Mask extent and whether selected pixels are white in the expected relative
   coordinates.
6. Final apply bounds/layer target.
