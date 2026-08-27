# DocumentProcessingToolkit API

## Verified public surface

```python
DocumentProcessingToolkit(
    cache_dir: Optional[str] = None,
    model: Optional[BaseModelBackend] = None,
)
extract_document_content(document_path: str) -> Tuple[bool, str]
get_tools() -> List[FunctionTool]
```

`get_tools()` returns one `FunctionTool` around
`extract_document_content`. The method returns `(True, content)` on the handled
paths and `(False, message)` for several caught parser/web failures. Check the
boolean before trusting `content`.

## Dispatch behavior

| Input | Source behavior | Important prerequisite/side effect |
|---|---|---|
| `.jpg`, `.jpeg`, `.png` | Calls the image toolkit with a detailed-caption question | Needs a usable vision-capable model. The constructor may require a default provider key if `model` is omitted. |
| `.xls`, `.xlsx` | Calls CAMEL `ExcelToolkit.extract_excel_content` | Spreadsheet parser dependency and supported file. |
| `.zip` | Invokes `_unzip_file` and returns a list of extracted paths | Calls the system `unzip` command and writes under `cache_dir`. Use an isolated cache. |
| `.json`, `.jsonl`, `.jsonld` | Uses `json.load` | The implementation parses as one JSON document, so ordinary multi-line JSONL may fail despite the extension. |
| `.py` | Reads text with UTF-8 | Returns source text; do not execute the file. |
| `.xml` | Reads text, then attempts `xmltodict.parse` | Returns parsed data if valid, otherwise raw XML text with success true. |
| URL recognized as webpage | Calls Firecrawl when configured, otherwise Crawl4AI | Can make network/browser requests and return an error/no-content string. |
| Other local path | Uses CAMEL `UnstructuredIO.parse_file_or_url` | Parser support and optional native dependencies determine fidelity. |

## Constructor caveat

The class stores the requested cache directory but creates an
`ImageAnalysisToolkit` immediately. In the verified CAMEL runtime,
`ImageAnalysisToolkit(model=None)` creates CAMEL's default model backend. That
can raise a missing-key error during construction, before any image extraction
is requested. Pass an explicit, appropriately configured model for a real
workflow. For an offline route-selection test, use the bundled probe instead of
constructing the toolkit.

## URL classifier details

`_is_webpage` first parses the URL and rejects values without both scheme and
netloc. It checks a guessed MIME type and otherwise issues a `requests.head`
with redirects and a ten-second timeout. A request failure logs a warning and
returns false, sending the value to the general Unstructured path. Do not use
this as an authoritative security or URL-validation layer.

## Cache and archive safety

`_unzip_file` makes `<cache_dir>/<archive-stem>` and runs `unzip -o`. It lists
all files recursively. Choose a cache directory controlled by the caller,
validate archive size/content before extraction, and clear temporary output
according to the task's data-retention policy.
