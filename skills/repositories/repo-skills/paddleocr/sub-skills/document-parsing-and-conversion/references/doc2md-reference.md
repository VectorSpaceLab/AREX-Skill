# Office Document to Markdown (`doc2md`)

`doc2md` converts office documents to Markdown with optional embedded image extraction.

## Supported formats

The bundled helper `doc2md_supported_formats()` returns the file extensions that the installed environment can handle. In the default package surface, the supported office formats are:

- `.docx`
- `.pptx`
- `.xlsx`

## Python API

```python
from paddleocr import doc2md_convert, doc2md_supported_formats

print(doc2md_supported_formats())
result = doc2md_convert("report.docx")
print(result.markdown)
```

`doc2md_convert()` returns a conversion result that includes:

- `markdown`
- optional document `title`
- `metadata`
- optional `images` mapping from relative path to image bytes

If you pass an output path, the converter writes the Markdown plus any extracted images to disk.

## CLI

The package CLI exposes a dedicated `doc2md` route.

Useful flags:

- `--formats` to print supported formats and exit
- `--input` / `-i` for the source file
- `--output` / `-o` for the Markdown destination
- `--no-drawings` for DOCX/XLSX drawing-layer extraction control
- `--no-headers-footers` for DOCX header/footer control
- `--sheet-name` and `--max-rows` for XLSX selection and trimming

## Optional dependencies

The `doc2md` extra installs the converters that the office-document workflow needs:

- `python-docx`
- `python-pptx`
- `openpyxl`
- `pylatexenc`

If those imports are missing, the converter raises a clear runtime error explaining which optional package is missing.

## Best practices

- Use the helper script or the CLI when you want to confirm supported formats.
- Use the Python API when you want to keep the conversion result in memory or post-process the returned Markdown before writing it to disk.
- Treat unsupported file extensions as a format-selection problem, not as a generic OCR failure.
