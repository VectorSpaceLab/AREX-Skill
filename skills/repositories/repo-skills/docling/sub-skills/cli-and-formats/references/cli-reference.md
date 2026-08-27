# Docling CLI Reference

Docling exposes a local `docling` command and a `docling-tools` command. The local conversion path is the responsibility of this sub-skill. Remote conversion through `docling convert-remote` is intentionally out of scope except to route agents to the remote-service-client sub-skill.

## Install and Entry Points

- Full install: `pip install docling` provides the local CLI and the standard model dependencies expected by most users.
- Slim CLI install: `pip install 'docling-slim[cli]'` provides CLI dependencies for the slim package; additional extras may still be needed for ASR, VLM, or advanced backends.
- Python support: installed package facts indicate Python `>=3.10,<4`.
- Entry points: `docling` for conversion and `docling-tools` for helper commands.

If `docling` fails at startup with missing `typer` or `rich`, install the full package or the slim package with the `cli` extra.

## Local Convert Command Anatomy

The current local command accepts one or more sources:

```bash
docling SOURCE [SOURCE ...] --output out --to md --to json --from pdf --from docx
```

A bare `docling SOURCE` invocation routes to local conversion. `docling convert SOURCE` is equivalent when the command group exposes the explicit subcommand.

Important local flags:

| Flag | Use |
| --- | --- |
| `--from FORMAT` | Repeatable input allow-list; also filters directory traversal. Defaults to all supported input formats. |
| `--to FORMAT` | Repeatable output selection. Defaults to `md`. |
| `--output DIR` | Output directory. Defaults to the current directory. |
| `--headers JSON` | HTTP headers for fetching URL input sources. |
| `--image-export-mode placeholder|embedded|referenced` | Controls images in image-capable outputs. Defaults to `embedded`. |
| `--html-image-fetch none|local|remote|all` | Fetch image resources referenced by HTML/EPUB inputs. Defaults to `none`. |
| `--html-image-headers JSON` | Headers for remote HTML/EPUB image resource fetches; requires `--html-image-fetch remote` or `all`. |
| `--ocr` / `--no-ocr` | Enable or disable bitmap OCR. Defaults to enabled. |
| `--force-ocr` / `--no-force-ocr` | Replace existing text with OCR output. Defaults to disabled. |
| `--tables` / `--no-tables` | Enable or disable table structure extraction. Defaults to enabled. |
| `--pipeline legacy|standard|vlm|asr` | Select local processing pipeline. Defaults to `standard`. |
| `--vlm-model NAME` | VLM preset when using `--pipeline vlm`; default is `granite_docling`. |
| `--asr-model NAME` | Whisper ASR preset when using audio/video inputs or ASR pipeline. |
| `--device auto|cpu|cuda|mps|xpu` | Accelerator device for local model work. |
| `--num-threads N` | Local thread count; default help shows `4`. |
| `--document-timeout SECONDS` | Per-document processing timeout. |
| `--abort-on-error` | Abort batch on first conversion error. |
| `--verbose` / `-v` | Increase logging; repeat for debug. |

Pipeline/backends flags such as `--pdf-backend`, `--table-mode`, `--artifacts-path`, enrichment flags, debug visualizers, and profiling flags are local execution controls. When the user asks about remote execution, switch to the remote-service-client sub-skill instead of extending local commands with service-client flags.

## Common Local Recipes

Convert a single PDF to Markdown in `out`:

```bash
docling report.pdf --output out --to md
```

Convert a mixed directory, accepting only PDFs and DOCX files, and emit Markdown plus JSON:

```bash
docling inbox --from pdf --from docx --to md --to json --output out
```

Convert trusted local HTML with local images embedded in Markdown:

```bash
docling page.html --from html --to md --output out --html-image-fetch local --image-export-mode embedded
```

Convert HTML and write referenced image files instead of base64:

```bash
docling page.html --from html --to md --output out --html-image-fetch local --image-export-mode referenced
```

Disable OCR and table extraction for fast text-native files:

```bash
docling docs --from docx --from md --to md --output out --no-ocr --no-tables
```

Use a local VLM preset for PDF/image conversion:

```bash
docling scan.pdf --pipeline vlm --vlm-model granite_docling --device auto --output out
```

Use ASR for audio/video when the ASR extra and `ffmpeg` are available:

```bash
docling meeting.mp3 --pipeline asr --to vtt --output transcripts
```

## Directory and URL Behavior

- Directories are walked recursively and filtered by the selected `--from` formats.
- Extension matching is case-insensitive; temporary Word files named like `~$file.docx` are ignored.
- Local paths are converted locally. HTTP(S) sources are fetched for local conversion unless the user is using the remote conversion command.
- For HTML URLs, `--html-image-fetch remote` or `all` allows fetching referenced remote images. Treat this as a network and trust-boundary decision.
- `--headers` applies to URL source fetching; `--html-image-headers` applies to remote image-resource fetching and requires remote/all image fetch mode.

## Output Behavior

Default output is Markdown (`.md`). Repeated `--to` writes one file per selected export where possible:

- `md`: Markdown, `.md`.
- `json`: lossless Docling document JSON, `.json`.
- `yaml`: lossless Docling document YAML, `.yaml`.
- `html`: HTML, `.html`.
- `html_split_page`: split-page HTML, `.html`-style output.
- `text`: strict text, `.txt`.
- `doctags`: DocTags, `.doctags`.
- `vtt`: WebVTT captions, `.vtt`.
- `doclang`: DocLang XML, `.dclg.xml`.

Image export modes affect only image-capable outputs: Markdown, JSON, YAML, HTML, and split-page HTML. Text, DocTags, WebVTT, and DocLang do not export embedded or referenced images.

## `docling-tools` Awareness

`docling-tools models download` prefetches known Docling model artifacts. This is useful for air-gapped work or avoiding first-use downloads. It accepts optional model names and `--all`, `--force`, `--output-dir`, and `--quiet`.

Examples:

```bash
docling-tools models download --all --output-dir ./models
```

```bash
docling-tools models download layout tableformer easyocr --output-dir ./models
```

`docling-tools models download-hf-repo MODEL_ID...` downloads specific Hugging Face repos to an output directory. Do not assume a model is already present; if the user needs offline execution, prefetch explicitly and then pass the resulting directory through the appropriate Docling model/artifacts option.
