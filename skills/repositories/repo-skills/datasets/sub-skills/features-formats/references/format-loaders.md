# Format Loaders and Decodable Features

This reference helps choose between file-format builders, folder-based builders, and decodable feature types. It does not replace the general loading sub-skill; use `../../loading-local-hub/SKILL.md` for split patterns, Hub paths, local paths, archives, authentication, and streaming mechanics.

## Loader Selection

| Data shape | Typical call | Feature concern |
| --- | --- | --- |
| CSV/TSV tables | `load_dataset("csv", data_files=..., sep=...)` | Pass `features=` for label columns, nullable columns, or dtype control. |
| JSON lines or JSON arrays | `load_dataset("json", data_files=..., field=...)` | Use `features=` or `Json()` for mixed/nested values; `field` selects a nested top-level array/object. |
| Parquet/Arrow | `load_dataset("parquet", ...)` or `load_dataset("arrow", ...)` | Often carries schema already; use `columns=` or `features=` when selecting/casting. |
| Text files | `load_dataset("text", data_files=...)` | Produces text rows; cast/add labels later if needed. |
| Pandas/Spark/SQL/generator | Builder-specific IO entry points | Define `Features` when inferred Arrow dtypes are not stable enough. |
| HDF5 | `load_dataset("hdf5", data_files=...)` | Multi-dimensional arrays may infer `ArrayXD`; variable-length arrays become `List`; complex/compound values become nested records. |
| WebDataset tar shards | `load_dataset("webdataset", data_files=...)` | Extension-based sample decoding is constrained for safety; inspect inferred feature keys. |
| Time-series `.ts` files | `load_dataset("tsfile", data_files=...)` | Check inferred sequence/list dtypes and class labels. |
| Folder of media files | `load_dataset("imagefolder"/"audiofolder"/"videofolder"/"pdffolder"/"niftifolder"/"meshfolder", data_dir=...)` | Folder names can infer labels; metadata files add columns and can override caption/annotation structures. |

If format inference chooses the wrong builder, pass the builder name explicitly. If a file extension is ambiguous, specify `data_files`, `features`, and relevant loader kwargs rather than relying on auto-detection.

## Decodable Feature Constructors

The verified package exposes these constructor shapes:

| Feature | Constructor | Decodes to | Optional dependency guidance |
| --- | --- | --- | --- |
| `Audio` | `Audio(sampling_rate=None, decode=True, num_channels=None, stream_index=None)` | `torchcodec.decoders.AudioDecoder` wrapper when decoded | Requires `torchcodec` and `torch`; FFmpeg support comes through torchcodec. Use `decode=False` in minimal environments. |
| `Image` | `Image(mode=None, decode=True)` | `PIL.Image.Image` when decoded | Requires Pillow. The vision extra includes Pillow; use `mode="RGB"` or another PIL mode when normalized image mode matters. |
| `Video` | `Video(decode=True, stream_index=None, dimension_order="NCHW", num_ffmpeg_threads=1, device="cpu", seek_mode="exact")` | `torchcodec.decoders.VideoDecoder` when decoded | Requires `torchcodec` and `torch`. Vision/video environments need those installed; choose `decode=False` for metadata-only validation. |
| `Pdf` | `Pdf(decode=True)` | `pdfplumber.pdf.PDF` when decoded | Requires `pdfplumber`; PDF support is experimental. |
| `Nifti` | `Nifti(decode=True)` | `nibabel.nifti1.Nifti1Image`-like object when decoded | Requires `nibabel`; visualization may use `ipyniivue` but basic decoding depends on nibabel. |
| `Mesh` | `Mesh(decode=True)` | `trimesh.Trimesh` or `trimesh.Scene` when decoded | Requires `trimesh`; supported common file types include `.glb`, `.ply`, and `.stl`. |

Do not assume optional dependencies are installed. Use feature constructors with `decode=False` to create, inspect, upload, or validate datasets without importing decoder libraries.

## Path/Bytes Casting Pattern

```python
from datasets import Dataset, Image, Audio, Video, Pdf, Nifti, Mesh

ds = Dataset.from_dict({
    "image": ["image.jpg"],
    "audio": ["audio.wav"],
    "video": ["clip.mp4"],
    "pdf": ["paper.pdf"],
    "scan": ["scan.nii.gz"],
    "mesh": ["model.glb"],
})

ds = ds.cast_column("image", Image(decode=False))
ds = ds.cast_column("audio", Audio(sampling_rate=16_000, decode=False))
ds = ds.cast_column("video", Video(decode=False))
ds = ds.cast_column("pdf", Pdf(decode=False))
ds = ds.cast_column("scan", Nifti(decode=False))
ds = ds.cast_column("mesh", Mesh(decode=False))
```

Accessing rows with `decode=False` returns path/bytes-like structures instead of decoded objects. To decode later, recast the column with the same feature and `decode=True` after installing dependencies.

## Folder Builders

Folder builders are no-code packaged modules for large local or Hub datasets:

- `imagefolder`: image files with optional `metadata.csv`, `metadata.jsonl`, or class folders.
- `audiofolder`: audio files with optional metadata/transcriptions or class folders.
- `videofolder`: video files with optional captions/metadata or class folders.
- `pdffolder`: PDF files with optional metadata or class folders.
- `niftifolder`: NIfTI files, including archive workflows, with optional metadata.
- `meshfolder`: `.glb`, `.ply`, `.stl` mesh files with optional metadata/captions or class folders.

Common behavior:

- Without metadata, directory names can infer a `label` column as `ClassLabel`.
- With metadata, the metadata file must reference media paths using the expected file-name column for that builder; relative paths must match the folder/archive layout.
- `drop_labels` style options may be available in folder configs when labels should not be inferred.
- Archives can be used, but metadata paths must match the paths inside the archive, not arbitrary local paths.

Route questions about split pattern hierarchy and `data_files` globbing to `../../loading-local-hub/SKILL.md`.

## Tabular and Semi-Structured Formats

For CSV/JSON/text-like files, schema bugs usually come from type inference:

```python
from datasets import load_dataset, Features, Value, ClassLabel, List, Json

features = Features({
    "id": Value("string"),
    "label": ClassLabel(names=["entailment", "neutral", "contradiction"]),
    "tokens": List(Value("string")),
    "raw_payload": Json(),
})
ds = load_dataset("json", data_files="train.jsonl", split="train", features=features)
```

Use `Json()` when a column stores arbitrary object payloads. Use a precise nested `Features` structure when the intended record shape should be enforced.

## Multimodal Minimal-Environment Plan

When the user lacks optional decoder dependencies:

1. Load or create path/bytes columns.
2. Cast media columns with `decode=False`.
3. Validate `ds.features`, row counts, split names, labels, and path/bytes structures.
4. Record which extra is needed for actual decoding: audio/video need `torchcodec` and `torch`; images need Pillow; PDFs need `pdfplumber`; NIfTI needs `nibabel`; meshes need `trimesh`.
5. Only enable `decode=True` once the runtime environment includes the required dependency and the task genuinely needs decoded objects.

## Format Ownership Boundaries

- Loading mechanics, split names, `data_dir`, `data_files`, archives, streaming, and Hub/local repository selection belong in `../../loading-local-hub/SKILL.md`.
- Post-load transforms, model preprocessing, output formatting with `with_format`, and streaming iteration performance belong in `../../processing-streaming/SKILL.md`.
- Dataset card examples, upload/push layout, cache cleanup, and `datasets-cli` usage belong in `../../sharing-cli-cache/SKILL.md`.
