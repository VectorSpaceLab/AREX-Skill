# Install and Runtime Reference

## When to read this

Read this when SimpleCV will not import, the `simplecv` shell behaves unexpectedly, or a task needs a realistic legacy runtime profile before using the workflow sub-skills.

## Verified runtime profile

SimpleCV 1.3 is a legacy Python 2 package. The verified inspection environment for this skill used these public/runtime facts:

- Python 2.7
- `SimpleCV` distribution version `1.3`, package version `SimpleCV.__version__ == '1.3.0'`
- OpenCV 2.4-era Python bindings where both `import cv2` and `import cv` work
- `numpy`, `scipy`, `Pillow`/PIL, `pygame`, `svgwrite`, `IPython`, and `nose`
- A headless-safe display configuration can use `SDL_VIDEODRIVER=dummy`

Do not expect modern Python 3 or OpenCV 4 environments to run unmodified SimpleCV source. The package imports Python 2 modules such as `urllib2`, `SocketServer`, `SimpleHTTPServer`, and old OpenCV symbols such as `cv2.cv` / `cv`.

## Generic install strategy

Use a Python 2.7 environment, then install a SimpleCV-compatible OpenCV build before importing SimpleCV:

```bash
python -c "import sys; print(sys.version)"
python -c "import cv2, cv; print(cv2.__version__)"
python -c "import SimpleCV; print(SimpleCV.__version__)"
```

A working OpenCV check must prove the old compatibility module exists. If `import cv` fails, core SimpleCV import usually fails with `Cannot load OpenCV library which is required by SimpleCV`.

For package managers that still provide legacy builds, the equivalent dependency set is:

```text
python=2.7
opencv=2.4.x with cv/cv2.cv compatibility
numpy
scipy
pillow or PIL
pygame
svgwrite
ipython
nose
```

If using pip for Python 2 wheels, pin Python-2-compatible packages. For example, `svgwrite==1.3.1` and `pygame==1.9.6` were compatible in inspection. If IPython pulls a Python-3-only `decorator`, pin `decorator<5`.

## Minimal import and sample-image smoke

Use this smoke test after installation:

```bash
python - <<'PY'
import SimpleCV
from SimpleCV import Image, Color, Camera, Display
img = Image('simplecv')
print(SimpleCV.__version__)
print(img.size())
print(Color.RED)
PY
```

Expected signal:

- SimpleCV version prints `1.3.0`.
- `Image('simplecv')` resolves a bundled sample image and reports a nonzero size.
- Importing `Camera` and `Display` succeeds even if no physical camera or real display is available.

## Shell behavior

The `simplecv` console entry point starts an interactive shell. A help-style run may print the banner and then wait at a prompt. When scripting, always bound it:

```bash
SDL_VIDEODRIVER=dummy timeout 10 simplecv --help
```

A successful bounded shell smoke prints the SimpleCV banner, command list, and documentation hints. If it stays interactive, kill it rather than treating the prompt as a hang in the package import path.

## Headless display behavior

If no window system is available, set:

```bash
export SDL_VIDEODRIVER=dummy
```

Prefer `Image.save(...)`, `Display(displaytype='notebook')`, or `Display(..., headless=True)` for non-interactive checks. Do not use infinite camera/display example loops as verification unless the user explicitly asks for an interactive hardware workflow.

## Sample image usage

Many examples use sample names rather than file paths:

```python
from SimpleCV import Image
img = Image('simplecv')
coins = Image('coins.jpg', sample=True)
```

This is safer than relying on a source checkout because SimpleCV packages sample images as package data. If these names fail, inspect whether package data was installed and whether the environment is importing the intended SimpleCV package.

## Optional integrations

Optional modules are detected by imports in `SimpleCV.base` and may be absent without blocking core image workflows:

| Optional integration | Signal | Typical handling |
|---|---|---|
| `freenect` / Kinect | `Kinect()` warnings or import flag false | Treat as optional hardware; do not install unless required. |
| `zxing` | barcode detection unavailable | Install only for barcode workflows. |
| `tesseract` | OCR unavailable | Install only for OCR workflows. |
| `pyscreenshot` | screen capture unavailable | Install only for screenshot workflows. |
| `Orange` / `orange` | `SVMClassifier` unavailable or warning | Use KNN/NaiveBayes/Tree alternatives unless Orange is required. |
| `pymba` / Vimba | industrial camera unavailable | Optional hardware stack; do not treat as core failure. |

## Bundled diagnostics

Run these from the generated skill tree when diagnosing a future environment:

```bash
python scripts/check_env.py
SDL_VIDEODRIVER=dummy python scripts/check_display_headless.py
```

If the target package is in a local checkout rather than installed, pass `--repo-root` to add that checkout to `sys.path` explicitly. Do not rely on the current working directory accidentally shadowing another SimpleCV install.
