# SimpleCV Troubleshooting

## Import fails: `Cannot load OpenCV library which is required by SimpleCV`

**Symptoms**

- `import SimpleCV` raises `ImportError: Cannot load OpenCV library which is required by SimpleCV`.
- `import cv2` works but `import cv` or `import cv2.cv` fails.

**Likely cause**

SimpleCV 1.3 expects OpenCV 2.4-era Python bindings. Modern OpenCV 3/4 packages often remove the `cv` compatibility module.

**Recovery**

1. Verify the environment is Python 2.7.
2. Run:
   ```bash
   python -c "import cv2; print(cv2.__version__, hasattr(cv2, 'cv'))"
   python -c "import cv; print(cv.CV_8UC3)"
   ```
3. Install an OpenCV build that exposes `cv` / `cv2.cv`.
4. Re-run `python -c "import SimpleCV; print(SimpleCV.__version__)"`.

Do not treat a modern `opencv-python` import as sufficient unless the old compatibility symbols are present.

## OpenCV import fails with `libjasper.so.1`

**Symptoms**

- `import cv2` or `import cv` raises `ImportError: libjasper.so.1: cannot open shared object file`.

**Likely cause**

A legacy OpenCV 2.4 build is installed but the matching Jasper library ABI is missing or too new.

**Recovery**

Install a compatible Jasper package for the OpenCV build, or choose an OpenCV package bundle that carries the matching dependency. Re-run both `import cv2` and `import cv` checks before importing SimpleCV.

## Python 2 shell imports fail in `decorator` or IPython

**Symptoms**

- Importing SimpleCV reaches IPython or traitlets and then fails with a Python 2 syntax error such as:
  ```text
  print('Error in generated code:', file=sys.stderr)
  ```

**Likely cause**

A Python-3-only version of `decorator` or another IPython dependency was installed in the Python 2 environment.

**Recovery**

Use Python-2-compatible versions, for example `decorator<5`. If `pip check` reports `wcwidth` requiring `backports-functools-lru-cache`, install `backports.functools_lru_cache`.

## `pygame` or SDL display errors

**Symptoms**

- Import succeeds, but `Image.show()` or `Display()` fails because no video device or X/Wayland display exists.
- `pygame.error: No available video device`.

**Recovery**

For non-interactive checks:

```bash
export SDL_VIDEODRIVER=dummy
python -c "from SimpleCV import Display; d = Display((64,64), headless=True); print('ok')"
```

Prefer `Image.save(...)` and bundled helper scripts that write files instead of showing windows. Only run camera/display loops when the user explicitly wants an interactive hardware session.

## `simplecv --help` appears to hang

**Symptoms**

- The shell prints a banner and then waits at `>>>`.

**Likely cause**

The `simplecv` entry point starts an interactive shell even for help-like invocations.

**Recovery**

Use a bounded command:

```bash
SDL_VIDEODRIVER=dummy timeout 10 simplecv --help
```

Treat a printed banner plus prompt as shell-start evidence, not as a package import failure.

## Sample image names fail

**Symptoms**

- `Image('simplecv')` or `Image('coins.jpg', sample=True)` fails or returns an empty image.

**Likely cause**

Package data was not installed, the wrong SimpleCV package is being imported, or the code is running from a partially copied source tree without `sampleimages`.

**Recovery**

1. Print the package version and import file.
2. Reinstall SimpleCV with package data included.
3. Prefer bundled sample names in docs and tests rather than absolute source-checkout paths.

## Optional detector integrations fail

| Symptom | Likely cause | Recovery |
|---|---|---|
| `findBarcode` returns nothing or warns | `zxing` missing or path unavailable | Install ZXing only for barcode workflows and pass the correct path when required. |
| `readText()` fails | `tesseract` missing | Install tesseract only for OCR workflows; keep OCR optional for core image tasks. |
| `findKeypoints(..., flavor='SURF')` fails | OpenCV build lacks nonfree/SURF or legacy feature factory | Try another available flavor or document the OpenCV build limitation. |
| `SVMClassifier` warns about Orange | `orange` / `Orange` missing | Use `KNNClassifier`, `NaiveBayesClassifier`, or `TreeClassifier`, or provision Orange explicitly. |

## Hardware examples fail

Physical camera, Kinect, Vimba, scanner, Arduino, and web-camera examples require devices, drivers, or services. Do not run them as automatic verification. Route setup questions to `sub-skills/acquisition-display-shell/` and keep core verification on static images or virtual sources unless the user requests hardware work.
