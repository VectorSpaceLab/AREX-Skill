# RAG application troubleshooting

Diagnose from stage boundaries: **preflight → load → parse → chunk → metadata →
build → retrieve → chat**. Preserve the source and failed staging artifacts.
Never respond to a private/live/heavy failure by exporting data, opening a
store, starting a service, installing a dependency, downloading a model, or
printing credentials without separate authorization.

## Fast triage

1. Record source family, platform, public command/API surface, dependency set,
   and expected item/chunk count.
2. Reproduce on the smallest approved non-sensitive fixture when possible.
3. Compare discovered, loaded, skipped, failed, chunked, and indexed counts.
4. Inspect one redacted passage and its metadata before changing retrieval.
5. Stop if there are no chunks. Do not let a zero-corpus build appear healthy.
6. Route index/backend faults to backends and storage, provider/model faults to
   embeddings and chat, and MCP transport/server faults to MCP and services.

## Failure matrix

| Symptom | Likely cause | Safe diagnosis | Corrective action |
|---|---|---|---|
| Source path rejected | Missing path, wrong path type, or unsupported platform | Check platform first, then path existence/type without listing contents | Supply an approved file/directory on a supported platform |
| “No files found” | Extension allowlist mismatch, hidden paths, `.gitignore`, wrong root, or empty corpus | Compare intended extensions and ignore policy; inspect only an approved fixture | Normalize extensions, narrow/fix root, or adjust ignore policy explicitly |
| PDF produces no text | Empty, scanned, encrypted, corrupt, or unsupported parser | Check file size/type and parser result on one approved PDF | Use visual-PDF only when justified; otherwise repair/replace input |
| Document parser import error | Optional LlamaIndex file reader missing | Identify the extension and missing reader without installing it | Add the minimum approved reader dependency or exclude that type |
| Garbled/duplicate email body | Malformed MIME, encoding issue, or both HTML and text alternatives indexed | Compare parsed MIME parts and failure counts on a synthetic `.emlx` | Decode with error policy; choose text or sanitized HTML, not both |
| WeChat JSON fails | Top level is not an array, records are malformed, or expected message fields differ | Validate JSON structure against a synthetic export; do not inspect unrelated exports | Repair/convert the approved export; count malformed records |
| Browser database locked | Browser holds the SQLite store or permission is denied | Confirm process/permission state without copying history | Close browser or grant approved read access; do not modify the store |
| Browser history missing | Public CLI expects a macOS default Chrome/Brave profile | Check platform and documented default profile | Use the supported default or a separately reviewed custom loader |
| Apple Mail/Calendar/iMessage missing | Non-macOS host, Full Disk Access absent, store moved, or schema changed | Reject non-macOS first; verify expected store exists without opening it during planning | Run only on authorized macOS host; adapt loader after schema review |
| Calendar query/schema error | `Calendar Cache` schema differs or copied database is invalid | Reproduce against a synthetic SQLite fixture with expected columns | Update the authorized reader; never write the source cache |
| iMessage returns zero rows | `chat.db` missing, no text rows, permission denied, or schema mismatch | Separate existence, permission, SQL, and empty-text outcomes | Correct access/path or adapt query; keep attachment-only rows excluded |
| `astchunk` unavailable | Optional import missing | Use a synthetic supported code file and observe strategy/count | Keep traditional fallback; install only when separately approved |
| AST parser fails one file | Invalid syntax, unsupported grammar, missing language metadata, or parser defect | Compare extension/language and fallback output | Use traditional fallback for that file and preserve source metadata |
| Code chunk lacks line metadata | Traditional fallback occurred or AST output omitted line fields | Check strategy and sampled metadata | Do not fabricate line numbers; route citations to file-level identity |
| Empty/whitespace chunks | Empty input or parser emitted unusable chunks | Assert `text.strip()` for every passage | Drop and count empties; fail if all passages are empty |
| Chunk overlap error | Overlap is negative or at least the size | Validate numeric relationships before building | Require `size > 0` and `0 <= overlap < size` |
| Embedding input too long | Unit confusion or size+overlap exceeds model limit | Record whether size is tokens or AST characters and estimate final budget | Reduce size/overlap; validate against the chosen embedding model |
| Metadata filter returns zero | Field absent, wrong type/name, unsupported operator, or too few retrieved candidates | Inspect stored metadata for known fixtures; test include/exclude cases | Rebuild with consistent schema or correct filter; increase candidate count if justified |
| Chunk text and metadata disagree | Metadata lost/reused during splitting or vector/order mismatch | Compare sampled source identity, line/page/date, ID, and vector order | Recreate passages deterministically and rebuild staged index |
| Relative-time search is unstable | Wall clock not injected, timezone differs, or month/year approximation hidden | Test parser with fixed `now` and timezone | Inject clock/timezone and disclose 30/365-day approximation |
| Spotlight semantic-file recipe fails | Non-macOS host, missing permissions, invalid scopes, or no indexed Spotlight results | Keep collection reference-only; validate a synthetic manifest instead | Use authorized macOS collection or another manifest source |
| MCP server unavailable | Command missing, process exits, stdio unavailable, or initialization fails | Do not start it here; confirm command and server ownership out of band | Route installation/transport to MCP and services |
| MCP lists no compatible tool | Tool names/schema differ from reader assumptions | Review `tools/list` schema from an authorized test-connection result | Adapt reader to exact tool contract; do not guess tool arguments |
| Slack returns cache-sync error | Server user cache still synchronizing | Distinguish the known sync message from authentication errors | Use bounded exponential backoff; stop after configured retries |
| Slack channel empty/denied | Wrong name/ID, bot not in channel, insufficient scopes, or date window limit | Check access and server result out of band | Correct channel/access; never broaden to all channels silently |
| Slack CSV rows skipped | Header/column layout differs or quoting is malformed | Test parser on a synthetic CSV fixture with quoted commas/newlines | Adapt parser to documented server schema and count bad rows |
| Twitter/X returns no bookmarks | Empty account, wrong username filter, auth failure, tool mismatch, or rate limit | Keep causes separate from true empty results | Correct approved scope/server; honor rate limits and bounds |
| Image directory yields zero | Extension case/list mismatch, corrupt images, or all decodes failed | Compare discovery and decode counts on synthetic images | Normalize extensions; count failures; fail if no successful image |
| Image/vector alignment error | Failed images changed ordering or IDs do not match vectors | Assert equal counts, unique IDs, dimensions, finite values, and order | Rebuild passage/vector arrays together; never truncate one side |
| CLIP search behaves like filename search | Query used a non-CLIP encoder or vectors were not precomputed correctly | Verify matching CLIP image/text towers and normalized vectors | Rebuild/query with the same CLIP model and cosine semantics |
| `pdf2image`/Poppler error | `pdfinfo`/`pdftoppm` absent from `PATH` | Record missing executable without installing it | Block until an approved system dependency is available |
| Visual PDF converts zero pages | Poppler missing or all PDFs corrupt/encrypted/empty | Reconcile per-PDF conversion failures | Replace/repair input or satisfy approved Poppler prerequisite |
| ColQwen/ColPali import/version error | Missing `colpali_engine` stack or Transformers 5.x | Record package versions; do not mutate environment | Use a reviewed environment with compatible Transformers 4.x |
| Model not cached | First use would download a large model | Probe cache/config without network access | Block until user approves cache population/download elsewhere |
| CUDA/MPS out of memory or NaNs | Corpus/batch too large or dtype/device issue | Stop the job; record device/dtype/batch/page count | Reduce bounded workload; MPS should use float32; make CPU fallback explicit |
| Visual PDF result has only doc ID | ID-to-page metadata map was not persisted/reloaded | Validate join artifact after reopen | Rebuild with durable ID→PDF/page mapping before citing results |
| “Ask” returns retrieval only | Visual-PDF app does not implement answer generation | Inspect output contract | Label it retrieval; add a separately approved vision LLM stage if needed |
| Chat answer is poor but search is good | Prompt/provider/context issue | Preserve known-good retrieval evidence | Route to embeddings and chat; do not rebuild corpus reflexively |

## Parser fixtures

Use synthetic, non-sensitive fixtures for difficult parser failures:

- a `.emlx` with length prefix, multipart text/plain + HTML, and one malformed
  payload;
- a WeChat JSON array with valid text, non-text XML, missing fields, and one
  non-dictionary record;
- Slack CSV with header, quoted comma, empty line, short row, and timestamp;
- a tiny iMessage-like SQLite database matching only the required tables;
- one valid and one invalid Python file plus Markdown to prove AST/traditional
  dispatch and fallback;
- two tiny RGB images plus one corrupt file;
- one one-page valid PDF plus an empty/corrupt PDF.

Fixtures must contain invented data only.

## Escalation record

When unresolved, hand off:

- exact stage and source family;
- platform and approved dependency state;
- command generated (with secrets absent), not private output;
- expected vs observed counts;
- synthetic reproduction and assertion;
- whether fallback ran;
- metadata schema and failing field/type;
- optional/heavy/backend/provider/MCP boundary owner;
- what was deliberately not accessed or executed.
