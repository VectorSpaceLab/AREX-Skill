# CLI configuration and credential safety

## DeepXiv token resolution

For commands that accept a token, the effective order is:

1. An explicit `--token`/`-t` option.
2. The `DEEPXIV_TOKEN` environment variable (Click also exposes it as the
   option's environment source for most token-taking commands).
3. A `.env` value loaded by the CLI module, if `python-dotenv` is available.
4. For commands using `ensure_token`, automatic registration on first use.

At import time the CLI attempts to load a home `.env` and then a current-working-
directory `.env`, with `override=False`. A shell variable that is already set
wins. Because values are not overridden, a value loaded from the first file can
also prevent a same-named value in the second file from taking effect; do not
assume that the project file overrides the home file. The explicit option always
wins after this loading step.

The command-specific behavior matters:

- `search`, `ask`, normal `paper`, biomedical `paper` flags, `pmc`, `biorxiv`,
  `medrxiv`, and `token` call `ensure_token` and may auto-register/save a token
  when none is found.
- `paper --popularity` uses the supplied/environment token without auto-creating
  one. If absent, it prints a warning and returns without an API call.
- `trending` does not expose a token option and constructs a tokenless
  `Reader`; the endpoint itself determines whether access is allowed.
- `health` only validates a token explicitly supplied to `--token`; no token
  option is required for its connectivity/free-paper checks.
- `debug` reports whether token-related variables are set but does not print
  their values.
- `agent query` first resolves a DeepXiv token and then separately resolves an
  LLM API configuration.

## Saving `DEEPXIV_TOKEN`

Use the interactive form when possible:

```bash
deepxiv config
```

The prompt hides the token. With a deliberate non-interactive choice, the
source supports `deepxiv config --token VALUE`. The `--token` option is visible
in shell history and may be visible to process inspection while the command is
running, so do not use it where those channels are untrusted.

The `config` command writes the raw `DEEPXIV_TOKEN=...` pair with no quoting or
file-permission hardening:

- default `--global` behavior writes the home `.env`;
- `--no-global` writes `.env` in the current directory;
- an existing `DEEPXIV_TOKEN=` line is replaced; otherwise a new line is
  appended;
- the current process also receives `DEEPXIV_TOKEN` immediately.

Protect either `.env` file as a secret-bearing file. Keep a project-local one
out of version control, do not include it in bug reports or archives, and use
normal operating-system permissions. If a token was exposed in a command,
terminal capture, CI log, or report, revoke/replace it through the service rather
than merely deleting the local file.

The CLI also auto-registration path writes its token to the home `.env`. An
automatic registration message may print the destination path and daily limit,
but it should not be treated as a safe way to display or share credentials.

## Inspecting a token

`deepxiv token` is not a masked status command. It resolves/auto-registers when
necessary and prints the complete current token, followed by support text.
Invoke it only when the terminal is private and never redirect it to a shared
log, paste it into an issue, or use it in a captured smoke test. For a safe
presence check use `deepxiv debug` instead; it reports set/unset status without
printing the value.

## Registered key versus SDK token

Regular search and paper retrieval can use the first-use auto-registered SDK
token. Hosted agentic `deepxiv ask` requires a registered account key; an
auto-registered token is not eligible and can produce a 403. Configure the
registered key through the interactive `deepxiv config` flow and then confirm
that the intended environment resolves it. Do not retry the same ineligible
credential as if it were a transient network error.

## Optional local agent configuration

`deepxiv agent config` manages a separate local JSON file named
`~/.deepxiv_agent_config.json`. It can prompt for an LLM API key and optionally
store a base URL and model. The key is stored in plaintext in that file; the
CLI does not encrypt it or harden its permissions. Protect it like `.env`, keep
it out of repositories and logs, and prefer environment/secret-manager
injection where persistence is not required.

`deepxiv agent query` accepts `--api-key`, `--base-url`, and `--model`; these
options override the saved config for that invocation. The corresponding
environment variables are `DEEPXIV_AGENT_API_KEY`, `DEEPXIV_AGENT_BASE_URL`,
and `DEEPXIV_AGENT_MODEL`. Passing a key directly on a command line has the
same history/process-list risk as `--token`. Local Agent behavior is outside
this route; use `../optional-local-agent/SKILL.md` for that boundary.

## Health and debug safety

Both commands need a clear distinction between local inspection and live
verification:

- `deepxiv debug` is the local-first diagnostic. Plain mode imports optional
  feature checks and reports variable/config presence. `deepxiv debug --verbose`
  enables debug logging and performs a live request against a test paper; do
  not use it in a no-network smoke test.
- `deepxiv health` always performs live connectivity and free-paper checks. A
  supplied `--token` adds a token validity request. It is useful for service
  diagnosis, not for proving that a command is network-free.

For a no-network, no-credential-read check use the bundled
`../scripts/cli_smoke.py` helper instead.
