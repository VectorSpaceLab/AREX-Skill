# File Inputs

CrewAI file support comes from the optional `crewai-files` package. Use it when files should be part of the prompt payload sent to a multimodal-capable LLM. Use document tools instead when the agent should browse, read, write, search, or OCR files through tool calls.

## Public Imports

The verified public surface includes:

```python
from crewai import Agent, Crew, LLM, Task
from crewai_files import (
    AudioFile,
    File,
    FileBytes,
    FilePath,
    FileResolver,
    FileResolverConfig,
    FileUrl,
    ImageFile,
    PDFFile,
    TextFile,
    VideoFile,
    format_multimodal_content,
    get_supported_content_types,
    normalize_input_files,
)
```

The installed package family version observed for `crewai`, `crewai-files`, `crewai-tools`, `crewai-cli`, `crewai-core`, and `crewai-devtools` is `1.14.8a2`.

## File Classes and Sources

| Need | Use | Notes |
| --- | --- | --- |
| Auto-detect file type | `File(source=...)` | Keeps the source but lets content type drive later formatting. |
| Images | `ImageFile(source=...)` | PNG, JPEG, GIF, WebP, BMP, TIFF, SVG, HEIC/HEIF are represented in type aliases; provider support is narrower. |
| PDFs | `PDFFile(source=...)` | Provider page and size limits matter. |
| Text | `TextFile(source=...)` | Text, markdown, CSV, JSON, XML, YAML, HTML, logs, config-like files. |
| Audio | `AudioFile(source=...)` | Provider duration checks require optional duration libraries. |
| Video | `VideoFile(source=...)` | Gemini has the broadest native video support; Bedrock formatter can produce video blocks for known formats. |

`source` can be a local path string, `pathlib.Path`, `FilePath`, HTTP(S) URL string, `FileUrl`, raw `bytes`, `FileBytes`, binary seekable stream, or compatible async readable source. A string beginning with `http://` or `https://` becomes `FileUrl`; other strings become `FilePath`.

```python
from crewai_files import FileBytes, FileUrl, ImageFile, PDFFile, TextFile

chart = ImageFile(source="./charts/revenue.png")
remote_chart = ImageFile(source=FileUrl(url="https://example.com/revenue.png"))
pdf = PDFFile(source="./reports/q4.pdf", mode="strict")
notes = TextFile(source=FileBytes(data=b"key,value\n1,2\n", filename="metrics.csv"))
```

## Local Path Rules

`FilePath` validates before kickoff:

- Path traversal strings containing `..` are rejected.
- Symlinks that resolve outside the current working directory are rejected.
- Missing paths and non-file paths are rejected.
- The default source-level max size is `524_288_000` bytes before provider-specific validation.
- MIME detection uses `python-magic` when installed; otherwise it falls back to filename extension and limited byte sniffing for PNG, JPEG, PDF, JSON, and plain text.

Use filenames with meaningful extensions when constructing `FileBytes`; without a filename, generic bytes can become `application/octet-stream` and may be filtered as unsupported.

## URL Rules

`FileUrl` accepts only `http://` and `https://` URLs. It guesses MIME type from the URL path until the content is fetched. Providers that support URL references can receive the URL without local network fetch; unsupported URL paths may require fetching bytes during resolution.

Important Bedrock caveat: even though Bedrock constraints record URL-style support for S3, ordinary HTTP(S) `FileUrl` sources are not passed as direct URL references for Bedrock. The resolver reads the URL content unless an uploader/S3 path is configured. Do not validate Bedrock remote URLs in no-network workflows unless you intentionally skip content resolution.

## Input Placement

CrewAI accepts file mappings in multiple places:

```python
task = Task(
    description="Analyze {chart} and compare it with {report}.",
    expected_output="A concise cross-file summary.",
    agent=analyst,
    input_files={
        "chart": ImageFile(source="chart.png"),
        "report": PDFFile(source="report.pdf"),
    },
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff(
    inputs={"topic": "Q4 revenue"},
    input_files={"shared_notes": TextFile(source="notes.md")},
)
```

File keys are the prompt placeholders and storage names. Keep keys short, stable, and descriptive: `chart`, `report`, `screenshot`, `audio_sample`, `policy_pdf`.

## Precedence and Storage

During crew kickoff, CrewAI merges file inputs from several scopes:

1. Flow-provided file baggage, when a flow invokes a crew.
2. `Crew.kickoff(..., input_files={...})` crew-scoped files.
3. File objects unpacked from the ordinary `inputs` mapping.
4. `Task(input_files={...})` task-scoped files when a task runs.

Task files override crew files with the same key. Crew and task files are stored in an in-memory `aiocache` file store with a default TTL of 3600 seconds.

## Native Payload Versus Tool Fallback

When an agent's LLM supports multimodal inputs, CrewAI converts supported files into provider-specific content blocks and attaches them to messages. Unsupported file content types are not silently forced into the LLM payload; the crew can add a `ReadFileTool` for files that are present but not natively supported by that LLM/provider combination.

When an LLM implementation receives files but reports no multimodal support, it raises an error saying the model does not support multimodal input and files were provided via `input_files`. In crew task execution, unsupported file types can instead be exposed through file tools depending on the execution path and agent/tool setup.

## JSON Project Notes

JSON project task definitions can include `input_files` as an object mapping names to strings or file specs. Local strings are resolved relative to the project root; HTTP(S) URLs are preserved; `file://` URIs must point to local project paths and remote `file://host/...` URIs are rejected.

## Multimodal Flag Migration

`Agent(multimodal=True)` still exists but is marked deprecated in the current runtime metadata: native files should be passed with `input_files` for direct model payloads. `multimodal=True` injects legacy image tooling when the underlying LLM is not a native multimodal `BaseLLM`. Use it when the task intentionally relies on the image tool path; otherwise prefer explicit `input_files` and a provider/model that supports the desired file type.

## Minimal Safe Pattern

```python
from crewai import Agent, Crew, LLM, Task
from crewai_files import ImageFile, PDFFile

llm = LLM(model="openai/gpt-4o-mini", api="responses")
analyst = Agent(
    role="File Analyst",
    goal="Extract accurate findings from supplied files",
    backstory="Careful analyst that cites only provided material.",
    llm=llm,
)
task = Task(
    description="Summarize {chart} and {report}; do not infer missing data.",
    expected_output="Three grounded bullets.",
    agent=analyst,
    input_files={
        "chart": ImageFile(source="chart.png"),
        "report": PDFFile(source="report.pdf", mode="strict"),
    },
)
crew = Crew(agents=[analyst], tasks=[task])
# Real kickoff calls an LLM; validate files first in no-network/debug contexts.
```

## File Tool Adjacency

Use native `crewai-files` when a model should directly see image/PDF/audio/video/text payloads. Use sibling [tools-and-mcp](../../tools-and-mcp/SKILL.md) for `FileReadTool`, `DirectoryReadTool`, `FileWriterTool`, `PDFSearchTool`, `DOCXSearchTool`, `JSONSearchTool`, `CSVSearchTool`, `TXTSearchTool`, `MDXSearchTool`, `DirectorySearchTool`, `OCRTool`, or custom tools. Use sibling [memory-knowledge-and-rag](../../memory-knowledge-and-rag/SKILL.md) for loaders, chunking for retrieval, embeddings, and vector store search.
