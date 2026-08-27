# DeepXiv CLI reference

This reference describes the `deepxiv_sdk/cli.py` command group at package
version 1.0.0. The console entry point is `deepxiv=deepxiv_sdk.cli:main`.
Use `deepxiv <command> --help` as the final authority for the executable that
is actually on `PATH`.

## Identity and command set

The expected top-level commands are:

```text
agent  ask  biorxiv  config  debug  health  help  medrxiv
paper  pmc  search  token  trending
```

The short root help is `deepxiv --help`; the expanded examples and option list
are `deepxiv help`; the package version is `deepxiv --version`. `ask` is a
first-class top-level command, not an `agent` subcommand.

If the executable reports a different version or lists commands such as an old
`serve`, `sc`, or `wsearch` surface while the current package is expected, do
not combine those flags with this reference. Resolve the environment's package
installation first and re-run help/version checks. `python -m deepxiv_sdk.cli`
is a useful diagnostic invocation when the module import and console script do
not agree.

## Choose a command

| Need | Command | Important output/default |
| --- | --- | --- |
| A cited answer about papers | `deepxiv ask QUERY` | arXiv backend, streamed answer |
| A cited answer about current/non-arXiv material | `deepxiv ask QUERY --web` | web backend, streamed answer |
| Candidate papers and filters | `deepxiv search QUERY` | arXiv by default, text list |
| Paper metadata/brief/full/section | `deepxiv paper ARXIV_ID` | Markdown by default |
| PubMed Central paper | `deepxiv pmc PMC_ID` | JSON by default |
| bioRxiv DOI | `deepxiv biorxiv DOI` | JSON by default |
| medRxiv DOI | `deepxiv medrxiv DOI` | JSON by default |
| Social-signal list | `deepxiv trending` | text, seven-day window by default |
| Save the DeepXiv token | `deepxiv config` | interactive hidden prompt by default |
| Inspect the current token | `deepxiv token` | prints the complete token; handle carefully |
| Connectivity/token smoke check | `deepxiv health` | makes live API requests |
| Environment diagnostics | `deepxiv debug` | local checks; `--verbose` makes a live request |
| Detailed built-in examples | `deepxiv help` | text to stdout |
| Optional local LLM agent | `deepxiv agent query/config` | separate local LLM configuration |

For API signatures and progressive research workflows, route to
`../../reader-and-paper-research/SKILL.md` rather than reconstructing them from
CLI output.

## `ask`

### Backend and flags

```text
deepxiv ask QUERY [OPTIONS]
```

Common options:

| Option | Values/default | Applies to |
| --- | --- | --- |
| `-t`, `--token` | text; also `DEEPXIV_TOKEN` | both |
| `-w`, `--web` | flag | select web instead of arXiv |
| `-e`, `--effort` | `default`, `high`, `xhigh`; `default` | both |
| `-v`, `--verbose` | flag | progress/tool/quota diagnostics on stderr |
| `--json` | flag | blocking one-object JSON response |
| `--no-stream` | flag | blocking text response |
| `--top-k` | integer 1–30; service default is 10 | **arXiv only** |
| `--search-type` | `search`, `scholar`, `news`, `images` | **web only** |
| `--gl` | Google country code, e.g. `us` or `cn` | **web only** |
| `--hl` | Google UI language, e.g. `en` or `zh-cn` | **web only** |
| `--max-answer-tokens` | integer 256–16384; default 4096 | both |
| `--language` | text; follows query language if omitted | both |
| `--no-sources` | flag | suppress source list in non-JSON text modes |
| `--all-sources` | flag | show every retrieved source instead of only cited ones |

The CLI rejects a cross-backend flag locally with exit code 2, before token
resolution or an API call:

```text
# Valid arXiv partition
deepxiv ask "compare retrieval methods" --top-k 12

# Valid web partition
deepxiv ask "latest API pricing" --web --search-type news --gl us --hl en

# Invalid: --top-k is arXiv-only
deepxiv ask "latest API pricing" --web --top-k 12

# Invalid: web-only flags require --web
deepxiv ask "compare retrieval methods" --search-type scholar
```

Do not try to repair the first invalid form by moving `--top-k` after `--web`;
the flag is still attached to the web backend. Use `--search-type` (and
optionally `--gl`/`--hl`) for web, or remove `--web` and use `--top-k` for
arXiv. `--search-type` defaults to the web `search` vertical when omitted.

Agentic search requires a registered account key from the service. The
first-use auto-registered SDK token is not eligible for this endpoint and
normally produces an authentication/403 message. Agentic quota is separate
from the general search/reading pool.

### Output and citations

Default mode streams answer deltas to **stdout**. The CLI writes the source
list, quota notices, warnings, and verbose progress to **stderr**. This keeps
an answer file clean:

```bash
deepxiv ask "what speedup does speculative decoding report on HumanEval" \
  > answer.md 2> answer.diagnostics
```

In arXiv mode a source is considered cited when its `arxiv_id` occurs in the
answer. In web mode the matching key is the source `url`. By default the CLI
prints only matching/cited sources; when none match, it prints the complete
retrieval set. `--all-sources` always prints the complete set. Web source lines
use `📄` for a page body read by the service and `🔗` for a snippet-only page;
the latter is weaker evidence.

`--json` calls the blocking endpoint and emits one JSON object to stdout rather
than streaming. It includes the service result, which can contain answer,
sources, quota, and stats fields; the CLI does not separately print its source
list in this mode. `--no-stream` also uses the blocking endpoint, prints the
answer to stdout, and prints the source/quota diagnostics to stderr. `--json`
and `--no-stream` may be combined; JSON takes precedence for output.

If the `done` event or blocking `stats` contains `answer_truncated`, the CLI
warns on stderr. Treat the answer as incomplete: rerun with a larger
`--max-answer-tokens` within its allowed range, or narrow/rephrase the query.
A streamed error can follow a partial stdout answer; preserve both streams and
report that the answer is partial rather than treating the error text as part
of the answer.

## `search`

```text
deepxiv search QUERY [OPTIONS]
```

Options in the current source are:

```text
-t/--token TEXT                 API token; DEEPXIV_TOKEN is also accepted
-l/--limit INTEGER              default 10; intended result range 1–100
--offset INTEGER                default 0; intended range 0–10000
-f/--format text|json            default text
-c/--categories TEXT            comma-separated, e.g. cs.AI,cs.CL
--authors TEXT                  comma-separated author filter
--orgs TEXT                     comma-separated organization filter
--venue TEXT                    repeatable venue filter
--venue-year INTEGER            conference/venue year
--min-citations INTEGER         minimum citation count
--date-from TEXT                YYYY, YYYY-MM, or YYYY-MM-DD
--date-to TEXT                  YYYY, YYYY-MM, or YYYY-MM-DD
--date-search-type MODE         between|exact|after|before
--date-str TEXT                 repeatable advanced date value
--use-fine-rerank               opt-in fine reranking
--biorxiv                       select bioRxiv
--medrxiv                       select medRxiv
```

The default source is arXiv. `--biorxiv` and `--medrxiv` switch the unified
search call to that preprint source. Do not select both source flags. `--date-str` is translated to a list for `between` and to a single value for the other
modes; use it twice for a between range. `--date-search-type` takes precedence
over convenience mapping from `--date-from`/`--date-to` in the upstream call.

Text output goes to stdout and includes total count, source label, ID, score,
citations, date, venue when present, and a truncated abstract/TLDR preview.
JSON output is a pretty-printed object with the service result, typically
including `status`, `total_count`, and `result`. Use `--format json` for
piping; do not parse the human-oriented text lines.

Filters are combined upstream. A zero-result response can be valid: loosen a
narrow date/citation combination before assuming authentication failed.

## `paper`

```text
deepxiv paper ARXIV_ID [OPTIONS]
```

`ARXIV_ID` is an arXiv ID unless `--biorxiv` or `--medrxiv` is selected, in
which case it is a DOI. Options are:

```text
-t/--token TEXT
-f/--format markdown|json       default markdown
-s/--section TEXT               one section name (comma-separated for biomed flags)
-p/--preview                    first approximately 10k characters
--head                         metadata/structure JSON
-b/--brief                     title, TLDR, keywords, citations, repository URL
--raw                          raw Markdown
--popularity                   social-impact metrics for an arXiv ID
--biorxiv                      treat ID as a bioRxiv DOI
--medrxiv                      treat ID as a medRxiv DOI
```

Selection behavior is explicit in the implementation: `--head` always emits
JSON; `--brief` is pretty text unless `--format json`; `--raw` emits Markdown;
`--section` emits content, or a JSON wrapper with `arxiv_id`, `section`, and
`content` when JSON is requested; `--preview` emits preview content or JSON;
plain `--format json` requests full paper JSON; no content selector requests
full Markdown. Avoid combining several content selectors; use one deliberate
mode per call.

With `--biorxiv`/`--medrxiv`, no section means metadata; a section requests
section data and is emitted as JSON even when the format option is Markdown.
For a human metadata view use the dedicated `biorxiv`/`medrxiv` commands with
`--format text`.

`--popularity` uses the token already supplied by the option/environment and
does not auto-register a missing token; it warns and returns without fetching
when no token is available. Other paper modes use normal first-use token
resolution.

## `pmc`, `biorxiv`, and `medrxiv`

`pmc` accepts a `PMC_ID` and only supports `--format json` (default). `--head`
returns metadata JSON; without it, the command returns full PMC JSON.

`biorxiv` and `medrxiv` accept a DOI and share this option set:

```text
-t/--token TEXT
-f/--format json|text             default json
-s/--section TEXT                comma-separated section names
--roc                            cited-by-reason list
--roc-num INTEGER                limit ROC entries
```

For these dedicated commands, `--format text` pretty-prints metadata only.
Section and ROC requests remain JSON. `--roc-num` affects ROC requests and is
passed through when supplied. Invalid paper/PMC/DOI identifiers are handled by
friendly command-specific diagnostics; see troubleshooting.

## `trending`

```text
deepxiv trending [OPTIONS]
```

Options are `--days` (integer 1–30, default 7), `--limit` (integer, default 30;
the request and display are capped at 100), `-o/--output text|json` (default
text), and `--json` (shorthand overriding `--output text`). The command uses a
live trending request and does not take a token option. Text includes the
period, generation time, total, rank, and social metrics; JSON preserves the
service result. For a digest workflow, route to the sibling research skill.

## `config`, `token`, `health`, `debug`, and `help`

See [configuration](configuration.md) for persistence and credential handling.
The operational distinctions are:

- `deepxiv config [--token TEXT] [--global]` saves `DEEPXIV_TOKEN` to the home
  `.env` by default; Click also exposes `--no-global` for the current directory
  `.env`. Omitting `--token` prompts with hidden input.
- `deepxiv token [--token TEXT]` resolves/auto-registers a token when absent and
  prints the complete token. It is not a masked status check; never redirect or
  paste its stdout into a shared log.
- `deepxiv health [--token TEXT]` checks API connectivity, optionally validates
  the explicitly supplied token against a free test paper, and checks a free
  arXiv paper. It makes network calls and does not implicitly use
  `DEEPXIV_TOKEN` through the option declaration.
- `deepxiv debug [--verbose]` prints Python/platform/version, optional feature
  availability, whether relevant environment variables are set, and config
  file presence without printing their values. `--verbose` additionally enables
  logging and makes a live paper request; use plain `debug` for a local-first
  diagnostic.
- `deepxiv help` prints the full built-in command examples and environment notes;
  `deepxiv --help` is the compact Click command listing.

## Optional `agent` boundary

The source registers an `agent` group with:

```text
deepxiv agent query QUERY
  -t/--token TEXT  --max-turn INTEGER (default 20)  -v/--verbose
  --api-key TEXT   --base-url TEXT   --model TEXT   --disable-thinking

deepxiv agent config
  --api-key TEXT   --base-url TEXT   --model TEXT
```

`agent query` needs a DeepXiv token plus a configured LLM API key. Query
options override the local agent configuration. `agent config` stores local
LLM configuration and can prompt for a key. Do not put local Agent graph/tool
implementation details in this route; use
`../../optional-local-agent/SKILL.md`.
