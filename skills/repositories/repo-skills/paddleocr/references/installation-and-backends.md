# Installation and Backend Notes

Use this reference when choosing dependency extras, backend families, or smoke checks. The generated runtime skill should stay self-contained and should not depend on the original checkout remaining available.

## Base install

```bash
python -m pip install paddleocr
```

The package requires Python `>=3.8` and depends on `paddlex[ocr-core]` plus light utility libraries. Use the package's optional extras only when the selected workflow needs them.

## Optional extras by workflow

| Workflow | Recommended install | Why |
| --- | --- | --- |
| Local document parsing | `python -m pip install "paddleocr[doc-parser]"` | Enables PP-StructureV3 / PaddleOCR-VL / hosted parsing-oriented helpers. |
| Office document conversion | `python -m pip install "paddleocr[doc2md]"` | Adds `python-docx`, `python-pptx`, `openpyxl`, and `pylatexenc` for `doc2md`. |
| Information extraction / hosted document parsing | `python -m pip install "paddleocr[ie]"` | Adds the broader PaddleX document-parsing stack. |
| Translation-oriented workflows | `python -m pip install "paddleocr[trans]"` | Adds translation-oriented PaddleX dependencies. |
| Everything in one environment | `python -m pip install "paddleocr[all]"` | Only use when you truly need every supported family; it is broader than most tasks need. |

## Backend and runtime notes

- CPU import and CLI/help checks are sufficient for the core package surface.
- Local model inference may need PaddlePaddle CPU or GPU wheels plus the matching PaddleX inference engine.
- PaddleOCR-VL and some document parsing paths may require additional VLM/service backends depending on the selected pipeline version and host hardware.
- `paddleocr` defaults to downloading models from HuggingFace. If that is blocked, set `PADDLE_PDX_MODEL_SOURCE=BOS`.

## Common environment variables

| Variable | Used for | Notes |
| --- | --- | --- |
| `PADDLE_PDX_MODEL_SOURCE` | model download source | Set to `BOS` when HuggingFace is unavailable. |
| `PADDLEOCR_ACCESS_TOKEN` | hosted API auth | Required by the official API client and some integrations. |
| `PADDLEOCR_BASE_URL` | hosted API endpoint override | Optional override for the official API service URL. |
| `PADDLEOCR_MCP_*` | MCP server configuration | See the cloud/integration sub-skill for provider-specific variables. |

## Suggested smoke checks

```bash
python -c "import paddleocr; print(paddleocr.__version__)"
paddleocr --help
paddleocr --version
paddleocr doc2md --formats
```

If the selected workflow needs the public API client, also check the option dataclasses and error mapping in the cloud/integration sub-skill before attempting a real remote request.
