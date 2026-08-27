# Docling Format Guide

Use `--from` to choose input formats Docling should accept and `--to` to choose output formats Docling should write. Both flags are repeatable.

## CLI Input Format Names

Installed enum facts list these `InputFormat` values:

| CLI name | Typical files or use |
| --- | --- |
| `pdf` | PDF files. |
| `docx` | Microsoft Word Open XML documents. |
| `pptx` | Microsoft PowerPoint Open XML presentations. |
| `xlsx` | Microsoft Excel Open XML workbooks. |
| `html` | HTML/XHTML pages and URLs. |
| `image` | PNG, JPEG, TIFF, BMP, WEBP and similar image files. |
| `asciidoc` | AsciiDoc text documents. |
| `md` | Markdown and Markdown-like text inputs. |
| `csv` | CSV tabular input. |
| `xml_uspto` | USPTO patent XML. |
| `xml_jats` | JATS article XML. |
| `xml_xbrl` | XBRL financial-reporting XML. |
| `xml_doclang` | DocLang XML (`.dclg`, `.dclg.xml`). |
| `mets_gbs` | METS/GBS-style inputs. |
| `json_docling` | JSON-serialized Docling Document. |
| `audio` | Audio/video media for transcription; requires ASR support and usually `ffmpeg` for video/audio containers. |
| `vtt` | WebVTT timed text input. |
| `latex` | LaTeX documents. |
| `email` | Email inputs such as EML/MSG where available in the installed package. |
| `epub` | EPUB e-books where available in the installed package. |

When a generated CLI reference omits newer formats, prefer the installed enum facts and verify with `docling --help` or `docling convert --help` in the target environment.

## CLI Output Format Names

Installed enum facts list these `OutputFormat` values:

| CLI name | Output intent | Image export support |
| --- | --- | --- |
| `md` | Markdown for downstream text/LLM workflows. | Yes. |
| `json` | Lossless Docling document JSON. | Yes. |
| `yaml` | Lossless Docling document YAML. | Yes. |
| `html` | HTML document. | Yes. |
| `html_split_page` | Split-page HTML view. | Yes. |
| `text` | Plain text without Markdown markers. | No. |
| `doctags` | DocTags layout/content markup. | No. |
| `vtt` | WebVTT captions/timed text. | No. |
| `doclang` | DocLang XML. | No. |

Default output is `md` if no `--to` is supplied.

## Choosing `--from`

Use `--from` when:

- Converting a directory and you need predictable filtering.
- Avoiding accidental processing of unrelated files in a mixed folder.
- Working around ambiguous extensions or intentionally selecting HTML behavior for URLs.
- Reducing attempted backends and dependencies for a constrained environment.

Examples:

```bash
docling inbox --from pdf --from docx --to md --output out
```

```bash
docling page.html --from html --to md --html-image-fetch local --output out
```

If no `--from` is supplied, Docling accepts all supported input formats known to the installed version.

## Choosing `--to`

Use repeated `--to` flags for multiple artifacts from one conversion run:

```bash
docling report.pdf --to md --to json --to html --output out
```

Common choices:

- `md` for agent-friendly text with document structure.
- `json` or `yaml` for lossless DoclingDocument serialization.
- `html` or `html_split_page` for browser review.
- `text` for plain-text downstream systems that do not want Markdown syntax.
- `vtt` for captions/transcripts, especially from audio/video or WebVTT workflows.
- `doclang` for DocLang XML interchange.

## Image Modes and Fetch Modes

`--image-export-mode` controls how converted document images are represented in outputs that support images:

- `placeholder`: mark image positions only; does not export image payloads.
- `embedded`: embed images as base64 in the main output when the output format supports it.
- `referenced`: write PNG image files and reference them from the main output.

`--html-image-fetch` controls whether Docling fetches image resources referenced by HTML/EPUB inputs:

- `none`: do not fetch referenced HTML/EPUB images.
- `local`: allow local resource fetches only.
- `remote`: allow remote resource fetches only.
- `all`: allow local and remote resource fetches.

Use `--html-image-headers '{"Header":"value"}'` only with `remote` or `all`. Keep source-fetch headers (`--headers`) separate from image-resource headers (`--html-image-headers`).

## Why WebVTT Differs from Markdown

Markdown is a structural text export from a Docling document. WebVTT is a timed-text caption format and does not carry the same Markdown structure, tables, or image references. A user converting the same source to `--to md --to vtt` should expect different content shape: Markdown optimizes readable document structure; VTT optimizes cue timing and caption playback.

If a VTT output is sparse or unexpected, confirm the input has timed text or an ASR/transcription path. For ordinary PDFs/DOCX, Markdown is usually the correct output. For audio/video, install ASR support and ensure `ffmpeg` is available when container extraction is needed.

## Safe Mixed Directory Pattern

For a mixed directory requiring Markdown plus JSON and referenced images:

```bash
docling inbox --from pdf --from docx --from html --to md --to json --output out --image-export-mode referenced --html-image-fetch local
```

This filters the directory, writes both agent-friendly Markdown and lossless JSON, and avoids remote image fetches while preserving local HTML/EPUB assets as referenced files.
