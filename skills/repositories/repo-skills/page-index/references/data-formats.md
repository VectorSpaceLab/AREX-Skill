# Data Formats

## PDF / Flash tree nodes

PDF tree page indexes are 1-based and inclusive.

Common node fields:

| Field | Meaning |
| --- | --- |
| `title` | Section or synthesized title. |
| `node_id` | Zero-padded pre-order identifier when enabled. |
| `start_index` | First physical PDF page covered by the node. |
| `end_index` | Last physical PDF page covered by the node or subtree. |
| `summary` | Optional node summary. Requires a model unless the code reuses short raw text. |
| `text` | Optional retained source text. Usually omitted to keep output small. |
| `key_items` | Titles preserved from nodes merged away by optimization. |
| `nodes` | Child sections. Missing or empty means leaf. |

Classic PDF output usually has this shape:

```json
{
  "doc_name": "document.pdf",
  "doc_description": "optional one-sentence description",
  "structure": [
    {"title": "Introduction", "node_id": "0000", "start_index": 1, "end_index": 3}
  ]
}
```

Flash output can also include:

```json
{
  "doc_name": "document.pdf",
  "doc_title": "Detected title",
  "has_abstract_or_references_section": false,
  "toc_source": "detected|hybrid|bookmarks",
  "optimize": {
    "merges": 1,
    "expands": 0,
    "before": {"worst_case_search_complexity": 6},
    "after": {"worst_case_search_complexity": 6}
  },
  "structure": []
}
```

`toc_source` appears when embedded bookmarks are considered. `optimize` appears only when optimization is requested.

## Markdown tree output

Markdown nodes use source line numbers instead of page ranges.

```json
{
  "doc_name": "notes",
  "line_count": 42,
  "doc_description": "optional description",
  "structure": [
    {
      "title": "Title",
      "node_id": "0001",
      "line_num": 1,
      "summary": "optional",
      "nodes": []
    }
  ]
}
```

Markdown heading rules:

- ATX headings (`#`, `##`, ... `######`) become tree nodes.
- A bold-only line such as `**Heading**` becomes a level-1 node if the title is non-empty.
- Headings inside fenced code blocks are ignored.
- When `if_thinning=True`, small child nodes can be merged into a parent before tree construction.

## Workspace layout

A workspace is a directory containing `_meta.json` plus one JSON file per document id.

`_meta.json` maps document ids to lightweight entries:

```json
{
  "doc-id": {
    "type": "pdf",
    "doc_name": "document.pdf",
    "doc_description": "short description",
    "path": "optional/source/path",
    "page_count": 10
  }
}
```

A full document JSON can include:

```json
{
  "id": "doc-id",
  "type": "pdf",
  "path": "document.pdf",
  "doc_name": "document.pdf",
  "doc_description": "short description",
  "page_count": 10,
  "structure": [],
  "pages": [
    {"page": 1, "content": "page text"}
  ]
}
```

For Markdown documents, use `type: "md"`, `line_count`, and a structure with `line_num` fields.

`get_page_content` accepts page or line selectors as strings:

- `"5-7"`
- `"3,8"`
- `"12"`

It returns a JSON string containing a list of `{"page": int, "content": str}` records or an `{"error": ...}` object.
