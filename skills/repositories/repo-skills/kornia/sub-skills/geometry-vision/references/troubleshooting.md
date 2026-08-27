# Geometry Vision Troubleshooting

## `ValueError: Input src must be a BxCxHxW torch.Tensor`

Most warps require batched channel-first images. Convert `H,W,C` or `C,H,W` data
before calling geometry APIs:

```python
if img.ndim == 3:          # C,H,W
    img = img.unsqueeze(0) # B,C,H,W
```

If the data came from an image loader, also verify dtype/range. Kornia
augmentations expect float images in `[0,1]`; geometry warps preserve numeric
values but downstream augmentation or visualization may not.

## Output shape is swapped or unexpectedly stretched

Cause: using `(width, height)` where Kornia expects `(height, width)`.

Fix:

```python
B, C, H, W = img.shape
out = warp_perspective(img, H_src_to_dst, (H, W))
resized = resize(img, (new_h, new_w))
```

When porting OpenCV snippets, flip `cv2` size tuples before passing to Kornia.

## Warp is shifted, mirrored, or moving the wrong direction

Check matrix direction before changing signs:

- `warp_affine` and `warp_perspective` take source→destination pixel matrices.
- Internally, the sampler inverts that matrix to sample source pixels for each
  destination pixel.
- `homography_warp` default is different: destination→source normalized matrix.
  Set `normalized_homography=False` if you already have a source→destination
  pixel homography.

Diagnostic:

1. Apply the matrix to a few known source corner points with `transform_points`.
2. Verify the transformed points land where expected in destination pixel space.
3. Run a tiny identity or one-pixel translation before testing a large real
   transform.

## Points or rotation center use `(y,x)` by mistake

Kornia point tensors use `(x,y)`. A common bug is using row/column order from
NumPy indexing as if it were pixel point order.

Fix:

```python
center = torch.tensor([[float(W - 1) / 2, float(H - 1) / 2]], device=device, dtype=dtype)
points = torch.tensor([[[x0, y0], [x1, y1], [x2, y2], [x3, y3]]], device=device, dtype=dtype)
```

## Different APIs disagree after the same homography

Likely causes:

- `align_corners` differs between calls.
- One call uses pixel coordinates while the other uses normalized grid
  coordinates.
- The homography was inverted twice or not inverted when switching between
  `warp_perspective` and `homography_warp`.

Fix: make the convention explicit in every call and test on a non-square image.
Square images and centered transforms can hide swapped size or inverse-order
mistakes.

## `get_perspective_transform` returns NaNs or a poor matrix

Likely causes:

- Source or destination points are repeated, collinear, or nearly collinear.
- The quadrilateral has near-zero area or an inconsistent corner order.
- Source and destination tensors have different dtype or device.
- Points are integer tensors.

Fix:

- Use float32/float64 tensors on the same device.
- Use a consistent order such as top-left, top-right, bottom-right, bottom-left.
- Validate polygon area before solving.
- For noisy many-point data, use `RANSAC("homography")` or a DLT homography fit
  instead of forcing a four-point transform.

## PnP fails or gives unstable extrinsics

`solve_pnp_dlt` needs at least six non-degenerate 3D/2D pairs. It cannot solve
when all 3D points for a batch item lie on one line or one plane; a twisted
cubic configuration is also bad and is not fully detected.

Fix:

- Use `world_points: (B,N,3)`, `img_points: (B,N,2)`, `intrinsics: (B,3,3)`,
  with `N>=6`.
- Use float32 or float64; prefer float64 for validation.
- Use spatially varied 3D points with positive camera depth after projection.
- Verify the returned `(B,3,4)` world→camera matrix by reprojection error.

## Camera projection explodes or returns inf/NaN

Perspective projection divides by depth. Near-zero or negative `z` values cause
large coordinates, invalid gradients, or non-finite outputs.

Fix:

- Restrict camera-frame `z` or depth maps to a positive range away from zero,
  e.g. `z >= 1` for tests and smokes.
- Use realistic intrinsics (`fx/fy` in pixel units, principal point near the
  image center) instead of fully random matrices.
- Clamp or mask invalid depth before calling `project_points`, `cam2pixel`, or
  depth warping.

## Fundamental/essential estimation is numerically unstable

Symptoms include multiple implausible candidates, poor epipolar distances, or
large CUDA/CPU differences.

Fix:

- Keep pixel coordinates in realistic image bounds.
- Normalize or use well-conditioned correspondences where appropriate.
- Use float64 for precision-sensitive checks.
- Rank candidates by Sampson or symmetric epipolar distance.
- For essential matrices, use cheirality/positive-depth checks to select motion.
- Be aware that SVD-heavy geometry can be sensitive on CUDA float32; Kornia casts
  internally where appropriate, but degenerate data still fails.

## TF32 changes CUDA float32 results

CUDA TF32 matmul can round float32 matrix operations enough to fail tight
geometry tests. This is most visible in camera, box, homography, fundamental,
and essential calculations.

Fix:

- Use integer-valued or in-bounds coordinates for exact-reference tests.
- Keep depths positive and not near zero.
- Prefer float64 for reference generation and critical validation.
- If a task enables TF32 for performance, compare with realistic tolerances and
  do not treat tiny hardcoded CPU differences as algorithmic failures.

## Half precision fails in geometry solvers

Many PyTorch linear algebra kernels do not support float16/bfloat16 on CPU, and
CUDA half-precision solver failures can corrupt the CUDA context asynchronously.

Fix:

- Use float32/float64 for camera, epipolar, PnP, SVD, inverse, and triangulation
  workflows.
- Limit half precision to simple image warps only after a backend-specific smoke
  proves support.
- Run half-precision CUDA checks in isolation if you must test them.

## MPS backend limitations

Known MPS limitations relevant to this sub-skill include lack of float64 tensors,
unsupported 2D `grid_sample` border padding, and unsupported nearest-mode 3D
`grid_sample` for volumes.

Fix:

- Avoid float64 on MPS; skip gradcheck-like validation there.
- Prefer zero padding or a verified workaround instead of 2D border padding.
- Do not silently replace nearest 3D volume sampling with bilinear for masks or
  labels; it changes semantics.

## `ImageRegistrator` refuses shape mismatch

By default, registration expects source and destination images to have the same
shape. If resizing the source to destination size is acceptable, construct with
`allow_shape_mismatch=True`; otherwise resize or crop explicitly before
registration.

Also check:

- Model type spelling: `homography`, `similarity`, `translation`, `scale`, or
  `rotation`.
- Learning rate and number of iterations.
- Whether the images have enough shared structure and compatible intensity
  ranges.

## `HomographyTracker` downloads weights or fails in offline mode

The default tracker builds feature matchers, including heavyweight learned or
pretrained components. In no-download contexts, do not instantiate the default
constructor. Inject explicit matchers and RANSAC modules that are already
available, or use low-level homography APIs.

If tracking returns `(H, False)`:

- Check `keypoints0_num`, `keypoints1_num`, and `inliers_num`.
- Increase texture, resolution, or matcher capacity.
- Lower `minimum_inliers_num` only when the scene truly has few reliable points.
- Reset target state when the scene changes.

## Point-cloud I/O errors

PLY helpers require valid point tensor shapes and user-writable file locations.
Validate the point tensor before writing, and do not use point-cloud file output
as proof that the 3D geometry is correct; also check finite values, depth sign,
and coordinate frame.

