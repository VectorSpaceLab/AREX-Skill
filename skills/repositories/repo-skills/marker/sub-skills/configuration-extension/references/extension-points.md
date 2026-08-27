# Extension Points Reference

Marker’s end-to-end pipeline is a converter that chooses a provider, runs builders, applies processors, and renders the resulting document schema. Use this reference to choose the smallest safe extension point.

## Pipeline Anatomy

For `PdfConverter`, the public flow is:

1. `provider_from_filepath(filepath)` chooses a provider class for the input file.
2. `DocumentBuilder`, `LayoutBuilder`, `LineBuilder`, and `OcrBuilder` construct a `Document` with pages, lines, blocks, and OCR/layout data.
3. `StructureBuilder` groups and orders the document structure.
4. Each processor mutates or enriches the `Document`.
5. The renderer converts the `Document` to a Pydantic output model.

A simplified Python shape:

```python
provider_cls = provider_from_filepath(filepath)
provider = provider_cls(filepath, config)
document = DocumentBuilder(config)(provider, layout_builder, line_builder, ocr_builder)
StructureBuilder(config)(document)
for processor in processor_list:
    processor(document)
rendered = renderer(document)
```

`BaseConverter.resolve_dependencies()` creates classes by inspecting constructor parameters. It passes `config`, any matching key from `artifact_dict`, or a constructor default. Missing unresolved parameters raise an error. Custom classes should keep constructor dependencies simple and compatible with this resolver.

## Ownership Map

| Need | Extension point | Why |
| --- | --- | --- |
| Support a new input format or file sniffing behavior | Provider plus registry/converter integration | Providers expose page images, text lines, references, and page boxes from a source file. |
| Change initial document/page/block construction | Builder | Builders create the initial `Document`, layout, lines, OCR, and structure. |
| Modify, relabel, merge, filter, or enrich blocks after initial construction | Processor | Processors operate on the `Document` and are easiest to swap with `--processors`. |
| Change markdown/html/json/chunks shape or add a new output format | Renderer | Renderers own output model fields, image extraction, metadata, and serialization shape. |
| Change the whole pipeline or default processor sequence | Converter subclass | Converters orchestrate providers, builders, processors, renderers, and LLM service injection. |
| Change block classes for existing block types | Converter `override_map` or schema registry | `PdfConverter` registers override block classes before processing. |

## Default PdfConverter Processor Sequence

The default whole-document processor sequence is:

1. `marker.processors.order.OrderProcessor`
2. `marker.processors.block_relabel.BlockRelabelProcessor`
3. `marker.processors.line_merge.LineMergeProcessor`
4. `marker.processors.blockquote.BlockquoteProcessor`
5. `marker.processors.code.CodeProcessor`
6. `marker.processors.document_toc.DocumentTOCProcessor`
7. `marker.processors.equation.EquationProcessor`
8. `marker.processors.footnote.FootnoteProcessor`
9. `marker.processors.ignoretext.IgnoreTextProcessor`
10. `marker.processors.line_numbers.LineNumbersProcessor`
11. `marker.processors.list.ListProcessor`
12. `marker.processors.page_header.PageHeaderProcessor`
13. `marker.processors.sectionheader.SectionHeaderProcessor`
14. `marker.processors.table.TableProcessor`
15. `marker.processors.llm.llm_table.LLMTableProcessor`
16. `marker.processors.llm.llm_table_merge.LLMTableMergeProcessor`
17. `marker.processors.llm.llm_form.LLMFormProcessor`
18. `marker.processors.text.TextProcessor`
19. `marker.processors.llm.llm_complex.LLMComplexRegionProcessor`
20. `marker.processors.llm.llm_image_description.LLMImageDescriptionProcessor`
21. `marker.processors.llm.llm_equation.LLMEquationProcessor`
22. `marker.processors.llm.llm_handwriting.LLMHandwritingProcessor`
23. `marker.processors.llm.llm_mathblock.LLMMathBlockProcessor`
24. `marker.processors.llm.llm_sectionheader.LLMSectionHeaderProcessor`
25. `marker.processors.llm.llm_page_correction.LLMPageCorrectionProcessor`
26. `marker.processors.reference.ReferenceProcessor`
27. `marker.processors.blank_page.BlankPageProcessor`
28. `marker.processors.debug.DebugProcessor`

Supplying `processor_list` replaces this sequence. LLM simple block processors may be grouped by `BaseConverter.initialize_processors()` into an internal meta-processor so the final instantiated processor list can differ from the class list.

## Processor Contract

A processor should subclass `marker.processors.BaseProcessor` or follow its public contract:

```python
class MyProcessor(BaseProcessor):
    block_types = None

    def __init__(self, config=None):
        super().__init__(config)

    def __call__(self, document):
        return None
```

`BaseProcessor.__init__` applies matching config keys to annotated or existing attributes through Marker’s config assignment helper. A processor should mutate the document in place. Keep side effects explicit and avoid network/model calls unless the processor clearly belongs to an LLM workflow.

Use [`../scripts/custom_processor_template.py`](../scripts/custom_processor_template.py) to generate a local skeleton or validate that a class path imports and subclasses `BaseProcessor`.

## Renderer Contract

A renderer should subclass `marker.renderers.BaseRenderer` or follow its public contract:

```python
class MyRenderer(BaseRenderer):
    def __call__(self, document):
        return MyOutputModel(...)
```

Built-in renderers return Pydantic models:

- `MarkdownRenderer` → `MarkdownOutput(markdown, images, metadata)`
- `HTMLRenderer` → `HTMLOutput(html, images, metadata)`
- `JSONRenderer` → `JSONOutput(children, block_type, metadata)`
- `ChunkRenderer` → `ChunkOutput(blocks, page_info, metadata)`

If a custom renderer returns a new model type, `marker.output.text_from_rendered()` and `save_output()` will not know how to serialize it unless the caller handles it directly or adds a wrapper.

## Provider Contract

A provider should subclass `marker.providers.BaseProvider` or implement compatible methods:

- `__len__()`
- `get_images(idxs, dpi)`
- `get_page_bbox(idx)`
- `get_page_lines(idx)`
- `get_page_refs(idx)`

`provider_from_filepath()` uses file signatures and extensions to select built-in providers for images, PDFs, EPUB, DOCX, XLSX, PPTX, and HTML. Unknown or ambiguous files fall back by extension and then to the PDF provider. If the user needs a new input format, plan provider integration deliberately; do not solve it with a processor unless the input can already become a `Document`.

## Builders

Builders are responsible for initial document construction:

- `DocumentBuilder`: creates pages and calls layout, line, and OCR builders.
- `LayoutBuilder`: adds layout blocks.
- `LineBuilder`: adds text line information.
- `OcrBuilder`: supplies OCR when needed or forced.
- `StructureBuilder`: builds document/page structure.

Choose builders only when the user must change how base document state is created. For most post-processing needs, use processors instead.

## Converter Subclasses

Create or select a converter subclass when the task changes orchestration:

- Use `TableConverter` for table/form-focused extraction; it filters page structure to table/form/TOC block types and uses a shorter processor set.
- Use `OCRConverter` for OCR-focused output.
- Use `ExtractionConverter` for structured extraction; route details to `../llm-extraction-services/`.
- Create a custom converter if the default builders, default processors, renderer default, block override map, or provider selection flow need coordinated changes.

A custom converter should preserve the public constructor shape when possible:

```python
def __init__(self, artifact_dict, processor_list=None, renderer=None, llm_service=None, config=None):
    super().__init__(artifact_dict, processor_list, renderer, llm_service, config)
```

## Schema And Block Overrides

Marker schema classes represent block and group types. `marker.schema.registry.register_block_class(block_type, block_cls)` maps `BlockTypes` enum values to classes. `PdfConverter.override_map` can register override block classes at initialization.

Use schema overrides when the semantics of a block type need a different class. Use processors when block instances only need cleanup, relabeling, grouping, metadata, or text changes.

## Safe Extension Planning Checklist

1. State the target behavior and current built-in owner.
2. Choose one owner: provider, builder, processor, renderer, schema/block, or converter.
3. Keep class paths importable from the runtime environment.
4. Keep constructor dependencies resolvable by `resolve_dependencies()`.
5. Decide whether the custom class replaces defaults or wraps them.
6. Verify with a no-conversion import check before running a document.
7. Inspect renderer output type and serialization path.
8. Route credentials, LLM model behavior, and extraction schemas to `../llm-extraction-services/`.
