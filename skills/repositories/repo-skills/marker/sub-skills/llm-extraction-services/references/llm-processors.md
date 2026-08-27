# LLM Processors

Marker’s default `PdfConverter` processor list includes LLM processors, but their base classes return early unless `use_llm` is true and an `llm_service` is resolved. Most users should enable `--use_llm` instead of manually overriding `--processors`.

## What `--use_llm` improves

| Processor | Class path | Main effect | Useful config |
| --- | --- | --- | --- |
| Table rewriting | `marker.processors.llm.llm_table.LLMTableProcessor` | Rewrites table HTML from table image crops, repairs headers/cells, handles inline math in cells, and skips very large tables. | `max_rows_per_batch`, `max_table_rows`, `max_table_iterations`, `table_image_expansion_ratio` |
| Table merging | `marker.processors.llm.llm_table_merge.LLMTableMergeProcessor` | Decides whether adjacent or cross-page tables should merge and in which direction. | `no_merge_tables_across_pages`, table threshold keys |
| Form rewriting | `marker.processors.llm.llm_form.LLMFormProcessor` | Rewrites form blocks into faithful HTML tables when table cells exist. | `use_llm`; table/form detection must produce cells first |
| Equation cleanup | `marker.processors.llm.llm_equation.LLMEquationProcessor` | Converts equation block images to KaTeX-compatible `<math>` HTML. | `min_equation_height`, `redo_inline_math`, `image_expansion_ratio` |
| Inline math cleanup | `marker.processors.llm.llm_mathblock.LLMMathBlockProcessor` | Rewrites inline math and math-heavy text blocks when `redo_inline_math` is true. | `redo_inline_math`, `inlinemath_min_ratio` |
| Complex regions | `marker.processors.llm.llm_complex.LLMComplexRegionProcessor` | Converts hard blocks to markdown, then HTML. | `use_llm` |
| Image descriptions | `marker.processors.llm.llm_image_description.LLMImageDescriptionProcessor` | Replaces extracted images with text descriptions when image extraction is disabled. | `extract_images=False` via `--disable_image_extraction` |
| Handwriting | `marker.processors.llm.llm_handwriting.LLMHandwritingProcessor` | Generates markdown for handwriting or empty text blocks. | `use_llm` |
| Section headers | `marker.processors.llm.llm_sectionheader.LLMSectionHeaderProcessor` | Adjusts section header levels across the document. | `use_llm` |
| Page correction | `marker.processors.llm.llm_page_correction.LLMPageCorrectionProcessor` | Applies a user prompt to page block order, labels, or HTML. | `block_correction_prompt` |

## When to enable extra flags

- Use `--redo_inline_math` with `--use_llm` when inline math quality matters more than speed/cost. It activates inline math reprocessing beyond large equation blocks.
- Use `--disable_image_extraction` with `--use_llm` when markdown should contain image descriptions instead of saved image files.
- Use `--force_ocr` for garbled digital text; it can improve OCR and math inputs before LLM cleanup.
- Use `--block_correction_prompt` only for focused page-level instructions, such as correcting reading order or block labels. Avoid broad prompts that invite content invention.

## Processor safety expectations

LLM processors send cropped page/block images and prompt text to the configured provider. Confirm privacy requirements before enabling remote Gemini, Vertex, Claude, OpenAI-compatible, or Azure services. Use Ollama only when a local model is acceptable and running. Bundled DisCo scripts do not send images or prompts to any provider.

## Manual processor overrides

Manual `--processors` overrides require full class paths and replace the default processor list. Only override when you intentionally want a reduced or custom pipeline. For class-path import troubleshooting, use `../configuration-extension/`; for ordinary conversion commands, use `../conversion-cli-api/`.
