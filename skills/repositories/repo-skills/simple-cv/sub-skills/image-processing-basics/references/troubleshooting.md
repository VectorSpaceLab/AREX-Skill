# Image Processing Troubleshooting

## Image is empty or cannot be loaded

**Symptoms**

- `img.isEmpty()` is true.
- A later method fails because width or height is zero.

**Causes**

- The user supplied a bad path.
- Package sample images were not installed.
- The wrong SimpleCV package is being imported.

**Fix**

1. Print `SimpleCV.__version__` and the image dimensions.
2. Try a package sample: `Image('simplecv')`.
3. If sample images fail, reinstall SimpleCV with package data and re-run the root `scripts/check_env.py`.
4. Do not fall back to absolute paths from the source checkout in runtime guidance.

## `show()` fails in automation

**Symptoms**

- `pygame.error: No available video device`.
- The script opens a window or blocks in a display loop.

**Fix**

Use `Image.save(...)` and set `SDL_VIDEODRIVER=dummy` for headless checks. Route true display/window tasks to `../acquisition-display-shell/`.

## Drawing appears missing in saved output

**Cause**

SimpleCV drawing layers may not be applied before comparison or file output.

**Fix**

Use:

```python
img.drawText('label')
rendered = img.applyLayers()
rendered.save('out.png')
```

or call `img.save(...)` only after confirming it renders the layer in the workflow being used.

## Colors look swapped

**Cause**

SimpleCV user-facing color constants/tuples and OpenCV internal BGR matrices can be easy to mix.

**Fix**

- Use `Color.RED`, `Color.BLUE`, and named constants when possible.
- When converting to raw cv2/numpy arrays, explicitly record whether the array is RGB, BGR, HSV, HLS, or grayscale.
- Use `toRGB()`, `toBGR()`, `toHSV()`, and `toGray()` rather than assuming channel order.

## Transform output has unexpected size

**Cause**

`rotate`, `warp`, `shear`, `crop`, `scale`, and `resize` have different size semantics.

**Fix**

- Use `img.size()` before and after the operation.
- For crop, check `x`, `y`, `w`, and `h` are in image coordinates.
- For rotation, decide whether fixed-size output or full extents are needed before calling the method.

## DFT or filters fail after an OpenCV upgrade

**Cause**

The package uses OpenCV 2.4 symbols. A modern OpenCV package may import but fail at specific filter calls.

**Fix**

Return to the root `references/troubleshooting.md` OpenCV compatibility checks and prove both `import cv2` and `import cv` before debugging the image method.
