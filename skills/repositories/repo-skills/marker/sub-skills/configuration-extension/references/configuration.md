# Configuration Reference

Marker exposes most runtime customization through `marker.config.parser.ConfigParser` plus dynamically generated Click options. Use this reference to explain how CLI-style options become converter arguments without depending on the source checkout.

## ConfigParser Contract

Import path and signature:

```python
from marker.config.parser import ConfigParser

config_parser = ConfigParser(cli_options: dict)
```

Common downstream calls:

```python
converter_cls = config_parser.get_converter_cls()
config = config_parser.generate_config_dict()
processors = config_parser.get_processors()
renderer = config_parser.get_renderer()
llm_service = config_parser.get_llm_service()
```

`PdfConverter` accepts these values as:

```python
PdfConverter(
    artifact_dict=artifact_dict,
    processor_list=processors,
    renderer=renderer,
    llm_service=llm_service,
    config=config,
)
```

`TableConverter`, `OCRConverter`, and `ExtractionConverter` follow the same broad configuration pattern where their constructors accept conversion artifacts and a config dictionary. Route basic conversion examples to `../conversion-cli-api/`; route LLM service specifics to `../llm-extraction-services/`.

## Generated Common Options

`ConfigParser.common_options` adds common CLI flags including:

| Option | Parser effect |
| --- | --- |
| `output_dir` | Used as base output directory and as debug data root when `debug` is enabled. |
| `debug` | Expands to `debug_pdf_images=True`, `debug_layout_images=True`, `debug_json=True`, and `debug_data_folder=<output_dir>`. |
| `output_format` | Selects renderer class path: markdown, json, html, or chunks. |
| `processors` | Comma-separated full module paths; validated by import before being returned. |
| `config_json` | Loads JSON from the given path and merges those keys into the generated config dictionary. |
| `disable_multiprocessing` | Sets `pdftext_workers=1`. |
| `disable_image_extraction` | Sets `extract_images=False`. |
| `page_range` | Converts strings like `0,5-10,20` to sorted integer page lists. |
| `converter_cls` | Imports a converter class from a full module path; defaults to `marker.converters.pdf.PdfConverter`. |
| `llm_service` | Supplies an LLM service import path only when `use_llm` is truthy. |

Generated CLI options from Marker classes are also accepted. They come from annotated attributes on builders, processors, converters, providers, renderers, services, and extractors. Shared attributes use `--attribute`; class-specific overrides use `--ClassName_attribute`, such as `--MarkdownRenderer_html_tables_in_markdown` if exposed by the installed version.

## Falsey Value Rule

`generate_config_dict()` skips any falsey option value before matching options. This means these values are dropped rather than passed through:

- `False`
- `None`
- `0`
- empty strings
- empty containers

Practical consequences:

- Boolean flags are only represented when enabled.
- You cannot force a config key to `False` or `0` through `ConfigParser.generate_config_dict()` unless the installed Marker version changes this behavior.
- `--disable_image_extraction` works because the flag itself is truthy when provided and is transformed to `extract_images=False`.
- `--disable_multiprocessing` works because the flag is transformed to `pdftext_workers=1`.
- Direct Python API calls can pass an explicit `config` dictionary when a falsey override must reach a class.

## config_json Merge Behavior

`config_json` is a path to a JSON object. Marker reads the file and updates the generated config dictionary with its keys.

Safe example file:

```json
{
  "paginate_output": true,
  "add_block_ids": true,
  "extract_images": false,
  "page_range": [0, 1, 2]
}
```

Notes:

- The JSON must be valid JSON, not Python literals.
- File values are merged at the point `config_json` is processed while iterating over input options.
- If the same key is set by both JSON and a later non-falsey CLI option, the later option can overwrite it depending on input dictionary order.
- For deterministic Python usage, build a final dictionary explicitly or inspect it with [`../scripts/inspect_marker_config.py`](../scripts/inspect_marker_config.py).

## Class Paths And Import Helpers

Marker uses full module paths for custom classes. Internally:

- `classes_to_strings([MarkdownRenderer])` returns `marker.renderers.markdown.MarkdownRenderer`.
- `strings_to_classes(["marker.renderers.markdown.MarkdownRenderer"])` imports the class.

Use full paths for:

- `--processors "package.module.MyProcessor,package.module.OtherProcessor"`
- `--converter_cls package.module.MyConverter`
- `--llm_service package.module.MyService` when routed to LLM tasks
- Python constructor `renderer="package.module.MyRenderer"`

Common mistakes:

- Passing only `MyProcessor` without a module path.
- Passing a module path with no class name.
- Importing a class whose dependencies are not installed.
- Providing a processor path that imports but does not follow the processor contract.

## Renderer Selection

`get_renderer()` maps output format to a renderer class path:

| `output_format` | Renderer |
| --- | --- |
| `markdown` | `marker.renderers.markdown.MarkdownRenderer` |
| `json` | `marker.renderers.json.JSONRenderer` |
| `html` | `marker.renderers.html.HTMLRenderer` |
| `chunks` | `marker.renderers.chunk.ChunkRenderer` |

The renderer controls the shape of the rendered Pydantic output. Use `marker.output.text_from_rendered(rendered)` or `marker.output.save_output(rendered, output_dir, fname_base)` for built-in output classes.

## Converter Class Selection

`get_converter_cls()` returns:

- The imported class from `converter_cls`, if supplied.
- `marker.converters.pdf.PdfConverter` by default.

Common public converter paths:

- `marker.converters.pdf.PdfConverter`: whole-document conversion.
- `marker.converters.table.TableConverter`: table/form-focused conversion.
- `marker.converters.ocr.OCRConverter`: OCR-focused conversion.
- `marker.converters.extraction.ExtractionConverter`: structured extraction; route service/schema specifics to `../llm-extraction-services/`.

## Processor List Selection

`get_processors()` returns either:

- `None`, which lets the converter use its `default_processors`.
- A list of full module path strings supplied by `processors`.

Supplying a custom list replaces the converter default list; it does not append. If a user wants “default processors plus one extra,” tell them to explicitly list every processor they want or create a converter subclass that changes `default_processors`.

## LLM Service Selection Boundary

`get_llm_service()` returns `None` unless `use_llm` is truthy. When `use_llm` is enabled:

- It returns `llm_service` if supplied.
- It returns `marker.services.gemini.GoogleGeminiService` by default.

Do not include credentials or backend-specific examples here. Route those tasks to `../llm-extraction-services/`.

## Safe Inspection Workflow

Use [`../scripts/inspect_marker_config.py`](../scripts/inspect_marker_config.py) to show downstream parser values without opening input files or running conversion:

```bash
python skills/marker/sub-skills/configuration-extension/scripts/inspect_marker_config.py \
  --inline-json '{"output_format":"chunks","debug":true,"output_dir":"out","processors":"mypkg.proc.MyProcessor","converter_cls":"marker.converters.table.TableConverter"}'
```

Expected categories in the output:

- generated config keys and values
- renderer class path
- processor class paths or import errors
- converter class path or import errors
- LLM service class path or `null`

Use this before diagnosing complex combinations such as chunks output, debug artifacts, custom processors, and table conversion.
