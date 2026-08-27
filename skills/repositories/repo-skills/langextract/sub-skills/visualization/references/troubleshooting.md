# Visualization Troubleshooting

Use this page when saving JSONL, loading saved LangExtract output, or rendering
interactive HTML fails or looks incomplete.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `InvalidDatasetError: No documents to save in: ...` | The iterator passed to `save_annotated_documents()` was empty/exhausted, yielded the wrong object type, or every document had a falsy `document_id`. | Rebuild the iterator, pass `AnnotatedDocument` objects, and ensure each document has a non-empty ID. `AnnotatedDocument(document_id=None, ...)` normally autogenerates an ID; explicit empty strings are the common pitfall. |
| A JSONL file is created in an unexpected place. | `output_dir` was omitted, so LangExtract used its relative default directory, or `output_name` contained path separators. | Always pass an explicit `output_dir` and validate any user-controlled `output_name`. Prefer simple names like `results.jsonl`. |
| Progress bars or colored completion lines pollute logs. | `show_progress=True` is the default for save/load functions. | Pass `show_progress=False` to `save_annotated_documents()` and `load_annotated_documents_jsonl()`. If `lx.visualize(path)` emits load progress, manually load with `show_progress=False` and then call `lx.visualize(document)`. |
| `FileNotFoundError: JSONL file not found: ...` or `IOError: File does not exist: ...` | The path points to a missing file or a different current working directory than expected. | Resolve the path before visualization, print `Path(...).resolve()` in private debugging if needed, or pass a path relative to the process working directory. Do not hard-code local checkout paths into reusable code. |
| `json.JSONDecodeError` while loading JSONL. | A line is not valid JSON, the file is a pretty-printed JSON array instead of JSONL, or a prior write was interrupted. | Inspect the first failing line, rewrite as one complete JSON object per line, or regenerate with `save_annotated_documents()`. Blank lines are ignored; malformed nonblank lines are not repaired. |
| Only one document appears even though the JSONL has many rows. | `visualize()` called with a JSONL path loads the file and uses `documents[0]`. | Use `load_annotated_documents_jsonl()`, select by `document_id` or index, then pass the selected `AnnotatedDocument` to `lx.visualize()`. |
| `ValueError: No documents found in JSONL file: ...` | The file exists but has no nonblank JSONL rows. | Confirm the save step wrote at least one document and that the source iterator was not consumed before saving. |
| `ValueError: annotated_doc must contain text to visualise.` | The selected `AnnotatedDocument` has `text=None` or an empty/invalid text payload. | Reload the correct document, preserve `text` during any `data_lib` conversion, or rerun/repair the upstream extraction route so result text is included. |
| `ValueError: annotated_doc must contain extractions to visualise.` | `extractions` is `None` instead of a list. | Use an empty list for a no-extraction document or preserve the extraction list through conversion. If you expected extracted entities, route to the extraction sub-skill. |
| The HTML says `No valid extractions to animate.` | All extractions have missing `char_interval`, missing start/end positions, or unusable intervals. | Inspect intervals. For model-produced results, route to extraction troubleshooting for grounding/alignment. For handcrafted data, compute offsets against `doc.text` and ensure `start_pos < end_pos`. |
| Some extracted rows are listed in JSONL but not highlighted. | Ungrounded or invalid intervals are not rendered as source spans. Zero-length or reversed intervals are especially confusing. | Filter highlightable extractions before visualizing, or fix offsets. A safe validity check is `interval and interval.start_pos is not None and interval.end_pos is not None and interval.start_pos < interval.end_pos`. |
| Written HTML is blank, shows a Python object repr, or contains no markup. | Notebook return handling was not normalized. In Jupyter/IPython the return may be an `HTML` object; in plain Python it is a string. | Write `payload = html.data if hasattr(html, "data") else html`, then write `payload` with UTF-8 encoding. |
| The page is too large or sluggish. | Large documents and thousands of highlighted extractions produce large self-contained HTML and heavy browser work. | Visualize one document at a time, prefilter to the classes or interval range the user needs, consider `show_legend=False`, use `gif_optimized=False` for compact styling, and keep JSONL as the canonical artifact. |
| User asks to change frontend controls, CSS architecture, or embed a custom UI. | This repo skill only covers generated LangExtract HTML, not custom frontend development. | Explain the unsupported gap. You may save JSONL and generated HTML, but custom frontend implementation should be handled as a separate software task. |

## Quick diagnostic snippets

### Count highlightable extractions

```python
def highlightable(extraction):
    interval = extraction.char_interval
    return (
        interval is not None
        and interval.start_pos is not None
        and interval.end_pos is not None
        and interval.start_pos < interval.end_pos
    )

for doc in documents:
    total = len(doc.extractions or [])
    grounded = sum(1 for e in (doc.extractions or []) if highlightable(e))
    print(doc.document_id, f"{grounded}/{total} highlightable")
```

### Select a specific document from JSONL

```python
from pathlib import Path
import langextract as lx

documents = list(lx.io.load_annotated_documents_jsonl(Path("results.jsonl"), show_progress=False))
selected = next(doc for doc in documents if doc.document_id == "target-id")
html = lx.visualize(selected)
```

### Suppress progress while visualizing a JSONL file

```python
from pathlib import Path
import langextract as lx

doc = next(lx.io.load_annotated_documents_jsonl(Path("results.jsonl"), show_progress=False))
html = lx.visualize(doc)
```

## When to route elsewhere

- Re-running extraction, prompt repair, resolver tuning, or missing
  `char_interval` from model output: `../../extraction/SKILL.md`.
- API keys, providers, Vertex/OpenAI batch, or Ollama service issues:
  `../../providers/SKILL.md`.
- Custom visualization UI beyond generated HTML: unsupported gap for this repo
  skill.
