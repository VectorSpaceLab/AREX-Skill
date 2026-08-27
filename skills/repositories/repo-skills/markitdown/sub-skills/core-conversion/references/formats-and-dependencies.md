# Formats and Dependencies

## Built-In Converter Families

MarkItDown registers built-in converters by default. The broad built-in coverage includes:

- Text-like content: plain text, HTML, RSS/XML feeds, CSV, notebooks, Bing SERP pages, Wikipedia pages, and YouTube pages/transcripts.
- Office documents: DOCX, XLSX, legacy XLS, PPTX, and Outlook `.msg` files.
- Documents and books: PDF and EPUB.
- Media: images and audio.
- Archives: ZIP, with recursive conversion through the same `MarkItDown` instance.
- Optional cloud converters: Document Intelligence and Azure Content Understanding when configured; route these to `../cloud-integrations/SKILL.md`.

Converters decide acceptance from `StreamInfo` fields, content detection, URL patterns, filenames, and MIME types. Generic plain text, HTML, and ZIP converters run at lower priority than more specific converters, so a recognized specialized format gets first chance.

## Optional Extras

The base package includes common dependencies such as `beautifulsoup4`, `requests`, `markdownify`, `magika`, `charset-normalizer`, and `defusedxml`. Some formats require extras:

| Extra | Enables | Key Dependencies |
| --- | --- | --- |
| `markitdown[pptx]` | PowerPoint `.pptx` conversion | `python-pptx` |
| `markitdown[docx]` | Word `.docx` conversion | `mammoth`, `lxml` |
| `markitdown[xlsx]` | Excel `.xlsx` conversion | `pandas`, `openpyxl` |
| `markitdown[xls]` | Legacy Excel `.xls` conversion | `pandas`, `xlrd` |
| `markitdown[pdf]` | PDF conversion | `pdfminer.six`, `pdfplumber` |
| `markitdown[outlook]` | Outlook `.msg` conversion | `olefile` |
| `markitdown[audio-transcription]` | WAV/MP3 audio transcription | `pydub`, `SpeechRecognition` |
| `markitdown[youtube-transcription]` | YouTube transcript fetching | `youtube-transcript-api` |
| `markitdown[az-doc-intel]` | Azure Document Intelligence conversion | `azure-ai-documentintelligence`, `azure-identity` |
| `markitdown[az-content-understanding]` | Azure Content Understanding conversion | `azure-ai-contentunderstanding`, `azure-identity` |
| `markitdown[all]` | All optional built-in extras | All optional dependencies above |

When a converter recognizes a format but its optional dependency is absent, it raises `MissingDependencyException` with an install suggestion such as `pip install markitdown[pdf]` or `pip install markitdown[all]`.

## Format Notes

- PDF conversion uses PDF-focused dependencies when installed and includes table-oriented extraction paths. Scanned-image PDFs still need OCR or cloud conversion; route OCR plugin work to `../ocr-plugin/SKILL.md`.
- ZIP conversion recursively calls MarkItDown for archive members, so nested unsupported formats can surface as nested conversion failures.
- Image conversion can include metadata and can use `llm_client`, `llm_model`, and optional `llm_prompt` for image descriptions when the caller intentionally supplies a model client.
- PPTX conversion can also use the LLM image-caption kwargs for image descriptions in slides.
- Audio conversion may require system audio tooling through dependencies; see troubleshooting for `ffmpeg` or `avconv` warnings.
- Video is not covered by built-in offline conversion; Azure Content Understanding may support video and belongs in `../cloud-integrations/SKILL.md`.
- OCR over embedded images is plugin functionality, not core conversion; route to `../ocr-plugin/SKILL.md`.

## Choosing Hints

For unknown bytes, provide as many truthful hints as are available:

```python
StreamInfo(extension=".csv", mimetype="text/csv", charset="utf-8")
```

Use `extension` when the format is known from an upload filename, `mimetype` when it comes from an HTTP header or content registry, and `charset` when text decoding must be deterministic.
