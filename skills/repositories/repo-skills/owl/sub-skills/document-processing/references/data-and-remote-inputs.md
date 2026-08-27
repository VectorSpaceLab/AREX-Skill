# Input and Remote-Service Guide

## Decide the path before calling the toolkit

1. Is the input a local file or a URL? Run `probe_document_input.py`; it does
   no I/O beyond local existence checks.
2. Is a local extension explicitly handled? JSON/XML/Python and ZIP follow
   special code paths; spreadsheets/images delegate to CAMEL toolkits.
3. Does the input need a model, a parser, a network service, or a browser? Do
   not retry an operational error without supplying the missing prerequisite.
4. Does the task need a verbatim source, normalized text, or a structured
   object? The current toolkit returns different shapes for JSON/XML and text.

## Remote input paths

### Web pages

For a recognized webpage, the toolkit reads `FIRECRAWL_API_KEY`. If a key is
set, it initializes Firecrawl and requests one Markdown-format crawl result. If
no key is set, it logs a warning and tries Crawl4AI asynchronously. The
Crawl4AI path may need browser binaries and can fail on JavaScript, login,
robots, network, or sandbox constraints. Neither path should receive secrets in
a URL or be used for credentialed websites without authorization.

### Chunkr helper

The private `_extract_content_with_chunkr` helper creates a `Chunkr` client
from `CHUNKR_API_KEY`, uploads a document, then writes JSON or Markdown output
in the current process directory before reading it. It is not used by the main
dispatch method shown above. Use it only after confirming upload/data-retention
policy, and avoid treating its generated output filename as a stable API.

### Images and spreadsheets

Images call a model-backed image question method. Spreadsheet input delegates to
CAMEL's Excel toolkit. Both depend on the model/tool versions available in the
target runtime; a text-only provider or missing key cannot be repaired by
changing file extension.

## Safe input rules

- Reject a missing local path before instantiating a model-backed toolkit.
- Keep document caches and ZIP extraction roots outside source trees and shared
  system locations.
- Never execute extracted `.py` content merely because OWL returned it.
- Treat URL content type and redirected destinations as untrusted data.
- For JSONL, test a representative file; the implementation uses `json.load`,
  not a line-by-line parser.
- Log success/failure status and source identifier, but redact credentials and
  sensitive document text from shared logs.
