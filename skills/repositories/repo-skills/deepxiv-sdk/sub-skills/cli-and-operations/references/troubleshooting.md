# CLI troubleshooting and recovery

Start with a non-secret identity check:

```bash
deepxiv --version
deepxiv --help
deepxiv debug
```

Do not start with `deepxiv token` in a captured terminal: that command prints
the complete token. Use the safe smoke helper for no-network validation.

## Command or option is missing

The 1.0 command group includes `ask`, `search`, `paper`, `pmc`, `biorxiv`,
`medrxiv`, `trending`, `config`, `token`, `health`, `debug`, `help`, and the
`agent` group. If `deepxiv --help` reports a different generation (for example,
an older command set with `serve` or `wsearch`) or `deepxiv --version` is not
1.0.0, the executable and intended package are out of sync. Do not work around
that by mixing old flags into current recipes. Repair the package/environment
selection, then repeat help/version checks. Running `python -m deepxiv_sdk.cli
--help` can distinguish a console-script resolution problem from a package
problem, but it is still a diagnostic only.

For exact installed options, run `deepxiv <command> --help`; Click rejects
unknown options and invalid choice/range values with a non-zero result, normally
exit code 2, before making a request.

## `ask` rejects the flags

The CLI intentionally partitions backend flags to prevent silently ignored
options:

- `ask --web --top-k N` fails with `--top-k is arXiv-only`.
- arXiv `ask` with `--search-type`, `--gl`, or `--hl` fails with
  `<flag> requires --web`.

For web, remove `--top-k` and select `--search-type search|scholar|news|images`
plus optional `--gl`/`--hl`. For arXiv, remove `--web` and use `--top-k`.
These local validation failures should be corrected, not retried.

`--effort` accepts only `default`, `high`, and `xhigh`. `--max-answer-tokens`
accepts 256 through 16384. Rephrase a low-recall query before raising effort;
effort adds evidence-gathering rounds but does not repair poor first-round
recall.

## Authentication and registration

The CLI maps reader authentication exceptions to a friendly stderr message and
exits non-zero. Interpret the context:

- For ordinary `search`, paper, PMC, or biomedical retrieval, a 401 generally
  means the token is missing, invalid, or expired. Check presence with
  `deepxiv debug`, then replace the credential through the hidden-prompt
  `deepxiv config` flow. Do not paste the replacement into logs.
- For hosted `ask`, a 403 can mean the token is a valid SDK token without
  registered agentic access. Use a registered account key; automatic
  re-registration of the same SDK-token class will not grant that access.
- The CLI's generic authentication handler suggests auto-registration for some
  authentication failures, but that suggestion must not override the hosted
  `ask` registered-key requirement.

If an interactive command has no token and auto-registration is enabled, it may
make a registration network request and persist a new token to the home `.env`.
Use `deepxiv config` when a specific registered key is required or when
network-free behavior is required.

## Rate limits

A `RateLimitError` is rendered as a daily-limit message and exits with status 1.
The general search/reading limit and the hosted agentic quota are separate:
exhausting one does not imply the other is exhausted. `ask` may additionally
print a near-empty agentic quota warning on stderr, especially with
`--verbose`. Wait for reset or use the appropriate account/plan; do not spin in
an immediate retry loop.

## Invalid identifiers or parameters

`BadRequestError` gets command-specific hints:

- `paper` expects an arXiv ID, not a keyword; search first if starting from a
  topic. With `--biorxiv`/`--medrxiv`, pass the corresponding DOI instead.
- `pmc` expects a PMC identifier such as `PMC...`.
- `biorxiv`/`medrxiv` expect a DOI.
- `ask` requires a query of 1–2000 characters according to the CLI's server
  hint.

For a paper that is simply absent, verify the identifier and try the smallest
retrieval mode (`--brief` or `--head`) before requesting full content. Detailed
paper-reading choices belong to `../reader-and-paper-research/SKILL.md`.

## Clean streaming and truncation recovery

Use separate file descriptors when automation needs the answer and diagnostics
independently:

```bash
set -o pipefail
deepxiv ask "a specific question with a measurable claim" \
  >answer.txt 2>diagnostics.txt
status=$?
```

Check `status` and inspect both files. A streamed answer can have partial text
on stdout before an error on stderr. The source list is intentionally on stderr
and may contain only sources whose arXiv ID (arXiv backend) or URL (web backend)
was found in the answer; use `--all-sources` when the full retrieval set is
needed. In web mode, distinguish `📄` full cached-body reads from `🔗` snippet-
only evidence.

A truncation warning is emitted on stderr when `answer_truncated` is true. Do
not summarise a truncated answer as complete. Retry with a higher value of
`--max-answer-tokens` up to 16384, or ask a narrower question. `--json` is
blocking and exposes service stats in its JSON object, so automation should
inspect `stats.answer_truncated` as well as the process status.

## JSON versus text surprises

- `ask --json` is one blocking JSON object on stdout; source decorations are
  represented in the payload rather than printed as the normal stderr list.
- `ask --no-stream` is blocking text: answer stdout, sources/quota stderr.
- `search --format json` is the machine-readable search response; its default
  text is a display list.
- `paper --head` always emits JSON. `paper --brief` is human text unless
  `--format json` is supplied. Biomedical section/ROC calls remain JSON even
  when a text format was requested.
- `biorxiv`/`medrxiv --format text` only changes metadata display; section and
  ROC responses remain JSON.
- `trending --json` overrides `--output text`.

Parse stdout only for structured output; do not parse source/progress lines from
stderr as answer content.

## `health` and `debug` are not equivalent

`health` is a live check: it requests API docs, may validate an explicitly
provided token, and checks a free arXiv paper. It can fail because of timeout,
connection, or API availability. `debug` without `--verbose` is local-first;
`debug --verbose` enables logging and makes a live paper request. Neither command
is a substitute for the no-network `cli_smoke.py` helper.

## Optional `agent` failures

`agent query` reports a missing LLM key and points to `deepxiv agent config` or
the agent environment variables. If optional imports are absent, install the
package's agent/all extra in the intended environment; do not add local Agent
implementation work to a CLI diagnosis. For reasoning models that fail with a
message about reasoning content needing to be the last assistant message, retry
with `--disable-thinking`. Route provider, graph, tool, and circuit-breaker
questions to `../optional-local-agent/SKILL.md`.
