# MCP and LangChain Integrations

This reference groups the non-local integration surfaces that sit on top of the hosted API or local PaddleOCR pipelines.

## MCP server

The repository provides a `paddleocr_mcp` server entry point.

### Installation notes

- `pip install -U paddleocr-mcp`
- `pip install "paddleocr-mcp[local]"` for local inference dependencies without the engine package
- `pip install "paddleocr-mcp[local-cpu]"` for local inference plus the CPU PaddlePaddle engine

### Provider modes

| Provider | Meaning | Key env vars |
| --- | --- | --- |
| `local` | Run local PaddleOCR pipelines through the MCP server | `PADDLEOCR_MCP_MODEL`, `PADDLEOCR_MCP_PIPELINE_CONFIG`, `PADDLEOCR_MCP_DEVICE` |
| `aistudio` | Use the official AI Studio API | `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN`, `PADDLEOCR_MCP_AISTUDIO_BASE_URL` |
| `qianfan` | Use the Qianfan API | `PADDLEOCR_MCP_QIANFAN_API_KEY`, `PADDLEOCR_MCP_QIANFAN_BASE_URL` |
| `self_hosted` | Use a self-hosted PaddleOCR service | `PADDLEOCR_MCP_SELF_HOSTED_BASE_URL` |

### Important CLI flags

- `--model`
- `--ppocr_source`
- `--http`
- `--host`
- `--port`
- `--verbose`
- `--pipeline_config`
- `--device`

### Important validation rules

- `--host` and `--port` are only valid with `--http`.
- AI Studio mode requires an access token.
- Qianfan mode requires an API key.
- Self-hosted mode requires a base URL.
- Qianfan only accepts the document-oriented models supported by the provider selection logic.

### MCP tool mapping

The server exposes OCR and document-parsing tools that map to the model family requested by the user. The model choice determines which tool name the host sees.

## LangChain loader

`langchain_paddleocr.PaddleOCRVLLoader` turns hosted PaddleOCR-VL document parsing into LangChain `Document` objects.

### Key constructor arguments

- `file_path`: a single path/URL or an iterable of paths/URLs
- `access_token`: optional `SecretStr`; falls back to `PADDLEOCR_ACCESS_TOKEN`
- `base_url`: hosted API base URL
- `model`: PaddleOCR-VL model or model name
- `timeout`: poll timeout for the request
- document-parsing toggles such as `use_doc_orientation_classify`, `use_doc_unwarping`, `use_layout_detection`, `use_chart_recognition`, `use_seal_recognition`, `use_ocr_for_image_block`, `merge_layout_blocks`, `prettify_markdown`, `show_formula_number`, and `restructure_pages`

### Returned document metadata

Each returned LangChain `Document` includes:

- `source`
- `paddleocr_vl_raw_response`

## Safe integration workflow

- Validate env vars and model/provider combinations before making a real remote call.
- Use local or fake tests for payload shape and provider routing.
- Keep MCP deployment and hosted API auth separate from local inference troubleshooting.
