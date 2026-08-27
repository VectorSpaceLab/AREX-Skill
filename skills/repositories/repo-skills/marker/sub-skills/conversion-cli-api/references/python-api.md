# Python API

Use the Python API when a caller needs to embed Marker conversion, inspect rendered objects before saving, choose converters dynamically, or integrate with an existing pipeline.

## Core imports and signatures

Live inspection verified these public signatures:

| Object | Signature or role |
| --- | --- |
| `ConfigParser` | `ConfigParser(cli_options: dict)` |
| `PdfConverter` | `PdfConverter(artifact_dict, processor_list=None, renderer=None, llm_service=None, config=None)` |
| `TableConverter` | Same constructor shape as `PdfConverter` |
| `OCRConverter` | Accepts the same arguments through `*args, **kwargs`; forces OCR and uses OCR JSON output |
| `text_from_rendered` | Converts a rendered Pydantic output into `(text, extension, images)` |
| `save_output` | Writes main text, metadata JSON, and extracted images |
| `json_to_html` | Reconstructs nested HTML from a JSON block with `content-ref` children |

## Basic PDF conversion

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("input.pdf")
text, extension, images = text_from_rendered(rendered)
print(extension)
print(text[:500])
```

`create_model_dict()` loads Marker model weights and can download or initialize them. Do not call it in import-time code or smoke tests.

## ConfigParser pattern

`ConfigParser` makes Python behavior match CLI options. Provide option names as dictionary keys; use strings for CLI-like options such as `page_range`.

```python
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import save_output, text_from_rendered

options = {
    "output_format": "json",
    "page_range": "0,5-10",
    "disable_image_extraction": True,
    "disable_multiprocessing": True,
}
config_parser = ConfigParser(options)
converter = PdfConverter(
    artifact_dict=create_model_dict(),
    config=config_parser.generate_config_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service(),
)
rendered = converter("input.pdf")
text, extension, images = text_from_rendered(rendered)
save_output(rendered, "output/input", "input")
```

Important transformations:

- `page_range="0,5-10"` becomes a list of page indices.
- `disable_image_extraction=True` becomes `extract_images=False`.
- `disable_multiprocessing=True` becomes `pdftext_workers=1`.
- `debug=True` enables debug images, layout images, debug JSON, and a debug data folder.
- `output_format` selects Markdown, JSON, HTML, or chunks renderer.

## Converter choices

### Full document conversion

```python
from marker.converters.pdf import PdfConverter

converter_cls = PdfConverter
```

Use `PdfConverter` for regular PDF/image/document conversion into Markdown, JSON, HTML, or chunks. For non-PDF document types, install `marker-pdf[full]` before conversion.

### Table-only conversion

```python
from marker.config.parser import ConfigParser
from marker.converters.table import TableConverter
from marker.models import create_model_dict

options = {"output_format": "json", "force_layout_block": "Table"}
config_parser = ConfigParser(options)
converter = TableConverter(
    artifact_dict=create_model_dict(),
    config=config_parser.generate_config_dict(),
    renderer=config_parser.get_renderer(),
)
rendered = converter("input.pdf")
```

Use JSON output when the caller needs table cell structure or bounding boxes. Keep LLM table cleanup routed to `../llm-extraction-services/`.

### OCR-only conversion

```python
from marker.config.parser import ConfigParser
from marker.converters.ocr import OCRConverter
from marker.models import create_model_dict

options = {"page_range": "0", "keep_chars": True}
config_parser = ConfigParser(options)
converter = OCRConverter(
    artifact_dict=create_model_dict(),
    config=config_parser.generate_config_dict(),
)
rendered = converter("input.pdf")
```

`OCRConverter` sets `force_ocr=True` internally and returns OCR JSON output. `keep_chars` requests character-level boxes where supported.

## Saving and parsing outputs

`text_from_rendered(rendered)` returns different extensions based on the renderer:

| Renderer output | Extension | Images |
| --- | --- | --- |
| Markdown | `md` | Extracted images keyed by filename unless disabled |
| HTML | `html` | Extracted images keyed by filename unless disabled |
| JSON | `json` | Empty image map in the text tuple; images may be base64 inside JSON blocks |
| Chunks | `json` | Empty image map in the text tuple |
| OCR JSON | `json` | Empty image map in the text tuple |

`save_output(rendered, output_dir, fname_base)` writes:

- `{fname_base}.{md|html|json}` for main content.
- `{fname_base}_meta.json` for metadata.
- Extracted image files for Markdown/HTML outputs when image extraction is enabled.

Create `output_dir` before direct `save_output` calls. The CLI creates a basename subfolder automatically through `ConfigParser.get_output_folder()`.

## Bytes input

`PdfConverter` accepts a file path or an `io.BytesIO` input for PDF data. Table and OCR converters are typically used with file paths.

```python
import io
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

with open("input.pdf", "rb") as source:
    payload = io.BytesIO(source.read())
rendered = PdfConverter(artifact_dict=create_model_dict())(payload)
```

## Avoid accidental expensive runs

- Keep `create_model_dict()` inside a function or `if __name__ == "__main__"` block.
- Validate input paths and output directories before constructing converters.
- Use `marker_cli_smoke.py` for help-only CLI checks.
- Use `marker_conversion_skeleton.py --help` to inspect a guarded conversion template.
- Do not embed credentials, private cache paths, or local environment paths in reusable examples.
