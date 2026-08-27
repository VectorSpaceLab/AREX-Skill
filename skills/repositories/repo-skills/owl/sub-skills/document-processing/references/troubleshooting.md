# Document Processing Troubleshooting

## Constructor raises a missing OpenAI key error

**Symptom:** a missing `OPENAI_API_KEY`/default model error appears before a
local JSON/Python call. **Cause:** construction creates an image-analysis
sub-tool and the current CAMEL runtime builds a default provider backend when
no model is supplied. **Recovery:** configure and pass an explicit model for a
real task, or use `probe_document_input.py` for offline classification. Do not
fake a production API key or assume a local extension avoids constructor setup.

## JSON/JSONL or XML parse surprise

**Symptom:** JSON raises a decode error, or XML returns plain text instead of a
mapping. **Recovery:** validate UTF-8 and JSON document structure first. The
current `.jsonl` branch uses `json.load`, so normalize a multi-record JSONL file
or process it line by line outside this method. XML parse failure intentionally
falls back to raw text; check the returned type before downstream reasoning.

## Web extraction returns error/no content

**Symptom:** a string reports webpage extraction error or no content. **Cause:**
network, content type, redirects, authentication, Firecrawl credentials, or
Crawl4AI/browser setup. **Recovery:** confirm a public URL, check the chosen
service key, use an approved browser setup, and record a skipped/blocked page
rather than inventing its content. Do not retry private/authenticated URLs
without authorization.

## Image or spreadsheet fails

**Symptom:** model capability, parser, or format error. **Recovery:** choose a
vision-capable configured model for images; verify that the file is actually
XLS/XLSX for the Excel route; route CSV/text through a suitable parser or code
worker instead. Provider configuration belongs in
[workforce-workflows](../../workforce-workflows/SKILL.md).

## ZIP extraction fails or writes unexpected files

**Symptom:** `unzip` command not found, archive error, or unexpected cache
contents. **Recovery:** check archive integrity and the `unzip` executable,
set a dedicated cache directory, inspect the returned file list, and do not
extract untrusted archives into a production location. The `-o` behavior can
overwrite names within the selected cache.

## General parser failure

**Symptom:** `UnstructuredIO.parse_file_or_url` returns no elements or raises.
**Recovery:** confirm the path, file type, parser dependencies, and size; try a
small representative input; then provide an alternate extraction route. A false
success flag or error string must stop downstream use of the content.
