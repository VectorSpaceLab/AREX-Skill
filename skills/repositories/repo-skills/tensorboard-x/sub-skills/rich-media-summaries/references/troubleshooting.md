# Troubleshooting

This reference covers the most common rich-media summary failures.

## Image problems

### Symptoms
- the image looks wrong or is empty
- `dataformats` errors appear
- boxes are drawn in the wrong place

### Likely causes
- the tensor layout does not match the `dataformats` string
- the array is not a valid image rank
- box coordinates are not `xyxy`

### First fix
- confirm whether the data is `CHW`, `HWC`, `HW`, or batched `NCHW`
- use a tiny smoke array from the bundled script as a shape reference
- make sure float images are in a reasonable range before they are scaled to `uint8`

## Audio problems

### Symptoms
- the helper raises a missing `soundfile` import
- the output is clipped or silent

### Likely causes
- `soundfile` is not installed
- the signal is not 1-D
- the values are outside `[-1, 1]`

### First fix
- install `soundfile`
- flatten the signal to one dimension
- check the sample rate and the amplitude range

## Video problems

### Symptoms
- `moviepy` or `imageio` import errors
- an empty or malformed GIF-backed summary
- 1-channel video does not render as expected

### Likely causes
- the optional video packages are missing
- the input is not 5-D
- the `dataformats` string is wrong
- the installed moviepy/imageio combination does not like 1-channel input

### First fix
- install `moviepy` and `imageio>=2.29.0`
- keep the smoke clip short and deterministic
- re-check the shape conversion before blaming the encoder

## Histogram and PR curve problems

### Symptoms
- empty histograms
- non-finite value errors
- PR curves with mismatched lengths

### Likely causes
- the data array is empty
- there are NaN or inf values
- labels and predictions are not aligned

### First fix
- clean the input arrays before logging
- confirm that labels and predictions have the same length
- use the raw variants only when you already computed the bucket data elsewhere

## Text and mesh problems

### Symptoms
- text does not render as expected
- mesh viewers show broken geometry

### Likely causes
- Markdown or escaping is not what you intended
- vertices, faces, or colors do not match the expected layout

### First fix
- simplify the text to a short plain string first
- verify the geometry arrays against the tables in `references/data-formats.md`

## When a fix is still unclear

Run the bundled smoke helper and compare your payload with the tiny known-good fixture. If the smoke helper works but your payload fails, the issue is usually shape, dtype, or optional dependency selection.
