# Provider Constraints

CrewAI formats files differently for each LLM provider. Validate content type and size before a real kickoff, especially when switching providers or API variants.

## Supported Native File Types

| Provider key/model signal | Images | PDF | Audio | Video | Text | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `openai`, `gpt` completions | Yes | No | No | No | No | Image content becomes OpenAI chat-style `image_url` or uploaded `file`. |
| `openai`/`gpt` with `api="responses"` | Yes | Yes | Yes | No | No | Responses API uses `input_image`, `input_file`, and `input_text` blocks. |
| `anthropic`, `claude` | Yes | Yes | No | No | No | Blocks are `image` or `document` with base64, URL, or file source. |
| `gemini`, `google` | Yes | Yes | Yes | Yes | Yes | Broadest native file surface, including text and video. |
| `bedrock`, `aws` | Yes | Yes | No | Formatter supports selected video/document bytes | Formatter supports selected document bytes | Constraints emphasize image/PDF; Bedrock formatting uses raw bytes or S3-style references. |
| `azure` | Yes | No | Yes | No | No | Mirrors selected OpenAI-compatible image/audio constraints. |

`get_supported_content_types(provider, api=None)` returns prefix-style support such as `image/`, `application/pdf`, `audio/`, `video/`, and `text/`. OpenAI Responses support is selected only when the provider looks OpenAI/GPT-like and `api="responses"`.

## Size and Count Limits

| Provider | Images | PDFs | Audio | Video | Text |
| --- | --- | --- | --- | --- | --- |
| OpenAI completions | 20,971,520 bytes; up to 10 images | Unsupported | Unsupported | Unsupported | Unsupported |
| OpenAI Responses | 20,971,520 bytes; up to 10 images | 33,554,432 bytes; up to 100 pages | 26,214,400 bytes; up to 1500 seconds | Unsupported | Unsupported |
| Anthropic | 5,242,880 bytes; 8000x8000 pixels; up to 100 images | 33,554,432 bytes; up to 100 pages | Unsupported | Unsupported | Unsupported |
| Gemini | 104,857,600 bytes | 52,428,800 bytes | 104,857,600 bytes; up to 34,200 seconds | 2,147,483,648 bytes; up to 3600 seconds | 104,857,600 bytes |
| Bedrock | 4,608,000 bytes; 8000x8000 pixels | 3,840,000 bytes; up to 100 pages | Unsupported | Not represented in constraints | Not represented in constraints |
| Azure | 20,971,520 bytes; up to 10 images | Unsupported | 26,214,400 bytes; up to 1500 seconds | Unsupported | Unsupported |

These values are encoded in `ProviderConstraints` objects and may be stricter than a model family's marketing page. Validate against the CrewAI runtime constraints for the installed version in use.

## MIME Formats

Default image formats are `image/png`, `image/jpeg`, `image/gif`, and `image/webp`. Gemini additionally supports `image/heic` and `image/heif` in constraints.

Default audio formats are `audio/mp3`, `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/flac`, `audio/aac`, and `audio/m4a`. Gemini additionally supports `audio/opus`.

Default video formats are `video/mp4`, `video/mpeg`, `video/webm`, and `video/quicktime`. Gemini additionally supports `video/x-msvideo` and `video/x-flv`.

Text formats include `text/plain`, `text/markdown`, `text/csv`, `application/json`, XML/YAML variants, and HTML, but only providers with text constraints treat text files as native multimodal payloads.

## File Modes

Each `BaseFile` accepts `mode` with one of `"strict"`, `"auto"`, `"warn"`, or `"chunk"`:

| Mode | Behavior |
| --- | --- |
| `strict` | Raises validation exceptions when provider constraints fail. Best for tests and preflight gates. |
| `auto` | Attempts supported transformations, mainly image resize/optimization; PDFs/audio/video are mostly kept as-is with warnings. |
| `warn` | Logs validation failures but leaves the file unchanged. |
| `chunk` | Splits PDFs by page limit or text by character-size approximation when optional dependencies are available. |

Optional transformation/validation dependencies matter: Pillow for image dimensions/resizing, `pypdf` for PDF page counting/chunking, `tinytag` for audio duration, and PyAV (`av`) for video duration. Missing libraries can downgrade checks to warnings or unknown duration/page counts.

## Formatting Shapes

`format_multimodal_content(files, provider, api=None, prefer_upload=None, text=None)` processes files, filters unsupported content types, resolves delivery, and formats provider-specific blocks.

- OpenAI Responses text block: `{"type": "input_text", "text": ...}`.
- OpenAI Responses image block: `{"type": "input_image", "image_url": ...}` or `{"type": "input_image", "file_id": ...}`.
- OpenAI Responses PDF block: `{"type": "input_file", "file_url": ...}`, `file_id`, or base64 `file_data`.
- OpenAI completions image block: `{"type": "image_url", "image_url": {"url": ...}}` for URL or inline data URI.
- Anthropic block: `{"type": "image"|"document", "source": {"type": "base64"|"url"|"file", ...}, "cache_control": {"type": "ephemeral"}}`.
- Gemini block: `{"inlineData": {"mimeType": ..., "data": ...}}` or `{"fileData": {"mimeType": ..., "fileUri": ...}}`.
- Bedrock block: `{"image": {"format": ..., "source": {"bytes": ...}}}` or `{"document": {"name": ..., "format": ..., "source": {"bytes": ...}}}`; S3-style file references use `s3Location`.

Avoid logging raw formatted blocks from real files because they may contain large base64 data or provider file IDs. Summarize block `type`, source kind, MIME, size, and filename instead.

## Provider Selection Heuristics

- Need image-only support with OpenAI chat completions: OpenAI/GPT completions can work.
- Need OpenAI PDF or audio native inputs: use an OpenAI/GPT model path with `api="responses"` and validate with `get_supported_content_types(provider, api="responses")`.
- Need video or native text-file payloads: prefer Gemini-compatible models.
- Need Bedrock Claude file inputs: validate small image/PDF sizes and decide whether bytes are acceptable or S3 upload is configured.
- Need unsupported file types or document search over many files: route to [tools-and-mcp](../../tools-and-mcp/SKILL.md) or [memory-knowledge-and-rag](../../memory-knowledge-and-rag/SKILL.md) instead of forcing native multimodal inputs.

## Validation Snippets

```python
from crewai_files import ImageFile, PDFFile, get_constraints_for_provider
from crewai_files.processing.validators import validate_file

constraints = get_constraints_for_provider("openai_responses")
files = {
    "chart": ImageFile(source="chart.png", mode="strict"),
    "report": PDFFile(source="report.pdf", mode="strict"),
}
for name, file_input in files.items():
    errors = validate_file(file_input, constraints, raise_on_error=False)
    print(name, file_input.content_type, errors)
```

```python
from crewai_files import ImageFile, format_multimodal_content

blocks = format_multimodal_content(
    {"chart": ImageFile(source="chart.png")},
    provider="openai/gpt-4o-mini",
    api="responses",
    text="Describe the chart.",
)
print([block.get("type") or next(iter(block)) for block in blocks])
```

## Boundary With LLM Provider Setup

This reference covers file payload constraints. For API keys, model IDs, provider/base URL configuration, hosted endpoint choices, streaming, and non-file compatibility, use [llm-and-providers](../../llm-and-providers/SKILL.md).
