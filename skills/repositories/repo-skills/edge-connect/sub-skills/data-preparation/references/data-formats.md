# Data formats

EdgeConnect consumes three kinds of inputs: images, masks, and edges. It also relies on file lists (`flist` files) when you do not pass a Python list directly.

## File-list loading rules
`Dataset.load_flist` behaves like this:

1. If the input is already a Python list, it is used as-is.
2. If the input is a directory path, only immediate `*.jpg` and `*.png` files are collected.
3. Directory results are sorted lexicographically before use.
4. If the input is a file path, the loader first tries to read it as a text flist with one path per line.
5. If text parsing fails, the runtime falls back to a one-item list containing the file path itself; anything else falls back to an empty list.

### Practical consequences
- Directory mode is **not recursive** in the runtime loader.
- If your data lives in nested folders or uses extensions beyond `jpg`/`png`, build a text flist instead of passing the directory directly.
- Keep flist entries plain paths only. Avoid headers and comments.
- For text flists, use one path per line and keep the list sorted so paired datasets stay stable.
- Avoid single-entry text flists when possible: the runtime loader uses `np.genfromtxt`, and a one-line file can collapse into an unsized value instead of a normal list.

## Recommended folder layout
A simple custom dataset usually looks like this:

```text
my-dataset/
  images/
  masks/
  edges/
  train.flist
  val.flist
  test.flist
```

The source-derived example pattern is simply a dataset folder with sibling image and mask folders:

```text
<dataset-name>/images/
<dataset-name>/masks/
```

## Image inputs
- Image flists should point to RGB or grayscale image files that can be decoded by the runtime image stack.
- If you provide a directory directly, only top-level `jpg` and `png` files are visible to the runtime loader.
- Use the bundled flist builder when you want recursive scanning; it resolves the discovered files and writes absolute paths by default.

## Mask inputs
Mask files should represent the missing region as nonzero pixels. After resizing, the runtime loader thresholds masks so any nonzero value becomes foreground.

### Mask modes
- `MASK=1`: random block generated on the fly.
- `MASK=2`: half-image block generated on the fly.
- `MASK=3`: external masks sampled from the mask flist.
- `MASK=4`: external masks mixed with random blocks.
- `MASK=5`: external masks mixed with random blocks and half-image masks.
- `MASK=6`: test-mode one-to-one masks.

### Mask mode gotchas
- `MASK=4` and `MASK=5` still need an external mask flist because one branch always samples external masks.
- `MASK=6` is used only in test mode and requires image/mask index alignment.
- For train and validation runs, external masks can act as a mask pool; they do not need one-to-one pairing with images.

## Edge inputs
### Edge mode `EDGE=1`
- Uses Canny edge detection on the grayscale image.
- `SIGMA` controls the Gaussian smoothing.
- `SIGMA=0` randomizes the blur strength per sample.
- `SIGMA=-1` disables edge output and returns an all-zero edge map.
- In test mode, the loader suppresses edge detection inside masked regions.

### Edge mode `EDGE=2`
- Loads edges from the edge flist.
- Resizes them to the image size.
- If `NMS=1`, the loaded edge map is thinned by multiplying it with a Canny map of the current image.

### Edge mode gotchas
- External edge lists must stay in the same order as the image list.
- Edge files should be prepared at the same spatial size or at least survive resizing cleanly.
- Prefer single-channel or grayscale edge rasters so the downstream tensor shape stays predictable.

## File pairing rules
- `EDGE=2` requires one edge entry per image entry.
- `MASK=3` does not require index pairing for train or validation because masks are sampled from a pool.
- `MODE=2` forces mask mode `6`, so test masks must match test images one to one.
- If you mix image, mask, and edge lists, keep their sort order deterministic.
