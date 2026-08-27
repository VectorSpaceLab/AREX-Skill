# Docling CLI Troubleshooting

## CLI Command Missing or Startup Import Error

Symptoms:

- `docling: command not found`.
- Error mentions missing `typer`, `rich`, or CLI dependencies.

Actions:

- Install the full package: `pip install docling`.
- For slim installs, include CLI support: `pip install 'docling-slim[cli]'`.
- Confirm the environment running the command is the same environment where Docling was installed.

Some converter imports require model foundation dependencies even when the CLI itself starts. If a pipeline/backend import fails, install the relevant full package or extras for the requested feature.

## Unsupported Input or Output Combination

Symptoms:

- The command accepts the flags but produces no useful content.
- A format enum or option is rejected by the installed version.
- A directory conversion skips files you expected to convert.

Actions:

- Check spelling against CLI enum names such as `md`, `json`, `html_split_page`, `doclang`, `pdf`, `docx`, `html`, and `audio`.
- Use repeated flags, not comma-separated values: `--to md --to json`, `--from pdf --from docx`.
- For directories, remember `--from` filters files by supported extensions; add every input type expected in the tree.
- If generated docs and installed behavior differ, trust `docling --help` / `docling convert --help` in the active environment.

## Image Export Confusion

Symptoms:

- Markdown contains base64 images but the user expected separate files.
- Markdown/HTML says an image is unavailable.
- `--image-export-mode` appears ignored for `text`, `doctags`, `vtt`, or `doclang`.

Actions:

- Use `--image-export-mode referenced` to write image files and references for image-capable outputs.
- Use `--image-export-mode embedded` to keep images in the main Markdown/HTML/JSON/YAML output.
- Use `--image-export-mode placeholder` when image payloads are not needed.
- Do not expect image export in `text`, `doctags`, `vtt`, or `doclang`; those output formats do not export images.
- For HTML/EPUB sources, also choose `--html-image-fetch local`, `remote`, or `all`; image export mode alone does not grant permission to fetch referenced HTML resources.

## HTML/EPUB Image Fetch Risk

Symptoms:

- Remote HTML images are missing.
- The CLI rejects `--html-image-headers`.
- Security review asks why the command contacts third-party image URLs.

Actions:

- Default `--html-image-fetch none` avoids fetching HTML/EPUB image resources.
- Use `local` for trusted local assets bundled near an HTML/EPUB source.
- Use `remote` or `all` only when outbound remote image fetches are acceptable.
- `--html-image-headers` requires `--html-image-fetch remote` or `all`; source URL headers belong in `--headers`.
- Avoid passing secrets to remote image hosts unless the image endpoint is trusted and intended.

## Directory Filtering Surprises

Symptoms:

- A mixed folder converts fewer files than expected.
- Temporary Office lock files appear in logs or are skipped.
- Uppercase or mixed-case extensions behave differently than expected.

Actions:

- Add explicit repeated `--from` values for every desired input type.
- Docling walks directories recursively and filters by supported extensions.
- Extension matching is case-insensitive.
- Temporary Word files with names like `~$example.docx` are ignored intentionally.

## No Output or Empty Outputs

Symptoms:

- The output directory exists but expected files are missing.
- Markdown is empty and the command reports a failure.
- Files were written to an unexpected location.

Actions:

- Always pass `--output DIR` in automation.
- Confirm `--to` includes the output the user expects; default is only `md`.
- Increase logs with `-v` or `-vv`.
- For batch work, decide whether `--abort-on-error` should stop on the first failed document or continue converting the rest.
- For empty Markdown, try a lossless `--to json` output to inspect whether conversion produced document content but Markdown export failed or had no textual content.

## Model Downloads and Offline Use

Symptoms:

- First conversion run downloads model artifacts.
- Air-gapped or CI execution fails while trying to fetch models.

Actions:

- Prefetch models with `docling-tools models download` before offline execution.
- Use `docling-tools models download --all --output-dir DIR` when the environment needs a broad local cache.
- Pass the chosen artifacts/model directory through the appropriate Docling option when configuring local model use.
- Do not assume models are available just because the Python package imports.

## ASR, VLM, and Advanced Backend Requirements

Symptoms:

- Audio/video conversion fails.
- VLM pipeline complains about model, backend, GPU, MLX, API, or remote-service settings.
- Advanced enrichment flags trigger missing dependency or remote-service errors.

Actions:

- For audio/video, install ASR support such as `docling[asr]` and ensure `ffmpeg` is available when needed.
- For VLM work, expect model downloads and possible GPU/MLX/API requirements depending on the chosen preset.
- For remote-service-backed internals, pass `--enable-remote-services`; otherwise Docling intentionally blocks remote model calls from pipeline internals.
- If the user is converting through a docling-serve endpoint rather than using local pipeline internals, route to the remote-service-client sub-skill.

## WebVTT Does Not Match Markdown

Symptoms:

- User asks why `--to vtt` output is shorter, cue-based, or lacks Markdown structure.

Explanation:

- WebVTT is a timed-caption format; Markdown is a structured document text format.
- `vtt` does not export images, tables as Markdown, or general document formatting.
- For ordinary documents, prefer `md` or `json`; for captions/transcripts, use `vtt` and confirm an ASR/timed-text path exists.
