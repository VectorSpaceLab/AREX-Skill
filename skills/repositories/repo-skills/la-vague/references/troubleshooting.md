# LaVague cross-cutting troubleshooting

## Use the shared probe first

From the `la-vague` skill root:

```bash
python scripts/check_lavague_environment.py --check all
```

This checks package imports and CLI availability without launching browsers, contacting model providers, starting servers, or reading original repo files.

## Python/package install failures

**Symptoms**

- `ModuleNotFoundError: lavague...`
- Console commands such as `lavague-serve`, `lavague-qa`, or `lavague-test` are missing.
- Provider context imports fail.

**Recovery**

1. Install the distribution that owns the import surface; see [package-overview.md](package-overview.md).
2. Prefer Python 3.10 for all packages in this snapshot because some provider contexts declare `<3.12`.
3. Install only needed optional packages; do not install every provider or browser integration unless the task needs them.
4. Re-run the shared probe and the nearest sub-skill probe.

## `pkg_resources` / setuptools issue

**Symptom**

`ModuleNotFoundError: No module named 'pkg_resources'` while importing `llama_index.legacy` through `lavague.core`.

**Recovery**

Install a setuptools version that still ships `pkg_resources`, for example:

```bash
python -m pip install 'setuptools<81'
```

This is an upstream compatibility issue; keep the pin local to the working environment.

## NLTK data or proxied-download warnings

**Symptoms**

- Import or first retrieval prints warnings for `stopwords`, `punkt`, `nltk_data`, proxy/pathsec, or SSRF protection.

**Recovery**

- If imports otherwise pass, this is often non-blocking for dry-run probes.
- For real retrieval workflows, pre-seed NLTK resources in the environment or authorize a trusted proxy explicitly.
- Do not set `NLTK_ALLOW_PROXIED_URLOPEN=1` unless the user confirms the proxy is SSRF-safe.

## Telemetry and privacy

LaVague telemetry is on by default in this snapshot. Disable it before importing/running LaVague when objectives, URLs, observations, generated code, screenshots, user data, or errors may be sensitive:

```bash
export LAVAGUE_TELEMETRY=NONE
```

Avoid persistent logs (`log_to_db=True`, `LocalLogger`, `LocalDBLogger`) unless the user asks for them.

## Browser backends unavailable

**Symptoms**

- Selenium/Playwright imports pass but browser construction fails.
- Errors mention Chrome, Chromedriver, Chromium revision, display, sandbox, or profile lock.

**Recovery**

Route to `sub-skills/browser-drivers/SKILL.md` and run:

```bash
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver both
```

Live browser examples remain optional unless the user has approved browser automation and the host has compatible binaries.

## Provider/API-key problems

**Symptoms**

- Default quick-tour code asks for OpenAI credentials.
- Anthropic/Fireworks/Gemini/Azure code imports but fails on construction or first call.
- Cohere reranker fails at rerank time.

**Recovery**

Route to `sub-skills/contexts-and-retrievers/SKILL.md` and run the safe context/retriever probe. Check env-var presence without printing secrets. Remember that some non-OpenAI contexts still use OpenAI embeddings or multimodal defaults unless overridden.

## Gradio/server dependency mismatches

**Symptoms**

- `agent.demo()` fails after normal core imports pass.
- `lavague-serve` help works but extension cannot connect.
- Gradio errors mention `huggingface_hub`, `HfFolder`, or UI launch dependencies.

**Recovery**

Route to `sub-skills/server-extension-gradio/SKILL.md`. Start with the safe probe and avoid launching a persistent server/UI until the user authorizes live interaction.

## QA/test-runner input issues

**Symptoms**

- `lavague-qa` requires `--url` or `--feature`.
- Feature file parses incorrectly.
- `lavague-test` config fails schema/operator/property validation.

**Recovery**

Route to `sub-skills/qa-and-test-runner/SKILL.md` and use the bundled file-only probes before launching browser/LLM runs.

## When to stop

Stop and ask before proceeding if the next step would:

- Use paid or credentialed provider APIs.
- Automate a sensitive website/account.
- Enable telemetry or persistent logs for sensitive data.
- Install browser binaries or mutate a user-provided environment.
- Start a long-running Gradio/websocket server.
