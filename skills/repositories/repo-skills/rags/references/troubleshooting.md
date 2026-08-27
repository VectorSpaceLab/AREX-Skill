# RAGs Cross-Cutting Troubleshooting

## Package Install Fails With No `rags` Package

**Symptom:** `pip install .` or equivalent root package installation fails with a
message that no file/folder was found for package `rags`.

**Cause:** this source snapshot is a Streamlit app with top-level modules and
page scripts, not an installable import package named `rags`.

**Action:** install dependencies for the app runtime and run from a checkout. If
using Poetry, prefer a dependency-only mode if root installation fails. Use the
root install checker with `--repo-root` to verify source imports.

## Missing Streamlit Secrets

**Symptom:** app launch or source import fails before any RAG agent is created.

**Cause:** the builder configuration reads `st.secrets.openai_key` while loading
the builder LLM.

**Action:** add an `openai_key` entry to the Streamlit secrets used by the app.
Add `anthropic_key`, `replicate_key`, or `metaphor_key` only when those provider
or web-search paths are selected. Do not print or commit secret values.

## Old Dependency Compatibility

**Symptom:** dependency imports fail around `pkg_resources`, Streamlit packaging
pins, or Pydantic deprecations.

**Cause:** RAGs targets older LlamaIndex/Streamlit versions. LlamaIndex 0.9.7
imports `pkg_resources`; newer setuptools versions may remove it. Streamlit
1.28 also pins `packaging<24`.

**Action:** use Python below 3.12 and keep dependency versions aligned with the
project metadata. If using modern packaging tools, pin setuptools below the
`pkg_resources` removal threshold and use a wheel version compatible with the
packaging pin.

## Cache Breaks After Upgrade

**Symptom:** app launch, sidebar selection, or agent loading fails after a code
or dependency upgrade.

**Cause:** cached agent metadata or persisted vector-index storage may be stale.

**Action:** inspect the cache read-only through the configuration sub-skill.
Preserve needed source/task information, then delete or move stale cache entries
only with approval and rebuild agents from source data.

## External Calls Fail

**Symptom:** OpenAI/Anthropic/Replicate, URL loading, or web-search operations
fail even though local imports succeed.

**Cause:** safe import checks do not prove credentials, quota, provider network,
URL reachability, or remote service behavior.

**Action:** verify credentials and network separately. For URL data, stage
content locally when network is unreliable. For web search, ensure the selected
agent includes `web_search` and a `metaphor_key` exists.

## Optional Multimodal Fails

**Symptom:** multimodal imports or class signatures work, but actual image/text
agent construction fails.

**Cause:** the beta multimodal branch needs optional dependencies and external
model credentials that are not part of the minimum verified environment.

**Action:** install optional dependencies deliberately, verify a tiny image/text
fixture, and treat failures as optional-branch issues unless the user explicitly
requires multimodal support.

## No Substantive Native Tests

**Symptom:** a user asks for a repo test command to prove app behavior.

**Cause:** the current repo has an empty test package only. The Makefile exposes
`make test`, but there are no substantive native tests in this snapshot.

**Action:** use the bundled helpers and synthetic usability checks for safe
validation. Run full app/server or external model tests only with explicit user
approval and credentials.
