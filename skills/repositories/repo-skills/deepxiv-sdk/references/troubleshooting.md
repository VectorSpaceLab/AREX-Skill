# Cross-cutting troubleshooting

Read this reference when installation, import selection, credentials, endpoint
configuration, or package-version behavior is unclear. Workflow-specific
failures belong to the nearest sub-skill troubleshooting reference.

## Install and import

- **`ModuleNotFoundError: deepxiv_sdk`:** install the distribution in the
  interpreter that will run the task: `python -m pip install deepxiv-sdk`, then
  check `python -c "import deepxiv_sdk; print(deepxiv_sdk.__version__)"`.
  Avoid relying on a different `pip` executable or a source checkout on
  `PYTHONPATH`.
- **`Agent` is missing from `deepxiv_sdk`:** the base Reader/CLI import can work
  without optional dependencies. Run `scripts/check_install.py`; install
  `"deepxiv-sdk[agent]"` or `[all]`, then install `tiktoken` if reported as
  missing. Do not treat a base-only import as local-agent support.
- **CLI/package mismatch:** run `python -m pip show deepxiv-sdk`, the version
  check above, and `deepxiv --help`. If the module says 1.0.x but the executable
  exposes an older command set, repair the active installation or invoke the
  intended interpreter's entry point; do not mix old flags with this graph.
- **Editable checkout confusion:** use the installed distribution for ordinary
  Researcher work. A repository checkout is evidence for refresh, not a
  runtime dependency of this skill.

## Credentials and quotas

- **401 or “Invalid or expired token”:** configure a valid DeepXiv token through
  the documented environment/config mechanism or pass it at runtime. Never
  paste it into a prompt, commit, or diagnostic report.
- **Hosted `ask` returns 403:** an auto-registered SDK token is not eligible for
  agentic search. Register for an account key, configure that key, and retry
  once; ordinary `search`, `brief`, and paper reads use a separate pool.
- **429/rate limit:** hosted agentic calls have a separate quota from ordinary
  retrieval. Stop repeated retries, record the remaining quota if returned, and
  wait or change the account tier. Local `Agent` model calls also consume the
  provider's own limits.
- **Live calls are unavailable:** use the no-network probes and mocked/native
  tests for package behavior, but label any research result as unverified until
  the service responds.

## Endpoint and input failures

- **Bad request / validation error:** check source-specific options and bounds.
  Hosted agentic queries are nonblank and at most 2000 characters; arXiv
  `top_k` is 1–30; web `search_type` is `search`, `scholar`, `news`, or
  `images`; answer caps are 256–16384. Ordinary search size is 1–100 and
  offset is 0–10000.
- **Paper/PMC/DOI not found:** confirm the identifier type before retrying:
  arXiv IDs go to arXiv methods, `PMC...` IDs go to PMC methods, and
  bioRxiv/medRxiv methods expect a DOI. A very recent paper may not be indexed;
  search again later or use a broader query rather than retrying the same ID.
- **No search results:** stacked date, venue, category, author, organization,
  and citation filters are combined. Loosen one constraint and record the
  change; a valid empty result is not automatically an authentication failure.
- **Timeout/connection error:** ordinary Reader GET methods retry using
  `max_retries` and exponential delay. Agentic methods do not auto-retry;
  narrow or rephrase the query, use default effort, and retry deliberately.

## Evidence integrity

- **Truncated answer:** inspect blocking `stats.answer_truncated` or the stream's
  `done.answer_truncated`; increase the cap within bounds or narrow the query.
  Do not summarize a cut-off answer as complete.
- **Unrelated sources shown:** the retrieval set is a superset of cited sources.
  Match arXiv IDs or web URLs that actually occur in the answer, or request all
  sources when auditing retrieval.
- **Weak web evidence:** a web source with `read: false` contributed only a
  search snippet. Mark it weaker than a `read: true` cached page body and avoid
  presenting snippet-only claims as fully verified.
