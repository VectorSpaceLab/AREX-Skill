# PageIndex API Reference

These facts were verified by live import/signature inspection of the source package with its runtime dependencies installed.

## Import surfaces

The top-level `pageindex` package re-exports the classic PDF pipeline, Markdown conversion, retrieval helpers, `PageIndexClient`, and `optimize_tree`. Flash extraction is imported from `pageindex.flash`.

```python
from pageindex import page_index, md_to_tree, PageIndexClient, optimize_tree
from pageindex import get_document, get_document_structure, get_page_content
from pageindex.flash import page_index_flash
```

## Classic PDF tree extraction

| API | Signature | Use |
| --- | --- | --- |
| `page_index` | `(doc, model=None, toc_check_page_num=None, max_page_num_each_node=None, max_token_num_each_node=None, if_add_node_id=None, if_add_node_summary=None, if_add_doc_description=None, if_add_node_text=None)` | Public PDF tree builder. `doc` is a PDF path or `BytesIO`. Keyword arguments override config defaults. |
| `page_index_main` | `(doc, opt=None)` | Lower-level entry point when you already built a `ConfigLoader` option object. |

The classic pipeline reads PDF text, detects/repairs TOC entries, validates physical page markers, recursively splits large nodes, applies a deterministic merge pass, optionally adds node text, summaries, and document descriptions, and returns a dict with `doc_name` and `structure`.

## Markdown tree extraction

| API | Signature | Use |
| --- | --- | --- |
| `md_to_tree` | `(md_path, if_thinning=False, min_token_threshold=None, if_add_node_summary='no', summary_token_threshold=None, model=None, if_add_doc_description='no', if_add_node_text='no', if_add_node_id='yes')` | Async Markdown converter. Use `asyncio.run(md_to_tree(...))` from synchronous code. |

Markdown headings come from ATX headings (`#`, `##`, etc.) and non-empty bold-only lines. Code-block headings are ignored. When summaries are disabled, this path can be exercised without an LLM key.

## PageIndex Flash

| API | Signature | Use |
| --- | --- | --- |
| `page_index_flash` | `(pdf, summary=True, summary_model=None, optimize=False, optimize_expand=True, optimize_model=None, summary_concurrency=None, use_embedded_toc=True) -> dict` | Fast PDF structure extraction from layout statistics. Accepts a PDF path or `BytesIO`. |

`summary=False` returns the structure without LLM calls. `optimize=True, optimize_expand=False` runs the deterministic merge-only optimizer. `optimize_expand=True` uses an LLM to propose additional subsections. `use_embedded_toc=True` lets Flash consume trusted PDF bookmarks and returns a `toc_source` signal when applicable.

## Tree optimization

| API | Signature | Use |
| --- | --- | --- |
| `optimize_tree` | `(doc, pdf_path=None, model=None, do_expand=None, **kwargs)` | Synchronous helper over a loaded structure dict or structure JSON path. Mutates `doc['structure']` and returns metrics/log summary. |
| `optimize` | `(structure, pages, lines, model=None, routing=1, trigger_pages=5, min_gain_ratio=0.0, do_merge=True, do_expand=True, max_rounds=3, page_count=None, cache=None, kinds=('section', 'table'), empty_retries=1, do_relabel=True, progress=False)` | Async lower-level optimizer. Use only when you already have per-page text and line lists. |

Merge-only optimization is deterministic and CPU-only. Expand needs page text plus an LLM model and API key when the model uses OpenAI-compatible credentials.

## Retrieval client and low-level tools

| API | Signature | Use |
| --- | --- | --- |
| `PageIndexClient` | `(api_key: str = None, model: str = None, retrieve_model: str = None, workspace: str = None)` | Client for indexing files and retrieving metadata, structure, and page content. |
| `PageIndexClient.index` | `(self, file_path: str, mode: str = 'auto') -> str` | Index a PDF or Markdown file, store it in memory or workspace, and return a document id. |
| `PageIndexClient.get_document` | `(self, doc_id: str) -> str` | Return JSON metadata for one document. |
| `PageIndexClient.get_document_structure` | `(self, doc_id: str) -> str` | Return structure JSON with text fields removed. |
| `PageIndexClient.get_page_content` | `(self, doc_id: str, pages: str) -> str` | Return page or line content for ranges such as `"5-7"`, `"3,8"`, or `"12"`. |
| `get_document` | `(documents: dict, doc_id: str) -> str` | Low-level retrieval helper over an existing `documents` dict. |
| `get_document_structure` | `(documents: dict, doc_id: str) -> str` | Low-level structure helper over an existing `documents` dict. |
| `get_page_content` | `(documents: dict, doc_id: str, pages: str) -> str` | Low-level page/line content helper over an existing `documents` dict. |

`PageIndexClient` sets `OPENAI_API_KEY` from its `api_key` argument. If no `api_key` is given and `OPENAI_API_KEY` is missing, it uses `CHATGPT_API_KEY` as a backward-compatible alias.
