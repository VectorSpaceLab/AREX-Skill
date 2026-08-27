# Azure Document Intelligence

Use Azure Document Intelligence when the user wants MarkItDown to perform cloud-backed document or image layout extraction instead of fully offline conversion. This path requires the `markitdown[az-doc-intel]` extra or `markitdown[all]`, an Azure Document Intelligence endpoint, usable credentials, network access, and permission for billable service calls.

## Install Extra

```bash
pip install 'markitdown[az-doc-intel]'
```

The optional dependency set includes the Azure Document Intelligence SDK and Azure Identity support. If the converter raises a missing dependency error, install `markitdown[az-doc-intel]` or `markitdown[all]` in the active environment.

## CLI Usage

```bash
markitdown "<input.pdf>" --use-docintel --endpoint "https://<document-intelligence-resource>.cognitiveservices.azure.com/" -o "<output.md>"
```

Equivalent short flags:

```bash
markitdown "<input.pdf>" -d -e "https://<document-intelligence-resource>.cognitiveservices.azure.com/"
```

Required parser conditions:

- `--use-docintel` or `-d` must include `--endpoint` or `-e`.
- A filename is required for cloud mode; stdin-only conversion is not accepted for this CLI branch.
- `--use-docintel` cannot be combined with `--use-cu`.

## Python Usage

High-level MarkItDown routing:

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="https://<document-intelligence-resource>.cognitiveservices.azure.com/")
result = md.convert("<input.pdf>")
print(result.markdown)
```

Direct converter use when a caller needs explicit control:

```python
from markitdown.converters import (
    DocumentIntelligenceConverter,
    DocumentIntelligenceFileType,
)
from azure.core.credentials import AzureKeyCredential

converter = DocumentIntelligenceConverter(
    endpoint="https://<document-intelligence-resource>.cognitiveservices.azure.com/",
    credential=AzureKeyCredential("<api-key-from-secure-secret-store>"),
    file_types=[
        DocumentIntelligenceFileType.PDF,
        DocumentIntelligenceFileType.JPEG,
        DocumentIntelligenceFileType.PNG,
    ],
)
```

Do not place real keys in source files, prompts, logs, or generated Markdown. Retrieve them from the user's secret manager or environment only when the user authorizes a real cloud call.

## Converter Behavior

`DocumentIntelligenceConverter.__init__` accepts:

- `endpoint`: required Azure Document Intelligence service endpoint.
- `api_version`: defaults to `2024-07-31-preview`.
- `credential`: optional Azure key or token credential.
- `file_types`: supported file-type enum list.

Supported enum values are `docx`, `pptx`, `xlsx`, `html`, `pdf`, `jpeg`, `png`, `bmp`, and `tiff`. The default converter list includes `docx`, `pptx`, `xlsx`, `pdf`, `jpeg`, `png`, `bmp`, and `tiff`; add `DocumentIntelligenceFileType.HTML` explicitly when using direct converter construction for HTML.

The converter sends file bytes to Azure Document Intelligence using `prebuilt-layout`, asks for Markdown content, and removes HTML comments from the returned Markdown. For Office and HTML formats it skips OCR-specific analysis features; for OCR-capable image/PDF inputs it enables formula extraction, high-resolution OCR, and font-style analysis when supported by the SDK.

## Credentials

When no explicit `credential` is passed, MarkItDown's converter chooses credentials at runtime:

- If `AZURE_API_KEY` is set, it uses an Azure key credential.
- Otherwise it falls back to Azure Identity's default credential chain.

Always ask the user which credential path they intend to use before making a network call. Do not invent endpoints, tenant details, or keys.

## Boundaries

- Every successful conversion attempt sends document bytes over the network to Azure and may incur cost.
- This skill does not cover Azure account creation, resource provisioning, service benchmarking, or cost measurement.
- For offline file conversion without Azure, route to `../core-conversion/SKILL.md`.
- For plugin-based OCR, route to `../ocr-plugin/SKILL.md`.
