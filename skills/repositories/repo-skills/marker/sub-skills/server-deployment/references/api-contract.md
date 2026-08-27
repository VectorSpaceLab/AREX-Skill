# FastAPI Contract

This contract describes the installed `marker_server` app. It is intentionally small and only wraps PDF conversion through Marker’s `PdfConverter`.

## Endpoints

| Method and path | Purpose | Body |
| --- | --- | --- |
| `GET /` | HTML landing page | none |
| `GET /docs` | FastAPI OpenAPI UI | none |
| `POST /marker` | Convert a server-visible file path | JSON body |
| `POST /marker/upload` | Convert an uploaded file | `multipart/form-data` |

The local server does not define a dedicated `/health` endpoint. Use `/` or `/docs` as a lightweight liveness check. The Modal recipe uses a separate `/health` endpoint in its hosted adaptation.

## `POST /marker` JSON body

Use filepath mode only when the server process can read the named file.

```json
{
  "filepath": "/path/visible/to/server.pdf",
  "page_range": "0,5-10,20",
  "force_ocr": false,
  "paginate_output": false,
  "output_format": "markdown"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `filepath` | yes for filepath mode | Path to a PDF readable by the server process. |
| `page_range` | no | Comma-separated zero-based pages/ranges, such as `0,5-10,20`. |
| `force_ocr` | no | Force OCR on every page. |
| `paginate_output` | no | Insert page separators into textual output. |
| `output_format` | no | One of `markdown`, `json`, `html`, or `chunks`; default is `markdown`. |

## `POST /marker/upload` multipart body

Use upload mode when the client owns the file or the server cannot read the client’s filesystem path.

| Part | Required | Meaning |
| --- | --- | --- |
| `file` | yes | Uploaded PDF file part. |
| `page_range` | no | Same syntax as filepath mode. |
| `force_ocr` | no | Boolean form value. |
| `paginate_output` | no | Boolean form value. |
| `output_format` | no | `markdown`, `json`, `html`, or `chunks`. |

The server writes uploads under a relative `uploads` directory in the server process working directory, converts the file, and removes it after a successful conversion path. Interrupted requests or early validation failures can leave files behind, so production adaptations should use unique filenames, size limits, cleanup jobs, and safer temporary-file handling.

## Response shape

Successful local server responses follow this shape:

```json
{
  "format": "markdown",
  "output": "converted content",
  "images": {"image-name": "base64-encoded-image-bytes"},
  "metadata": {},
  "success": true
}
```

Conversion exceptions caught by the server return:

```json
{
  "success": false,
  "error": "error message"
}
```

Invalid `output_format` is asserted before conversion. Clients should validate the format locally before sending a request.

## Client examples

Dry-run a filepath request without contacting a server:

```bash
python scripts/marker_server_client_template.py \
  --base-url http://127.0.0.1:8000 \
  --path /documents/input.pdf \
  --output-format markdown \
  --dry-run
```

Send a multipart upload:

```bash
python scripts/marker_server_client_template.py \
  --base-url http://127.0.0.1:8000 \
  --file ./input.pdf \
  --output-format html
```

Use the sibling conversion sub-skill for detailed output semantics and the sibling LLM sub-skill before adding LLM-specific fields to a custom server adaptation.
