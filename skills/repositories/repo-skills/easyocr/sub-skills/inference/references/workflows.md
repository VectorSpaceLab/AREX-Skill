# EasyOCR Inference Workflows

This reference collects the normal OCR patterns that users ask for.

## 1. Basic OCR from one image

```python
import easyocr

reader = easyocr.Reader(['en'], gpu=False)
result = reader.readtext('path/to/image.png')
print(result)
```

Use this for the default "read text from an image" request. The image can also
be a NumPy array, bytes, or a raw image URL.

## 2. Text only, boxes, or structured output

- `detail=0` -> plain text strings.
- `detail=1` -> `(box, text, confidence)` tuples.
- `output_format='dict'` -> dictionaries.
- `output_format='json'` -> JSON strings.

Example:

```python
lines = reader.readtext('path/to/image.png', detail=0)
boxes = reader.readtext('path/to/image.png', output_format='dict')
```

## 3. Control recognition behavior

Useful options when the result needs tighter control:

- `allowlist` and `blocklist` for character filtering.
- `paragraph=True` to merge nearby boxes.
- `rotation_info=[90, 180, 270]` to try rotated crops.
- `contrast_ths` and `adjust_contrast` for low-contrast text.
- `min_size`, `text_threshold`, `low_text`, and `link_threshold` for detection
  sensitivity.

Example:

```python
reader.readtext(
    'path/to/image.png',
    allowlist='0123456789',
    paragraph=True,
    rotation_info=[90, 180, 270],
)
```

## 4. Split detection and recognition

Use this when you already have a crop or when you want to inspect the detected
boxes before recognition.

```python
img = 'path/to/image.png'
boxes, free = reader.detect(img)
text = reader.recognize(img, boxes[0], free[0])
```

If you pass no box lists to `recognize`, it treats the full image as one text
region.

## 5. Batched OCR

`readtext_batched` accepts a list of same-sized images and returns one result
list per image.

```python
batch = [img1, img2, img3]
results = reader.readtext_batched(batch)
```

This is the right route when multiple same-sized images must be processed in a
single call.

## 6. CLI equivalent

The CLI mirrors the API routing but is less flexible for booleans because of the
current parser types. Prefer the Python API when you need exact control.

```bash
easyocr -l en -f path/to/image.png
```

## Practical shortcuts

- Use `gpu=False` when you want a deterministic CPU baseline.
- Use `download_enabled=False` when you already have the model cache and want
  to fail fast instead of downloading.
- Use `../../../scripts/inspect_runtime.py` before a long run if you only need to verify
  the install.
- Use `scripts/readtext_smoke.py` for a one-image sanity check.

## Output interpretation

- A confidence value near `1.0` is strong.
- Boxes are polygon coordinates in image space.
- The `paragraph` mode merges line-level results, so it may reduce the number
  of boxes compared with the default mode.
