# Workflows

These workflows route the existing GIMP-ML plugin contracts without pretending that
model inference is available. Use the generic `WEIGHTS_ROOT` placeholder; never
embed a host-specific checkout path in a runtime instruction.

## Common preflight

1. Make a copy or save point for the GIMP document if the user needs rollback.
2. Select the intended layer and make it image-sized. For a layer that does not fill
   the image, use **Layer -> Layer to Image Size** in GIMP.
3. Keep RGB pixels where possible. The plugins drop alpha, but unusual modes and
   channel counts were not verified.
4. Check assets without downloading:

   ```text
   python scripts/check_model_assets.py WEIGHTS_ROOT
   ```

   Require an all-present report for the selected workflow. The checker does not
   inspect checkpoint contents or prove architecture compatibility.
5. Probe the backend without allocation:

   ```text
   python scripts/probe_torch_backend.py
   ```

   Select **Force CPU** if CUDA is unavailable, the probe reports an error, or the
   available device is too constrained. CUDA availability alone is not proof that a
   model can allocate its working memory.
6. Explain the expected output and the unverified status before invoking the GIMP
   plugin. Never substitute a downloaded or unrelated checkpoint.

## Restoration route

For **deblur**, **dehaze**, **denoise**, or **enlighten**:

1. Select one image-sized source layer.
2. Choose the operation and set **Force CPU** according to the preflight result.
3. Confirm the relevant checkpoint set: deblur has `best_fpn.h5` plus the sibling
   `mymodel.pth` required by the inspected helper; denoise has two; the other
   operations have one observed primary file.
4. Run the plugin only in a real, compatible GIMP/Python 2 host with the matching
   optional model package and checkpoint. This verification cannot execute it
   without that compatible host and the external assets.
5. Check that a new result layer appears at the expected image dimensions. Compare
   visually to the preserved source; do not treat a layer insertion as proof of model
   quality.

## Analysis-map route

For **monocular depth**:

1. Use a single image-sized RGB-like layer.
2. Set Force CPU if required. The source scales input toward a 640-pixel target and
   emits a normalized 8-bit map repeated into three channels.
3. Treat the result as relative disparity visualization. Do not measure distances or
   claim calibrated depth.

For **semantic segmentation**:

1. Use a single image-sized layer containing at least one documented supported class.
2. Set Force CPU if required and verify `deeplabv3/deeplabv3+model.pt` is present.
3. Expect an output-sized class-index visualization. The source declares a palette
   but returns a repeated numeric class map in the observed path; inspect the actual
   host result before describing colors or labels.

## Portrait parsing route

For **face parsing**:

1. Confirm the selected layer is a portrait image of one person, not a general scene
   or a group image.
2. Ensure `faceparse/79999_iter.pth` is present and select Force CPU if needed.
3. Expect a 19-label map generated from a 512x512 normalized input and resized back
   to the source dimensions, then colorized by the plugin.
4. Preserve the source layer. A valid-looking colored layer cannot establish that
   every facial region is correctly parsed; quality and checkpoint compatibility are
   unverified.

## Super-resolution route

1. Select an image-sized layer and choose Scale from the observed 1--4 range.
2. If either dimension is around or above 400 pixels, keep **Use as filter = True**
   unless a tested host and memory budget justify another choice. The source tiles
   with about 300-pixel blocks in this mode.
3. Check `super_resolution/model_srresnet.pth` and select Force CPU when CUDA memory
   is uncertain.
4. Confirm expected output dimensions after the requested scale. At scale 1 the
   source intends a result layer; for larger scales it intends a new GIMP image.
5. If memory fails, reduce the source size or use tiled/filter mode; do not assume
   changing only the device flag fixes a host-level OOM.

## Frame interpolation route

1. Select distinct start and end layers in the same image.
2. Make both image-sized and verify equal dimensions. Remove or account for alpha;
   the source discards it.
3. Choose a dedicated output folder. Confirm it exists or can be created, is writable,
   and does not contain files the user wants protected. The plugin writes PNG files;
   it does not add a result layer in the observed code.
4. Check all three assets under `interpolateframes/`: `contextnet.pkl`,
   `flownet.pkl`, and `unet.pkl`.
5. Set Force CPU if needed. The source pads to multiples of 32 and performs four
   rounds, intending 17 output PNGs (`img0.png` through `img16.png`).
6. Review generated files and preserve the input layers. Output-file success alone
   does not verify temporal quality.

## Synthetic difficult cases for later usability verification

- **Mismatch-and-memory case:** use a selected layer smaller than the image and a
  5000x5000 synthetic RGB fixture; request super-resolution with filter disabled,
  then with filter enabled and Force CPU. The route should reject/repair the layer
  size first, warn about output/memory cost, and never claim inference when assets
  are absent.
- **Temporal-and-filesystem case:** use two same-sized synthetic RGB fixtures whose
  dimensions are not divisible by 32 and an output directory containing a protected
  `img0.png`; verify the route detects the collision, explains padding and the
  intended 17-file output, and does not overwrite the protected file during a
  preflight-only check.
