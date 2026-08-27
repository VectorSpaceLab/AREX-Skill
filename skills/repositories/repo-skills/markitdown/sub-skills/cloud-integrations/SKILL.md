---
name: cloud-integrations
description: "Use MarkItDown Azure Document Intelligence and Azure Content
  Understanding integrations safely from CLI and Python."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MarkItDown Cloud Integrations

Use this sub-skill when a user explicitly wants MarkItDown to send supported files to Azure Document Intelligence or Azure Content Understanding. These integrations require Azure endpoints, credentials, optional MarkItDown extras, network access, and may incur service cost. For local/offline conversion use `../core-conversion/SKILL.md`; for OCR plugin behavior use `../ocr-plugin/SKILL.md`; for MCP serving use `../mcp-server/SKILL.md`.

## Choose the Integration

- **Document Intelligence**: use for document/image layout extraction through Azure Document Intelligence `prebuilt-layout`; CLI flags are `--use-docintel` or `-d` plus `--endpoint` or `-e`.
- **Content Understanding**: use for multimodal document, image, audio, and video conversion; CLI flags are `--use-cu`, `--cu-endpoint`, optional `--cu-analyzer`, and optional `--cu-file-types`.
- **Mutual exclusion**: `--use-docintel` and `--use-cu` cannot be combined in one CLI invocation.
- **Safe first step**: run `scripts/check_cloud_configuration.py` for import, argument, and file-type validation before any real cloud conversion.

## Safe Preflight

The bundled checker performs local validation only by default and does not call Azure.

```bash
python scripts/check_cloud_configuration.py \
  --mode cu \
  --endpoint "https://<content-understanding-resource>.cognitiveservices.azure.com/" \
  --analyzer "<custom-analyzer-id>" \
  --file-types pdf,mp4
```

For Document Intelligence:

```bash
python scripts/check_cloud_configuration.py \
  --mode docintel \
  --endpoint "https://<document-intelligence-resource>.cognitiveservices.azure.com/"
```

## References

- `references/azure-document-intelligence.md`: install extras, CLI flags, Python usage, file-type routing, credentials, and cloud boundaries for `DocumentIntelligenceConverter`.
- `references/content-understanding.md`: install extras, CLI flags, Python usage, analyzer routing, YAML front matter, multimodal file types, and `cu_file_types` restrictions for `ContentUnderstandingConverter`.
- `references/troubleshooting.md`: parser failures, missing optional dependencies, credential selection, analyzer mismatch behavior, and safe cloud-call boundaries.

## Safety Rules

- Do not make a real Azure request unless the user supplies an endpoint and explicitly authorizes network use, credentials, and possible cost.
- Use placeholders in examples; never hard-code API keys, tokens, or real endpoints in skill content or generated code.
- Prefer `--cu-file-types` or `cu_file_types` when the user wants only selected formats routed to the cloud, such as PDFs and MP4s while keeping DOCX offline.
- Treat credential discovery as runtime behavior: explicit credential objects in Python win when provided; otherwise MarkItDown cloud converters may use `AZURE_API_KEY` or Azure identity defaults depending on installed Azure SDK support.
