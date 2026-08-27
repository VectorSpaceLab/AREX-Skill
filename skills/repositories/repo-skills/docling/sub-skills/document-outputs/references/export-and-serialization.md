# Export and Serialization Recipes

Docling represents converted content as a `DoclingDocument`: a Pydantic document model with top-level `texts`, `tables`, `pictures`, `key_value_items`, `groups`, `body`, `furniture`, page/provenance data when available, and JSON-pointer relationships between items. Use these exports when a conversion has already succeeded and the task is to deliver content in another form.

## Common Export Methods

```python
from pathlib import Path
import json
import yaml

from docling_core.types.doc import ImageRefMode

# result is a ConversionResult from DocumentConverter.convert(...)
doc = result.document

markdown = doc.export_to_markdown()
plain_text = doc.export_to_markdown(strict_text=True)
html = doc.export_to_html()
doctags = doc.export_to_doctags()
data = doc.export_to_dict()

Path("out.md").write_text(markdown, encoding="utf-8")
Path("out.txt").write_text(plain_text, encoding="utf-8")
Path("out.html").write_text(html, encoding="utf-8")
Path("out.doctags").write_text(doctags, encoding="utf-8")
Path("out.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
Path("out.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

# Equivalent save helpers are available for persisted outputs.
doc.save_as_markdown(Path("out.md"), image_mode=ImageRefMode.PLACEHOLDER)
doc.save_as_json(Path("out.json"), image_mode=ImageRefMode.PLACEHOLDER)
doc.save_as_yaml(Path("out.yaml"), image_mode=ImageRefMode.PLACEHOLDER)
doc.save_as_html(Path("out.html"), image_mode=ImageRefMode.PLACEHOLDER)
```

Use `export_to_dict()` before `json.dumps(...)` when you need schema-stable machine-readable output. Use `save_as_json(...)` or `save_as_yaml(...)` when image handling and serializer defaults matter.

## CLI Output Formats

The `docling` CLI can write these output families after conversion:

- `md`: Markdown.
- `json`: Docling JSON.
- `yaml`: Docling YAML.
- `html`: normal HTML.
- `html_split_page`: split-page HTML view; layout visualization can be enabled by CLI options.
- `text`: strict text exported through Markdown serialization with placeholder images.
- `doctags`: DocTags serialization.
- `vtt`: WebVTT, mainly useful for audio/transcript-style outputs.
- `doclang`: DocLang XML.

When calling Python directly, mirror these with `save_as_markdown`, `save_as_json`, `save_as_yaml`, `save_as_html`, `save_as_doctags`, `save_as_vtt`, and `export_to_doclang` when those methods are present in the installed `docling-core` version.

## Image Export Modes

Docling uses `ImageRefMode` for Markdown, JSON, YAML, and HTML image handling:

- `ImageRefMode.PLACEHOLDER`: emit placeholders instead of image payloads or references. This is safest for text-only or small JSON outputs.
- `ImageRefMode.EMBEDDED`: embed image data in the serialized output. This is portable but can make Markdown/HTML/JSON large.
- `ImageRefMode.REFERENCED`: write references to external image files. This is best for website-style output, but only works if image files are written and shipped with the document.

Images are only available if conversion preserved them. For PDF page, picture, and table images, configure PDF pipeline options during conversion, then export afterward:

```python
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
result = converter.convert("input.pdf")
doc = result.document

out_dir = Path("output")
out_dir.mkdir(parents=True, exist_ok=True)

for page_no, page in doc.pages.items():
    with (out_dir / f"page-{page_no}.png").open("wb") as file:
        page.image.pil_image.save(file, format="PNG")

picture_index = 0
table_index = 0
for element, _level in doc.iterate_items():
    if isinstance(element, PictureItem):
        picture_index += 1
        element.get_image(doc).save(out_dir / f"picture-{picture_index}.png", "PNG")
    elif isinstance(element, TableItem):
        table_index += 1
        element.get_image(doc).save(out_dir / f"table-{table_index}.png", "PNG")

doc.save_as_markdown(out_dir / "with-images.md", image_mode=ImageRefMode.EMBEDDED)
doc.save_as_markdown(out_dir / "with-image-refs.md", image_mode=ImageRefMode.REFERENCED)
doc.save_as_html(out_dir / "with-image-refs.html", image_mode=ImageRefMode.REFERENCED)
```

## Tables

For Python workflows, each `TableItem` can be exported through a dataframe and HTML/Markdown serializers:

```python
from pathlib import Path

out_dir = Path("tables")
out_dir.mkdir(parents=True, exist_ok=True)

for table_index, table in enumerate(result.document.tables, start=1):
    dataframe = table.export_to_dataframe(doc=result.document)
    dataframe.to_csv(out_dir / f"table-{table_index}.csv", index=False)
    (out_dir / f"table-{table_index}.html").write_text(
        table.export_to_html(doc=result.document), encoding="utf-8"
    )
    (out_dir / f"table-{table_index}.md").write_text(
        dataframe.to_markdown(index=False), encoding="utf-8"
    )
```

If you only have exported Docling JSON and not the original source, use `scripts/export_tables_from_doc.py`. It first attempts to validate the JSON as a `DoclingDocument` and use `TableItem.export_to_dataframe(doc=doc)`; if that is unavailable, it scans raw JSON table structures and writes best-effort summaries and CSV-like files.

## Serialization Strategy

For advanced formatting, Docling exposes serializer classes in `docling-core`, including Markdown, HTML, DocTags, and lower-level serializers for text, tables, pictures, lists, and inline content. The public `DoclingDocument` methods are shorthands over those serializers and should be the default for most agents. Reach for serializer classes only when you need custom table/picture/list formatting beyond the shorthand arguments.

## Choosing Outputs

- Choose Markdown for LLM prompts, human review, and lightweight RAG pre-processing.
- Choose strict text when non-textual structure is not needed and downstream tools dislike Markdown syntax.
- Choose JSON/dict/YAML when preserving document hierarchy, tables, pictures, provenance, and schema fields matters.
- Choose HTML or split-page HTML for visual review and web rendering.
- Choose DocTags or DocLang when a downstream Docling-aware model/tool expects those formats.
- Choose WebVTT for timestamped transcript-style media outputs.
