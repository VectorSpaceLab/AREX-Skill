# Chat Troubleshooting

## "Agent Not Created"

**Symptom:** the page reports that no agent exists.

**Likely cause:** `current_state.cache.agent` is `None`, either because no bot
was built or the selected cache failed to reconstruct.

**Fix:** build a new bot through the builder route or inspect the selected cache
with the configuration sub-skill.

## No Sources Expander

**Symptom:** the answer text appears, but there is no Sources expander.

**Likely cause:** `response.source_nodes` is empty, missing, or all source lists
are empty after splitting.

**Fix:** ask a narrow question tied to known source content, increase `top_k`,
review chunk size, verify the data source was loaded correctly, and inspect the
agent/cache route before changing UI code.

## Irrelevant Sources

**Symptom:** sources are displayed but do not support the answer.

**Likely cause:** retrieval miss, stale vector index, inappropriate chunk size,
embedding mismatch, or a broad query.

**Fix:** rebuild or update the agent with better chunking/retrieval settings,
then test with a known-answer prompt.

## Broken Image Rendering

**Symptom:** image sources are found but Streamlit cannot render them.

**Likely cause:** image node metadata lacks `file_path`, points to a moved file,
or the node is not an `ImageNode` and is routed to the text table.

**Fix:** verify the data source still exists, inspect image node metadata, and
ensure the multimodal build path was used deliberately.

## Provider or Credential Error During Chat

**Symptom:** `agent.chat` raises an OpenAI, Anthropic, Replicate, local model, or
network error.

**Likely cause:** chat uses the model settings saved during build/configuration.
Missing secrets or unavailable network surface only when a live chat call is
made.

**Fix:** inspect `llm`, `embed_model`, provider prefixes, and secrets through the
builder/configuration routes. Do not debug source rendering until the provider
call succeeds.

## Summary Questions Are Weak

**Symptom:** broad summarization questions return incomplete answers.

**Likely cause:** summarization was not enabled, the selected LLM is weak for
summary synthesis, or the summary tool was not chosen.

**Fix:** enable summarization for broad summary tasks and use a GPT-4-class
model when possible. For simple factual queries, rely on vector retrieval.

## Chat History Looks Stale

**Symptom:** old messages appear after switching agents or rebuilding.

**Likely cause:** Streamlit session state stores `agent_messages` separately
from persisted agent cache.

**Fix:** refresh the app or clear session state. Confirm the sidebar selected ID
matches the intended generated agent.
