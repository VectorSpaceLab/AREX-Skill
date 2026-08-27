# Azure Content Understanding

Use Azure Content Understanding when the user wants MarkItDown to perform cloud-backed multimodal conversion with optional structured field extraction. It can handle documents, images, audio, and video, and may emit YAML front matter from analyzer fields. This path requires the `markitdown[az-content-understanding]` extra or `markitdown[all]`, a Content Understanding endpoint, usable credentials, network access, and permission for billable service calls.

## Install Extra

```bash
pip install 'markitdown[az-content-understanding]'
```

The optional dependency set includes Azure Content Understanding SDK version support for the `to_llm_input()` helper and Azure Identity. If converter construction reports a missing dependency, install `markitdown[az-content-understanding]` or `markitdown[all]` in the active environment.

## CLI Usage

Basic Content Understanding conversion:

```bash
markitdown "<input.pdf>" --use-cu --cu-endpoint "https://<content-understanding-resource>.cognitiveservices.azure.com/"
```

Custom analyzer with limited routing:

```bash
markitdown "<input.mp4>" \
  --use-cu \
  --cu-endpoint "https://<content-understanding-resource>.cognitiveservices.azure.com/" \
  --cu-analyzer "<custom-analyzer-id>" \
  --cu-file-types pdf,mp4
```

Required parser conditions:

- `--use-cu` must include `--cu-endpoint`.
- A filename is required for Content Understanding CLI mode.
- `--use-cu` cannot be combined with `--use-docintel`.
- `--cu-file-types` is comma-separated and must use supported enum values such as `pdf,jpeg,mp4`.

## Python Usage

High-level MarkItDown routing:

```python
from markitdown import MarkItDown

md = MarkItDown(
    cu_endpoint="https://<content-understanding-resource>.cognitiveservices.azure.com/",
    cu_analyzer_id="<custom-analyzer-id>",
)
result = md.convert("<input.pdf>")
print(result.markdown)
```

Restrict cloud routing to selected formats:

```python
from markitdown import MarkItDown
from markitdown.converters import ContentUnderstandingFileType

md = MarkItDown(
    cu_endpoint="https://<content-understanding-resource>.cognitiveservices.azure.com/",
    cu_analyzer_id="<custom-analyzer-id>",
    cu_file_types=[
        ContentUnderstandingFileType.PDF,
        ContentUnderstandingFileType.MP4,
    ],
)
```

Direct converter use when a caller needs explicit control:

```python
from markitdown.converters import (
    ContentUnderstandingConverter,
    ContentUnderstandingFileType,
)
from azure.core.credentials import AzureKeyCredential

converter = ContentUnderstandingConverter(
    endpoint="https://<content-understanding-resource>.cognitiveservices.azure.com/",
    credential=AzureKeyCredential("<api-key-from-secure-secret-store>"),
    analyzer_id="<custom-analyzer-id>",
    file_types=[ContentUnderstandingFileType.PDF, ContentUnderstandingFileType.MP4],
)
```

Do not hard-code real keys. Use explicit credential objects only when the user provides a secure source for them and authorizes real Azure calls.

## File Types

Supported `ContentUnderstandingFileType` values:

- Documents and text: `pdf`, `docx`, `pptx`, `xlsx`, `html`, `txt`, `md`, `rtf`, `xml`.
- Email: `eml`, `msg`.
- Images: `jpeg`, `png`, `bmp`, `tiff`, `heif`.
- Video: `mp4`, `m4v`, `mov`, `avi`, `mkv`, `webm`, `flv`, `wmv`.
- Audio: `wav`, `mp3`, `m4a`, `flac`, `ogg`, `aac`, `wma`.

When `file_types` or `cu_file_types` is omitted, Content Understanding accepts all supported CU formats. To avoid sending local DOCX files to Azure while using CU for PDFs and MP4s, set `--cu-file-types pdf,mp4` on the CLI or `cu_file_types=[ContentUnderstandingFileType.PDF, ContentUnderstandingFileType.MP4]` in Python.

## Analyzer Routing

`ContentUnderstandingConverter.__init__` accepts:

- `endpoint`: required Content Understanding resource endpoint.
- `credential`: optional Azure key or token credential.
- `analyzer_id`: optional custom analyzer.
- `file_types`: optional list of accepted `ContentUnderstandingFileType` values.

If no analyzer is provided, MarkItDown auto-selects a prebuilt analyzer by modality:

- Document and image inputs use document-oriented prebuilt routing.
- Video inputs use `prebuilt-videoSearch`.
- Audio inputs use `prebuilt-audioSearch`.

If a custom analyzer is provided, the converter resolves its base modality during initialization. Compatible file types use the custom analyzer. Incompatible modalities automatically fall back to the default prebuilt analyzer for that file's modality. For example, a document analyzer can process documents and images, but MP4 video routes to a video prebuilt instead.

## YAML Front Matter

Content Understanding conversion formats the SDK result through the SDK's LLM input helper. When analyzer fields are present, the returned Markdown may begin with YAML front matter similar to:

```markdown
---
contentType: document
fields:
  VendorName: <extracted-value>
---
```

Treat extracted fields as service output from the user's configured analyzer. Do not promise specific field names unless the user describes the analyzer schema.

## Credentials and Boundaries

When no explicit `credential` is passed, MarkItDown's converter chooses credentials at runtime:

- If `AZURE_API_KEY` is set, it uses an Azure key credential.
- Otherwise it falls back to Azure Identity's default credential chain.

Every CU conversion sends file bytes over the network to Azure and may incur cost. Custom analyzer initialization can also require a service request when the analyzer ID is not a known prebuilt. Always perform local preflight first, then ask for explicit user authorization before real cloud calls.
