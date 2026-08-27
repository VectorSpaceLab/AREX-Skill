# Builder Troubleshooting

## Missing `openai_key` During Import or App Launch

**Symptom:** importing builder modules or launching the app fails while reading
Streamlit secrets, often before any user interaction.

**Likely cause:** `core.builder_config` reads `st.secrets.openai_key` while
creating the builder LLM.

**Fix:** create a Streamlit secrets file for the environment running the app and
set `openai_key = "..."`. Do not rely only on `OPENAI_API_KEY`; the current
source reads the Streamlit secret directly.

## `ValueError`: Must Specify Only One Data Source

**Symptom:** a build request with files and a directory, files and URLs, or a
directory and URLs raises a source-selection `ValueError`.

**Likely cause:** `load_data` permits exactly one source kind.

**Fix:** use [`../scripts/validate_source_selection.py`](../scripts/validate_source_selection.py)
first. Split mixed local/remote sources into separate builds or stage remote
content locally before building.

## URL Loading Fails

**Symptom:** URL source loading errors, stalls, or produces no documents.

**Likely cause:** URL loading uses LlamaHub's simple web page reader and needs
network access, reachable pages, and compatible dependencies.

**Fix:** verify network access separately. If network is unavailable, download
or copy the content into local files and build from `file_names` or `directory`.

## `web_search` Is Missing or Rejected

**Symptom:** the builder does not offer web search, or updating tools with a
name other than `web_search` fails.

**Likely cause:** web search is conditionally exposed only when `metaphor_key`
is present. The current tool registry recognizes only `web_search`.

**Fix:** add `metaphor_key` before creating the builder if web search is needed.
Remove unknown tool names from configuration.

## Unsupported LLM Prefix

**Symptom:** agent construction raises `ValueError("LLM ... not recognized.")`.

**Likely cause:** `_resolve_llm` only supports unprefixed OpenAI names plus
`openai:`, `anthropic:`, `replicate:`, and `local:` prefixes.

**Fix:** rewrite the model ID using one of those formats and ensure the matching
Streamlit secret exists.

## Summarization Gives Poor or Failed Results

**Symptom:** enabling summarization produces weak, costly, or failed responses.

**Likely cause:** the README states summarization is intended for GPT-4-class
models. The summary tool adds another query route and may amplify model/provider
limitations.

**Fix:** disable summarization for first-pass lookup bots, or use a GPT-4-class
model and validate with a small representative document set.

## Multimodal Branch Fails

**Symptom:** beta multimodal setup imports but fails while building or querying.

**Likely cause:** actual multimodal construction needs optional dependencies and
OpenAI multimodal credentials. The minimum verified environment did not install
`torch`, `torchvision`, or the GitHub CLIP dependency.

**Fix:** treat multimodal as an opt-in capability. Install optional dependencies
and credentials deliberately, then run a small image/text fixture before using
it for real data.

## `pip install .` Fails for `rags`

**Symptom:** package installation reports no module or package named `rags`.

**Likely cause:** the current repository is a Streamlit app with top-level
modules (`core`, page scripts, `st_utils`) and no import package named `rags`.

**Fix:** use dependency installation for the app runtime and run/inspect from a
RAGs checkout. For Poetry-based setup, a dependency-only mode such as
`poetry install --no-root` may be more appropriate than installing the root
package.
