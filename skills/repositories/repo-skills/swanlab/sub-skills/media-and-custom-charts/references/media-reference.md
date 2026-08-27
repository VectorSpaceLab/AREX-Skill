# Media reference

This page covers the SwanLab media classes and the public `log_*` wrappers that build them.

## Installed constructor signatures

Observed in the inspection environment:

```text
Text(content: Text | str, caption: str | None = None)
Html(data: Html | str | Path | IO, caption: str | None = None)
Image(data_or_path: Image | str | PIL.Image.Image | numpy.ndarray | torch.Tensor | matplotlib.figure.Figure, mode: str | None = None, caption: str | None = None, file_type: "png" | "jpg" | "jpeg" | "bmp" | None = None, size: int | list | tuple | None = None)
Audio(data_or_path: Audio | str | numpy.ndarray, sample_rate: int = 44100, caption: str | None = None)
Video(data_or_path: Video | str | bytes | BytesIO, caption: str | None = None)
ECharts(chart: Base | ECharts | Table, caption: str | None = None)
Molecule(data: Molecule | str | Path, caption: str | None = None)
Object3D(data: Object3D | str | Path | numpy.ndarray | dict, caption: str | None = None)
```

## Shared logging contract

- The top-level `swanlab.log_text`, `log_html`, `log_image`, `log_audio`, `log_video`, `log_echarts`, `log_object3d`, and `log_molecule` helpers accept a single value or a list.
- A single caption, mode, sample rate, or file type is broadcast across the batch when the helper supports it.
- List kwargs must match the data length or the helper raises `ValueError`.
- A prebuilt media object can be passed directly; a raw value is wrapped into the matching media class.
- Each transform writes a content-addressed file named like `{step:03d}-{sha256[:8]}.ext` and returns a `MediaItem` with `filename`, `sha256`, `size`, and `caption`.

## Class-by-class notes

### `Text`
- Accepts raw text or another `Text` instance.
- Stores content as UTF-8 bytes and writes a `.txt` file.
- Best for short model outputs, snippets, and LLM responses.

### `Html`
- Accepts raw HTML, `Path`, file-like objects, or another `Html`.
- A string ending in `.html` is only treated as a path when the file exists and the string is short enough to plausibly be a path; otherwise it is treated as raw HTML content.
- File-like inputs are read from the start when possible.
- Binary streams are decoded as UTF-8 before storage.
- Writes a `.html` file.

### `Image`
- Accepts a path string, PIL image, NumPy array, Torch tensor, Matplotlib figure, or another `Image`.
- Supported output formats are `png`, `jpg`, `jpeg`, and `bmp`.
- GIF input is rejected.
- `size` can be a max side length or a target size tuple/list.
- Writes an image file with the selected suffix.

### `Audio`
- Accepts a path string, NumPy array, or another `Audio`.
- Raw arrays must use `float32`, `float64`, `int16`, or `int32` and must have one or two channels.
- One-dimensional arrays are reshaped to mono automatically.
- The file is stored as `.wav`.

### `Video`
- Accepts GIF bytes, a GIF path string, a `BytesIO`, or another `Video`.
- Current support is GIF-only.
- Path inputs are checked by extension and GIF magic number.
- Writes a `.gif` file.

### `ECharts`
- Accepts any pyecharts chart object, SwanLab's wrapped `ECharts`, or a pyecharts table-like object that exposes `dump_options()`.
- Writes a JSON file.
- Use this when the chart is already expressed as pyecharts options.

### `Molecule`
- Accepts SMILES strings, file paths, RDKit `Mol` objects, or another `Molecule`.
- RDKit is required for molecule conversion.
- Path inputs are expected to resolve to `.pdb`, `.sdf`, or `.mol` files.
- Writes a `.pdb` file.

### `Object3D`
- Accepts NumPy arrays, dictionaries with `points`, file paths, or another `Object3D`.
- Array points must be `(N, 3)`, `(N, 4)`, or `(N, 6)`.
- File inputs support `.glb` and `.swanlab.pts.json`.
- Writes either `.swanlab.pts.json` or `.glb`.

## Practical routing hints

- Use `Text` for short generated text and `Html` for rendered pages or snippets.
- Use `Image`, `Audio`, `Video`, `Molecule`, or `Object3D` only when the data is truly rich media.
- Use `ECharts` when the user already has a pyecharts object or a `dump_options()` provider.
- Route scalar-only logging back to `experiment-tracking`.
- Route framework-produced media back to `integrations-and-plugins`.
