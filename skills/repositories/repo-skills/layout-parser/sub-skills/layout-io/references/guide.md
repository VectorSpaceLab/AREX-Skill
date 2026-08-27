# Layout I/O Guide

This guide covers the file-based path into and out of LayoutParser layouts.
It is the right place for JSON/CSV/DataFrame/PDF loading, page metadata, and
COCO-style conversion patterns.

## Main APIs

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `load_json(filename)` | Read a JSON file into a `Layout` or `TextBlock` | Accepts serialized `layoutparser` dicts |
| `load_dict(data)` | Rebuild a layout object from dict/list data | Used by `load_json()` and custom pipelines |
| `load_csv(filename, block_type=None)` | Load a CSV file into a `Layout` | `block_type` is required when the CSV lacks that column |
| `load_dataframe(df, block_type=None)` | Load from a pandas dataframe | Same rules as CSV |
| `load_pdf(filename, load_images=False, ...)` | Extract page tokens from a PDF | Uses `pdfplumber`; image rendering also uses `pdf2image` |

## Data format rules

### JSON / dict

- A block dict must contain `block_type`.
- `TextBlock` rows carry the underlying block fields plus optional content
  fields such as `text`, `id`, `type`, `parent`, `next`, and `score`.
- Layout dicts contain `page_data` and a `blocks` list.

### CSV / dataframe

- `block_type` must be present in the dataframe or supplied explicitly.
- `points` columns are parsed back into lists/arrays when they look like
  literal Python data.
- If a textblock column is present and `id` is missing, `load_dataframe()`
  synthesizes the index as the id.
- For quadrilateral CSV rows, confirm that the `points` column is parsed back
  to Python lists before calling `load_dataframe()`. With newer pandas string
  dtypes, a CSV value such as `"[0, 1, 2, 3, 4, 5, 6, 7]"` can remain a plain
  string and make `Quadrilateral(...)` raise a `ValueError`. Work around this
  by applying `ast.literal_eval` to non-null `points` values or by using JSON
  for quadrilateral-heavy round-trips.

### PDF

- `load_pdf()` returns a list of page layouts by default.
- Each page layout gets `page_data` with `width`, `height`, and `index`.
- `load_images=True` also returns rendered page images and rescales the page
  layout when the rendered image size differs from the PDF page size.

## Typical workflows

### 1) Round-trip a layout

1. Build or load a `Layout`.
2. Serialize it with `to_dict()` or `to_dataframe()`.
3. Persist it as JSON or CSV.
4. Read it back with `load_json()`, `load_dict()`, `load_csv()`, or
   `load_dataframe()`.

### 2) Parse a PDF page

1. Call `load_pdf(path)`.
2. Inspect `page_data` for dimensions and page index.
3. Filter or sort each page layout before visualization or OCR.
4. If you need rendered images too, enable `load_images=True` and make sure the
   image-rendering dependency stack is present.

### 3) Convert COCO-style annotations

The repository's notebook example shows the standard pattern:

1. Read a COCO annotation list.
2. Convert each `bbox` into a `Rectangle`.
3. Wrap it in `TextBlock` if category or score metadata matters.
4. Put the blocks into a `Layout` and visualize them.

That conversion pattern is safe to adapt into a local helper for later reuse.
See `../scripts/coco_layout_helpers.py` for a bundled version of the notebook recipe.

## Troubleshooting

- `ValueError: block_type not specified`: supply the column or pass
  `block_type=` explicitly.
- `ValueError: Invalid input JSON structure`: the JSON does not match the
  expected dict/list layout schema.
- `ValueError` from `Quadrilateral` while loading CSV often means the `points`
  column stayed as a string; pre-parse it with `ast.literal_eval` or use JSON.
- `load_pdf(..., load_images=True)` fails: install or repair `pdf2image` and a
  local PDF renderer such as poppler.
- Empty PDFs still return one layout per page, but the page may contain no text
  tokens.
- CSV files with mixed textblocks and plain blocks need careful column handling
  so ids and texts survive the round-trip.

## Read next

- `../layout-objects/references/guide.md` for coordinate manipulation after
  loading
- `../visualization/references/guide.md` for overlays on images and pages
- `../../../references/troubleshooting.md` for common file and PDF issues
