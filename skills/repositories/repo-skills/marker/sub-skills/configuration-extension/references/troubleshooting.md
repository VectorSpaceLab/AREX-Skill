# Configuration And Extension Troubleshooting

Use this matrix to debug Marker configuration and extension failures before running expensive conversions.

## Invalid JSON

Symptoms:

- `json.JSONDecodeError` while reading `config_json`.
- Config inspection fails before class-path checks.

Checks:

- Confirm the file is JSON, not Python syntax.
- Use double quotes for strings and keys.
- Ensure the top-level value is an object.
- Validate inline JSON separately when shell quoting is complex.

Recovery:

```bash
python -m json.tool config.json
python skills/marker/sub-skills/configuration-extension/scripts/inspect_marker_config.py --config-json config.json
```

## Falsey Options Are Dropped

Symptoms:

- `False`, `0`, or empty-string overrides do not appear in generated config.
- A direct CLI option appears ignored.

Cause:

- `ConfigParser.generate_config_dict()` skips falsey option values before applying transformations.

Recovery:

- Use supported positive flags such as `disable_image_extraction` when available.
- Pass a direct Python config dictionary when you must preserve `False` or `0`.
- Inspect generated config before conversion.

## Full Module Path Mistakes

Symptoms:

- `ValueError: not enough values to unpack` from class loading.
- `ModuleNotFoundError` or `AttributeError` for a processor/converter/renderer.

Checks:

- Use `package.module.ClassName`, not `ClassName`.
- Ensure the package containing the custom class is installed or on `PYTHONPATH`.
- Ensure the class name is exported in the module exactly as written.

Recovery:

```bash
python skills/marker/sub-skills/configuration-extension/scripts/custom_processor_template.py \
  --validate-class-path mypackage.processors.MyProcessor
```

For non-processor classes, use `inspect_marker_config.py` with the appropriate option and read the import error.

## Invalid Processor Imports

Symptoms:

- `Error loading processor` in logs.
- Config inspection fails on `get_processors()`.
- Conversion fails after replacing the default processor list.

Checks:

- The path imports.
- The class subclasses or behaves like `marker.processors.BaseProcessor`.
- The constructor accepts `config=None` or only dependencies Marker can resolve.
- The custom list includes every processor needed; `--processors` replaces defaults.

Recovery:

- Validate one processor path at a time.
- Start from the default processor sequence in `extension-points.md` and remove only what is intentional.
- Avoid LLM processors unless `use_llm` and an LLM service are configured; route service details to `../llm-extraction-services/`.

## Invalid Converter Imports

Symptoms:

- `Error loading converter` in logs.
- `get_converter_cls()` raises import errors.
- Converter initializes but cannot resolve dependencies.

Checks:

- Use known public paths when possible: `marker.converters.pdf.PdfConverter`, `marker.converters.table.TableConverter`, `marker.converters.ocr.OCRConverter`, or `marker.converters.extraction.ExtractionConverter`.
- Preserve constructor compatibility for custom converters.
- Keep required constructor parameters resolvable by `resolve_dependencies()` or provide defaults.

Recovery:

- Inspect `converter_class_path` with `inspect_marker_config.py` before conversion.
- If only processor order changes, prefer a processor list or converter subclass with a changed `default_processors` tuple.

## Invalid Renderer Or Output Mismatch

Symptoms:

- `Invalid output format` from `get_renderer()`.
- `text_from_rendered()` raises `Invalid output type`.
- Saved file extension does not match expected custom output.

Checks:

- Built-in `output_format` choices are `markdown`, `json`, `html`, and `chunks`.
- A custom renderer class path passed directly to a converter must return a model the caller knows how to serialize.
- Built-in `save_output()` only handles built-in output classes.

Recovery:

- Use built-in renderer paths when possible.
- For custom renderers, write a small serializer wrapper or consume the returned model directly.
- For RAG-friendly flat records, use `chunks` rather than custom JSON unless schema requirements differ.

## Debug Output Folder Surprises

Symptoms:

- Debug files are not where expected.
- Metadata contains a `debug_data_path` under a nested document folder.
- Debug is enabled but no files appear.

Checks:

- `debug=True` sets `debug_data_folder` to `output_dir`.
- `DebugProcessor` appends the document base name.
- Custom processor lists must include `marker.processors.debug.DebugProcessor` if debug artifacts are expected.
- The process must have write permission to the output/debug directory.

Recovery:

- Inspect generated config for `debug_*` keys.
- Use an explicit `output_dir`.
- Include `DebugProcessor` at the end of a custom processor sequence.

## Provider Unsupported Extension Or Misdetected File

Symptoms:

- A non-PDF file falls through to PDF behavior.
- Provider fails to read the source file.
- HTML-like text is not detected as HTML.

Checks:

- Built-in provider detection covers images, PDF, EPUB, DOCX, XLSX, PPTX, and HTML.
- Detection uses file signatures first and extension fallback later.
- Unknown extensions can fall back to `PdfProvider`.

Recovery:

- Confirm the file has a supported extension and valid file signature.
- Install optional extras for non-PDF document formats when needed.
- If adding a new input format, implement a provider rather than patching a processor.

## Custom Class Dependencies

Symptoms:

- Import succeeds locally but fails in another agent/runtime.
- `Cannot resolve dependency for parameter` during converter initialization.
- Model downloads or network calls happen unexpectedly during import/initialization.

Checks:

- Keep custom classes in an installed package or project path available to the runtime.
- Avoid required constructor parameters beyond `config` and known artifact keys.
- Avoid side effects at import time.
- Keep model/API calls out of constructors unless explicitly documented and optional.

Recovery:

- Move expensive work to `__call__` and gate it behind config.
- Add constructor defaults.
- Validate imports in a fresh shell before conversion.

## Schema Or Block Output Confusion

Symptoms:

- JSON output contains `content-ref` placeholders.
- Child blocks are nested unexpectedly.
- Chunks output does not match JSON tree shape.

Checks:

- JSON is hierarchical and may need `json_to_html(block)` for full child HTML.
- Chunks are flattened top-level blocks with child HTML assembled.
- `section_hierarchy`, geometry, and images differ by renderer and block type.

Recovery:

- Choose `json` for full tree inspection.
- Choose `chunks` for RAG-style flat records.
- Inspect `metadata.page_stats` and debug artifacts before changing processors.

## Combined Complex Configuration

For combinations like `config_json` + `chunks` + `debug` + custom processors + `TableConverter`:

1. Run `inspect_marker_config.py` with the same options.
2. Confirm `generated_config` includes expected debug and output keys.
3. Confirm `renderer` is `marker.renderers.chunk.ChunkRenderer`.
4. Confirm `converter_class_path` is `marker.converters.table.TableConverter`.
5. Confirm every processor imports.
6. Remember that the custom processor list replaces the converter default list.
7. Route actual conversion command construction to `../conversion-cli-api/` if needed.
