# Core WebAgent troubleshooting

## Start with the safe probe

From the `la-vague` skill root:

```bash
python sub-skills/core-web-agent/scripts/lavague_minimal_agent.py --dry-run
```

If imports fail, fix the package/context/driver installation before attempting a browser or model-provider run.

## Missing model-provider credentials

**Symptoms**

- Provider errors mentioning missing API keys.
- Default quick-tour code fails before or during model calls.
- Anthropic or Fireworks context unexpectedly asks for OpenAI credentials.

**Likely causes**

- The default LaVague bundle uses OpenAI-backed LLM, multimodal LLM, and embeddings.
- Some non-OpenAI contexts still default one component to an OpenAI model or embedding.

**Recovery**

1. Route provider choices to `../contexts-and-retrievers/SKILL.md`.
2. Check that required environment variables exist without printing values.
3. Use `Context`/`from_context` consistently so `WorldModel` and `ActionEngine` share the intended model stack.
4. Do not run live tasks until the user accepts provider cost and network use.

## Browser construction fails

**Symptoms**

- Selenium/Playwright import succeeds but `SeleniumDriver()` or `PlaywrightDriver()` fails.
- Errors mention Chrome, Chromedriver, Chromium revision, headed/headless, display, or profile locks.

**Recovery**

Use `../browser-drivers/SKILL.md`. Core WebAgent guidance assumes the driver object can already construct or attach to a browser.

## Telemetry warning appears

**Symptom**

LaVague warns that telemetry is turned on.

**Recovery**

Set the environment variable before importing/running LaVague:

```bash
export LAVAGUE_TELEMETRY=NONE
```

Do this whenever objectives, user data, generated code, page text, URLs, screenshots, or errors could contain sensitive information.

## NLTK data/proxy warnings during import

**Symptoms**

- Warnings mention `nltk_data`, `stopwords`, `punkt`, proxy security, or SSRF/pathsec refusal.
- Imports may still succeed, but retrieval/text utilities may later miss NLTK resources.

**Likely cause**

Upstream dependencies can try to fetch NLTK resources at import time. In proxied or locked-down environments, NLTK blocks downloads unless the proxy is trusted.

**Recovery**

- Prefer pre-seeding NLTK data through the environment management process.
- Do not set `NLTK_ALLOW_PROXIED_URLOPEN=1` unless the user confirms the proxy is trusted and SSRF-safe.
- If the task does not need live retrieval over large pages, treat the warning as non-blocking after import probes pass.

## `pkg_resources` or setuptools errors

**Symptoms**

- Import stack ends in `ModuleNotFoundError: No module named 'pkg_resources'`.
- Warnings say `pkg_resources` is deprecated.

**Likely cause**

`llama_index.legacy` imports `pkg_resources`; newer setuptools releases may omit it.

**Recovery**

Install or pin a setuptools version that still provides `pkg_resources`, for example `setuptools<81`, inside the project environment. Do not bake local environment paths into runtime guidance.

## `agent.demo()` import error

**Symptom**

`agent.demo()` raises an import error for `lavague-gradio` or a Gradio dependency.

**Recovery**

Route to `../server-extension-gradio/SKILL.md`. `agent.demo()` is exposed on `WebAgent`, but the UI dependency is optional and imported lazily.

## Stale logs or result state

**Symptoms**

- `display_previous_nodes` reports no previous nodes.
- `result.output` is from an earlier successful step.
- Generated code accumulation looks unexpected.

**Recovery**

1. Call `agent.prepare_run(...)` or use `agent.run(...)` rather than manually mixing state across objectives.
2. Create a fresh `WebAgent` for a new browser/session when debugging confusing state.
3. Remember that `WebAgent` initializes `result.code` with driver setup code and appends successful action code.
4. Check `action_result.success` before trusting generated code for a step.

## Objective/data privacy issue

**Symptoms**

- User wants to automate pages containing personal data, credentials, account information, or private URLs.

**Recovery**

- Ask for explicit authorization before live browsing or sending page content to providers.
- Disable telemetry if required.
- Avoid `log_to_db=True` and persistent local logs unless explicitly requested.
- Redact user data from objectives and logs when possible.
