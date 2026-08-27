# Personal and live-data RAG

Personal sources require a stricter gate than ordinary documents. Planning may
check the operating-system name and whether a user-supplied path exists; it must
not open a profile, mail store, database, export, credential file, or MCP
connection. Execution requires separate user authorization.

## Source matrix

| Source | Supported input | Platform / access prerequisite | Passage shape and metadata | Safe public command surface |
|---|---|---|---|---|
| Chrome/Brave history | Default browser `History` SQLite store | `leann index-browser` uses macOS default profile paths; browser should be closed if the store is locked | Text includes title, URL, visit time/counts; structured `title`, `url`, `domain`, `last_visited`, `visit_count`, `typed_count` | `leann index-browser chrome|brave` |
| Apple Mail | `.emlx` files under Mail `Messages` directories | macOS; terminal may need Full Disk Access | Text headers include file/from/to/subject/date/body; the current reader emits empty structured metadata | `leann index-email` |
| Apple Calendar | `Calendar Cache` SQLite store | macOS; Full Disk Access may be needed | Event text includes start/end/location/description; metadata contains `event` and `start` | `leann index-calendar` |
| iMessage | `chat.db` in the Messages directory | macOS; Full Disk Access; database schema must match | Conversation mode: `source`, chat identity, count, first/last date, participants; individual mode also has message timestamp/sender fields | `leann index-imessage` |
| WeChat | Existing directory of per-contact JSON exports | Any platform for reading an existing export; exporting is out of scope | Text contains contact/time/sender; structured metadata currently preserves `contact_name` | `leann index-wechat --export-dir DIR` |
| Slack | Live MCP server output | Server command installed; workspace authorization/scopes and channel access configured out of band | Formatted text contains workspace/channel/user/time/message; app adapter metadata only guarantees `source: slack` | Reference-only in this sub-skill |
| Twitter/X | Live MCP server output | Server command installed; bookmark access, authentication, network/rate-limit policy configured out of band | Formatted text may contain author/date/content/URL/engagement; app adapter metadata only guarantees `source: twitter` | Reference-only in this sub-skill |

## Private local-source workflow

1. Obtain explicit permission for the named source and index destination.
2. Reject an unsupported platform **before** checking the private path. The
   bundled planner follows this order for browser, mail, calendar, and iMessage.
3. Confirm that the default platform store exists, or that a supplied WeChat
   export path exists and is a directory. Do not enumerate or sample records
   during planning.
4. Start with a small positive `--max-count`. Use a separate index name that
   does not reveal sensitive account or contact names.
5. After authorized execution, compare loaded, parsed, failed, and emitted
   document counts. Stop on zero documents or unexpectedly high parser failure.
6. Inspect a redacted sample for header/body boundaries, timestamp validity,
   conversation grouping, and metadata/text agreement.
7. Search with a narrow known-answer query. Show metadata only in a trusted
   terminal and avoid copying private results into logs or reports.

The planner only prints commands:

```bash
python scripts/build_rag_command.py personal browser \
  --index browser-history --browser chrome --max-count 100 \
  --ack-private-data

python scripts/build_rag_command.py personal wechat \
  --index wechat-history --source ./approved-export --max-count 100 \
  --ack-private-data
```

It never opens a store or export and never executes `leann`.

## Per-source validation

### Browser history

- Verify the selected browser and profile policy. The public command indexes the
  default Chrome or Brave profile on macOS; it does not accept a custom profile.
- A missing profile, absent `History` file, locked database, or schema error
  must fail as no data, not produce an empty successful index.
- `last_visited` is a local-time string. Keep `visit_count` and `typed_count` as
  integers if filtering on them.

### Apple Mail

- Validate `.emlx` structure: a length prefix line followed by RFC-style email
  content. Malformed MIME, undecodable payloads, and HTML-only messages can
  reduce the emitted count.
- HTML is excluded by the app-derived reader unless explicitly enabled in a
  custom flow. Avoid indexing both HTML and text alternatives as duplicates.
- Sender, recipient, subject, and date are embedded in text, not structured
  metadata. Do not issue metadata filters for those fields without a custom
  loader and a rebuild.

### Apple Calendar

- The public reader copies the cache to a temporary file before querying
  `CI_EVENT`; it does not modify the original store.
- Validate event summary, local-time start/end conversion, and empty optional
  location/description handling. The structured `start` field is a string.
- Calendar data is platform-private even if only event summaries are indexed.

### iMessage

- The app-derived reader accepts either the default Messages directory or a
  directory containing `chat.db`; a custom path to the file is converted to its
  parent directory.
- Concatenated mode groups all text messages by chat and preserves first/last
  dates and participant list. Individual mode preserves per-message timestamp,
  sender direction, contact, and service.
- Exclude attachment-only/empty text rows. Check timestamp conversion and
  database schema errors before trusting conversation counts.

### WeChat exports

- Input must be an existing directory containing JSON arrays. Each message may
  use `content`, `message`, `createTime`, `fromUser`, `toUser`, and
  `isSentFromSelf`; malformed files or non-dictionary entries are parser errors.
- The reader can group readable text messages by maximum length and time window.
  The app-derived RAG path uses concatenation for context.
- Do not invoke automatic export, modify a WeChat client, install exporter
  requirements, or search common directories. Require the exact approved
  export path.

## Live MCP readers: reference-only composition

Slack and Twitter/X application readers start a user-supplied server command as
a subprocess, initialize JSON-RPC over stdio, list tools, call a selected tool,
format returned records, and stop the subprocess. That behavior is not a public
`leann index-*` package command, so this skill does not synthesize or execute a
live command. Route protocol/server work to MCP and services.

### Slack preflight

- Confirm the server executable and arguments without starting it.
- Confirm required workspace/channel permissions out of band. Private channels
  require explicit access; names and IDs are server-specific.
- The reader prefers a `conversations_history` tool, then tool names containing
  `conversations_search`, `message`, or `history`. A server without such a tool
  is incompatible.
- Responses may be JSON or a CSV text payload. CSV requires at least seven
  columns; malformed rows are skipped. Cache-sync errors may be retried with
  exponential backoff by the reader, but authentication and permission errors
  should not be retried blindly.
- Conversation mode sorts numeric timestamps, limits messages, and groups by
  channel. Validate channel, workspace, user, timestamp, and body in a redacted
  sample before indexing.

### Twitter/X preflight

- Confirm a bookmark-fetching MCP tool, account access, and the maximum bookmark
  limit without connecting in this skill.
- Decide whether tweet content and engagement metadata are allowed. Disabling
  metadata should remove likes/retweets/replies from formatted text.
- Validate ISO timestamps, author, URL, content, and optional hashtags/mentions.
  Treat rate limits, empty bookmarks, and username mismatch as distinct causes.

## Metadata and time search

Metadata filters only work on structured fields, not labels embedded in passage
text. For example, browser `domain` and numeric visit counts are filterable;
Apple Mail `Subject` is not filterable without custom metadata. Slack channel
and Twitter author are formatted text in the app-derived adapters, not
structured fields.

Use ISO-8601 date strings consistently if lexical range comparison is intended.
For natural-language phrases such as “about 2 weeks ago,” parse the time phrase
into a date range, remove it from the semantic query, retrieve a candidate set,
and filter candidates by `modification_date` or `creation_date`. Months and
years represented as fixed 30/365-day deltas are approximations; report that
limit and use an injected clock in tests.

## Acceptance checks

- Named source, platform, authorization, destination, and retention policy are
  explicit.
- Unsupported platforms fail before any private-path probe.
- Export/store/schema prerequisites are source-specific and verified without
  collection during planning.
- Loaded, failed, skipped, grouped, chunked, and indexed counts reconcile.
- Text and structured metadata have the documented fields and types.
- Live readers are bounded by channel/account/limit and remain reference-only.
- Logs, index names, commands, and reports contain no credentials or private
  sample content.
