# Files and Multimodal Troubleshooting

Use this page when CrewAI file inputs fail before kickoff, disappear from provider payloads, fall back to file tools, or behave differently across providers.

## Quick Triage

1. Confirm `crewai-files` is installed and importable.
2. Print each file key, class, source kind, filename, MIME type, and byte size without printing file content.
3. Compare each MIME type with `get_supported_content_types(provider, api=...)`.
4. Validate against `get_constraints_for_provider(...)` with `raise_on_error=False` first.
5. Decide whether native `input_files`, legacy `multimodal=True`, document tools, or RAG is the right path.
6. Only then run an LLM kickoff or provider upload if the user approved network/credential side effects.

## Common Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: crewai_files` | Optional file-processing package is missing. | Install CrewAI with file-processing support or add `crewai-files`; keep generated examples import-based and no-network by default. |
| MIME is `application/octet-stream` | Missing extension, ambiguous bytes, or `python-magic` unavailable/fell back. | Add a filename to `FileBytes`, use a typed class, install `python-magic` where allowed, or pass a real file path with extension. |
| `Invalid URL scheme` | `FileUrl` only accepts `http://` and `https://`. | Use local `FilePath`/path strings for local files; do not pass `file://` to `FileUrl`. |
| Path traversal rejected | `FilePath` rejects paths containing `..`. | Resolve/copy the file into an allowed working directory and pass a clean path. |
| Symlink rejected | Symlink resolves outside current working directory. | Use the real file inside the working directory or avoid symlinked inputs. |
| File not found | Relative path is resolved against the process current directory or JSON project root. | Use the project-relative path expected by the runtime, or pre-resolve before constructing `FilePath`. |
| Provider receives no file blocks | File type filtered as unsupported for provider/API. | Use a provider/API that supports the MIME type, e.g. OpenAI Responses for PDFs/audio or Gemini for video/text. |
| Model says it does not support multimodal input | LLM reports no native multimodal support but `input_files` were provided. | Choose a multimodal-capable model/provider, remove `input_files`, or use file/document tools instead. |
| PDF works with Anthropic but not OpenAI | OpenAI chat completions support images only; PDFs require Responses API in CrewAI constraints. | Use `LLM(model="openai/...", api="responses")` and validate `application/pdf` support. |
| Video ignored or routed to tool | Most providers do not support native video in constraints. | Use Gemini for native video or use document/file tools/RAG depending on the task. |
| Bedrock URL unexpectedly fetches | Ordinary HTTP(S) URLs are not passed as direct Bedrock URL references. | Use local bytes for small files, configure S3 upload intentionally, or avoid remote Bedrock validation in no-network mode. |
| Upload attempted unexpectedly | `prefer_upload=True`, file exceeds upload threshold, or provider config prefers upload. | Set `prefer_upload=False` for dry runs; inspect resolver config before kickoff. |
| Cache cleanup deletes provider files | Cleanup helper called with provider deletion enabled. | Use local cache clear/reset for dry runs; provider cleanup requires explicit approval. |
| Base64 bytes misuse | Raw base64 text was passed as `bytes`, so MIME detection sees plain text or octet-stream. | Decode base64 into bytes and pass a filename through `FileBytes`, or pass a `data:<mime>;base64,...` URI only to a diagnostic tool that decodes it. |
| `UnsupportedFileTypeError` | Typed file class or MIME not supported by constraints. | Change provider/API, change file class/source, or route to file tools/RAG. |
| Size/page/duration validation is incomplete | Pillow, `pypdf`, `tinytag`, or PyAV is missing. | Install optional dependency when allowed, or treat the result as a best-effort preflight and use stricter provider-side limits. |

## Missing Optional Dependencies

`python-magic` improves MIME detection, but CrewAI falls back to extensions and limited byte sniffing when it is absent. If a byte input lacks a filename and `python-magic` is missing, provider filtering may reject it as `application/octet-stream`.

Validation/transformation helpers use optional packages:

- Pillow: image dimensions, resizing, optimization.
- `pypdf`: PDF page count and chunking.
- `tinytag`: audio duration.
- PyAV (`av`): video duration.
- Provider SDKs (`openai`, `anthropic`, `google-genai`, `boto3`): uploaders.

If installing packages is not allowed, use file size, extension, MIME guesses, and provider support tables as a conservative preflight.

## Native Inputs Versus Tools

Native `input_files` are best for a small number of files the model should directly inspect. File/document tools are better when the agent needs to open files on demand, search a directory, write outputs, or handle file types the model cannot natively consume. RAG/knowledge is better for persistent retrieval, embeddings, or large corpora.

Route accordingly:

- File/document tools and custom tools: [tools-and-mcp](../../tools-and-mcp/SKILL.md).
- Knowledge sources, RAG loaders, embeddings, vector stores: [memory-knowledge-and-rag](../../memory-knowledge-and-rag/SKILL.md).
- Provider credentials/model choice: [llm-and-providers](../../llm-and-providers/SKILL.md).
- Task/crew design, callbacks, outputs, guardrails: [core-runtime](../../core-runtime/SKILL.md).

## Multimodal Flag Issues

`Agent(multimodal=True)` enables a legacy image-tool path and is described in runtime metadata as deprecated in favor of native file inputs. If an old task says “set `multimodal=True` and paste an image URL in the description,” consider migrating to:

```python
from crewai_files import ImageFile

task.input_files = {"product_image": ImageFile(source="product.jpg")}
```

Keep `multimodal=True` only when the desired behavior is the built-in image tool and not native provider file payloads.

## Provider-Specific Fixes

### OpenAI

- Use `api="responses"` for PDF and audio native file inputs.
- Chat/completions constraints support images, not PDFs/audio/video/text.
- Large files may upload when supported; avoid `prefer_upload=True` during no-network checks.

### Anthropic

- Native support covers images and PDFs.
- Audio/video/text should route to tools or another provider.
- Blocks use ephemeral cache control; do not assume persistent provider storage unless using upload APIs intentionally.

### Gemini

- Best fit for mixed image/PDF/audio/video/text native inputs.
- Upload threshold is higher than OpenAI/Anthropic; very large video can still require provider upload behavior.

### Bedrock

- Constraints focus on small images and PDFs.
- Formatter can emit raw bytes for images/documents and S3 locations for uploaded references.
- Configure S3 upload intentionally with Bedrock bucket settings; ordinary HTTP(S) URLs are not direct Bedrock references.

## Safe Diagnostic Command

Run the bundled checker before real kickoff:

```bash
python skills/crewai/sub-skills/files-and-multimodal/scripts/check_file_inputs.py \
  --provider openai --api responses \
  --file chart=./chart.png \
  --file report=./report.pdf \
  --data-uri sample='data:text/plain;base64,SGVsbG8='
```

The checker validates source coercion, MIME detection, provider support, constraints, and resolution class without network fetches, uploads, LLM calls, or credential use by default.

## Source Artifact Note

A repository maintenance script for an AGE-90 PDF investigation was adapted into the bundled `check_file_inputs.py` diagnostic. Its real kickoff and payload-patching modes were intentionally excluded because they can require provider credentials, LLM calls, or source-repository fixtures. The bundled script keeps only safe inspection patterns and replaces source-specific defaults with user-provided inputs.
