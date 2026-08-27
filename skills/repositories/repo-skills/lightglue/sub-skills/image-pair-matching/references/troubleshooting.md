# Troubleshooting

## Missing image

**Symptom:** `FileNotFoundError` or `Could not read image`.

**Fix:**
- Check that both paths exist.
- Make sure the files are readable images.
- Prefer explicit file paths over shell-expanded assumptions.

## Tensor shape, range, or device mismatch

**Symptom:** shape assertions, device errors, or unexpected matching behavior.

**Fix:**
- Use `load_image(...)` to get a `(3, H, W)` RGB tensor in `[0, 1]`.
- Move the image tensor, extractor, and matcher to the same device.
- Do not feed raw BGR arrays or `uint8` tensors directly into the matcher flow.
- Keep the explicit batch dimension only when you are bypassing the `.extract(...)` helper.

## First-use weight download or network failure

**Symptom:** model initialization stalls or fails while downloading weights.

**Fix:**
- Expect first-use downloads for SuperPoint, DISK, ALIKED, DoGHardNet, and the feature-specific LightGlue heads.
- SIFT avoids neural extractor downloads, but the SIFT LightGlue head still loads pretrained weights on first use.
- Re-run once with network access if the cache is empty.
- If you are offline, seed the cache on a machine with access and rerun in the target environment.

## No or too few keypoints

**Symptom:** `matches` is empty or nearly empty.

**Fix:**
- Increase `--max-keypoints`.
- Increase `--resize` for tiny images.
- Confirm the image pair actually overlaps and contains texture.
- Try a different feature family if the scene is hard for the current one.

## CPU slowness

**Symptom:** matching is noticeably slow on large images.

**Fix:**
- Use `--device auto` or `--device cuda` when available.
- Lower `--max-keypoints`.
- Lower `--resize` if the image resolution is unnecessarily large.
- For the lowest-dependency path, use `sift`, but remember that the matcher still runs the LightGlue head.

## Missing backend

**Symptom:** the script says CUDA, MPS, or SIFT support is unavailable.

**Fix:**
- CUDA missing: re-run with `--device auto` or `--device cpu`.
- MPS missing: re-run with `--device auto` or `--device cpu`.
- OpenCV SIFT missing: use another feature or install an OpenCV build that exposes `cv2.SIFT_create`.
- PyCOLMAP is not required for this bundled CLI.

## Common safe fallback

If you want the least surprising path, use:

```bash
python scripts/match_image_pair.py \
  --image0 /path/to/image0.jpg \
  --image1 /path/to/image1.jpg \
  --features sift \
  --device cpu \
  --no-viz \
  --output matches.png
```

That avoids neural extractor downloads and keeps the output deterministic across hosts.
