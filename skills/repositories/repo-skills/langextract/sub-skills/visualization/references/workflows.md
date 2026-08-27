# Visualization Workflows

## Purpose

Read this reference when a LangExtract result already exists and you need to
persist it, reload it, inspect the JSONL representation, or generate HTML. Do
not use these workflows to run model inference; route extraction and provider
setup to the sibling sub-skills.

## Verified API surface

Installed-package inspection confirmed these public signatures:

```python
lx.io.save_annotated_documents(
    annotated_documents,
    output_dir=None,
    output_name="data.jsonl",
    show_progress=True,
) -> None

lx.io.load_annotated_documents_jsonl(
    jsonl_path,
    show_progress=True,
) -> Iterator[lx.data.AnnotatedDocument]

langextract.visualization.visualize(
    data_source,
    *,
    animation_speed=1.0,
    show_legend=True,
    gif_optimized=True,
) -> HTML | str
```

`lx.visualize(...)` is a convenience wrapper around
`langextract.visualization.visualize(...)`. The full keyword-only visualization
signature belongs to `langextract.visualization.visualize`.

## Save AnnotatedDocument JSONL

Use JSONL when the user wants to review results later, share a portable artifact,
or visualize without re-running `lx.extract()`.

```python
import langextract as lx

# result is an lx.data.AnnotatedDocument returned by lx.extract() or constructed
# manually with valid text, extractions, and document_id.
lx.io.save_annotated_documents(
    [result],
    output_dir="./outputs",
    output_name="extraction_results.jsonl",
    show_progress=False,
)
```

Behavior to account for:

- `output_dir` may be a string or `Path`. If omitted, LangExtract uses a
  relative `test_output/` directory; prefer an explicit directory in reusable
  agent code.
- `output_name` defaults to `data.jsonl` and is joined under `output_dir`. It is
  not sanitized by LangExtract, so validate any user-controlled filename before
  passing it into a hosted or automated workflow.
- `show_progress=True` is the API default. It creates a save progress bar and
  prints a completion line; pass `show_progress=False` for logs, tests, or other
  non-interactive runs.
- The input is an iterator of `AnnotatedDocument` objects. If the iterator is
  empty, exhausted, or every produced document has a falsy `document_id`,
  LangExtract raises `InvalidDatasetError` instead of writing useful rows.
  `AnnotatedDocument(document_id=None, ...)` normally autogenerates an ID when
  accessed; explicit empty strings and non-document objects are the common
  save-time mistakes.

## Reload and inspect JSONL

`load_annotated_documents_jsonl()` yields `AnnotatedDocument` objects. It does
not silently repair malformed lines.

```python
from pathlib import Path
import langextract as lx

jsonl_path = Path("./outputs/extraction_results.jsonl")
documents = list(lx.io.load_annotated_documents_jsonl(jsonl_path, show_progress=False))

for doc in documents:
    print(doc.document_id, len(doc.extractions or []), bool(doc.text))
```

For multi-document files, select the document before visualizing:

```python
target_id = "case-42"
selected = next(doc for doc in documents if doc.document_id == target_id)
html = lx.visualize(selected, animation_speed=0.5, show_legend=True)
```

Use `langextract.data_lib` when you need dictionaries rather than dataclasses:

```python
from langextract import data_lib

as_dict = data_lib.annotated_document_to_dict(selected)
round_tripped = data_lib.dict_to_annotated_document(as_dict)
```

Conversion facts:

- `CharInterval` becomes `{"start_pos": ..., "end_pos": ...}` in JSON.
- `AlignmentStatus` enum values become strings such as `"match_exact"`.
- Private tokenization fields are intentionally omitted from the JSON dict.
- Missing `char_interval`, `token_interval`, or `alignment_status` round-trip as
  `None`.

## Visualize from an object or path

```python
import langextract as lx

# Direct object visualization.
html_content = lx.visualize(
    selected,
    animation_speed=0.5,
    show_legend=True,
    gif_optimized=True,
)

# JSONL path visualization. This loads the file and visualizes the first row.
html_content = lx.visualize("./outputs/extraction_results.jsonl")
```

Visualization behavior to remember:

- `data_source` may be an `AnnotatedDocument`, a string path, or a `Path`.
- A missing JSONL path raises `FileNotFoundError` from `visualize()` or `IOError`
  from the loader.
- A JSONL file with no rows raises `ValueError` when visualized from a path.
- An `AnnotatedDocument` must contain non-`None` `text` and `extractions`.
- If a JSONL path contains multiple documents, `visualize()` uses the first
  document. Load and choose the desired document yourself when document identity
  matters.
- `animation_speed` is the number of seconds between highlighted extractions
  while the HTML animation is playing.
- `show_legend=False` omits the class-to-color legend.
- `gif_optimized=True` applies larger, higher-contrast styling intended for GIF
  or video capture. Turn it off for a more compact page.

## Grounding and highlighted spans

LangExtract visualizes source-grounded extractions. A useful highlight needs a
`char_interval` whose `start_pos` and `end_pos` are present and define a
non-empty range in the document text.

```python
def has_visual_span(extraction):
    interval = extraction.char_interval
    return (
        interval is not None
        and interval.start_pos is not None
        and interval.end_pos is not None
        and 0 <= interval.start_pos < interval.end_pos
    )

grounded = [e for e in (selected.extractions or []) if has_visual_span(e)]
print(f"{len(grounded)} visually highlightable extractions")
```

If a document renders as `No valid extractions to animate.`, inspect intervals
before changing visualization parameters. `char_interval=None` usually means the
extraction result could not be aligned back to the exact source text; fix the
extraction/prompt/alignment workflow in the extraction sub-skill, or compute
correct offsets when constructing data manually.

## Write HTML in plain Python and notebooks

`visualize()` returns an `IPython.display.HTML` object when running inside a
Jupyter/IPython notebook that can display HTML. In ordinary Python it returns a
string. Write both safely like this:

```python
html_content = lx.visualize(selected)
payload = html_content.data if hasattr(html_content, "data") else html_content

with open("./outputs/visualization.html", "w", encoding="utf-8") as f:
    f.write(payload)
```

## No-model round trip helper

The bundled helper `scripts/save_and_visualize.py` is the quickest safe
workflow check. From the visualization sub-skill directory, run:

```bash
python scripts/save_and_visualize.py --output-dir ./lx-viz-demo
```

It handcrafts an `AnnotatedDocument`, saves JSONL, reloads it, converts the
reloaded document through `langextract.data_lib`, generates HTML, and reports
which extractions can be highlighted. It never calls `lx.extract()` and never
requires API keys.

## Evidence basis

The behavior above is distilled from the README save/visualization flow, the
long-document and medication visualization examples, implementation evidence in
`langextract/io.py`, `langextract/visualization.py`, `langextract/data_lib.py`,
`langextract/progress.py`, `langextract/core/data.py`, installed signature
inspection, and smoke verification that a handcrafted JSONL round trip and HTML
generation succeeded.
