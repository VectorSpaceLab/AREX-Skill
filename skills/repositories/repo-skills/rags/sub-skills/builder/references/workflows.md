# Builder Workflows

## Purpose

Use this reference to build a RAGs agent from scratch without reopening the
original README or source pages. It distills the Home page and builder-agent
flow into repeatable decisions and validation checks.

## Prerequisites

- Install the runtime dependencies described by the root skill.
- Provide a Streamlit secret named `openai_key` before importing or running the
  builder path. RAGs reads this secret while configuring the builder LLM.
- Use one data-source kind per build: local files, one directory, or URLs.
- Do not run real LLM, URL, or web-search calls unless credentials and network
  access are intentionally available.

## Home Page Builder Route

1. Start from a new agent selection. If an old agent is selected in the sidebar,
   choose the new-agent route before building.
2. Decide whether beta multimodal search is needed before creating the builder.
   The multimodal toggle is locked after a cache is selected because the cached
   builder type determines reconstruction.
3. Describe the target task in natural language. This text is used by the
   builder to produce a system prompt for the generated RAG agent.
4. Specify one data source:
   - `file_names`: one or more local files.
   - `directory`: a directory whose files should be loaded.
   - `urls`: one or more web pages; this branch needs network access.
5. Ask for or accept RAG parameters. Defaults are safe for a small first pass:
   summarization disabled, `top_k=2`, `chunk_size=1024`, default embedding
   model, and GPT-4 preview as the LLM.
6. Optionally add `web_search` only when the app has a `metaphor_key` secret.
7. Create the agent. Creation builds the vector index, constructs the query
   tools, saves cache state, and makes the agent available to the configuration
   and chat pages.

## Data-Source Validation

Run the bundled validator before a build when the user supplies paths or URLs:

```bash
python sub-skills/builder/scripts/validate_source_selection.py --file notes.md --file paper.txt
python sub-skills/builder/scripts/validate_source_selection.py --directory ./docs
python sub-skills/builder/scripts/validate_source_selection.py --url https://example.com/page
```

The helper performs structural checks only. It does not download URLs or call
LlamaIndex. If the user wants to mix a local file and a URL, split the work into
separate agent builds or ask them to stage the remote content locally first.

## RAG Parameters

| Parameter | Default | Builder meaning | Practical guidance |
| --- | --- | --- | --- |
| `include_summarization` | `False` | Adds a summary query tool in addition to vector search. | Enable for broad summary tasks and GPT-4-class models; keep disabled for simple lookup or cheaper models. |
| `top_k` | `2` | Number of retrieved chunks passed to the vector query engine. | Increase for diffuse questions or low recall; decrease when answers are noisy. |
| `chunk_size` | `1024` | Chunk size used by the LlamaIndex service context. | Smaller chunks improve pinpoint retrieval; larger chunks preserve context. |
| `embed_model` | `default` | Embedding resolver input. | `default` uses the configured LlamaIndex default; local Hugging Face embeddings use `local:<model-id>`. |
| `llm` | `gpt-4-1106-preview` | LLM resolver input for the generated RAG agent. | Use unprefixed or `openai:<model>` for OpenAI, `anthropic:<model>`, `replicate:<model>`, or `local:<model>`. |

## Optional Web Search

The builder exposes `add_web_tool` only when a `metaphor_key` Streamlit secret is
present. The current app supports only the tool name `web_search` in persisted
config. If a user asks for web search but the secret is absent, either add the
secret before building or proceed without the tool and explain the limitation.

## Optional Multimodal Builder

The beta multimodal route swaps in `MultimodalRAGAgentBuilder`. It supports
local files or a directory, not URL loading, and sets `builder_type` to
`multimodal` before saving. Actual multimodal querying requires optional image
and model dependencies plus OpenAI multimodal credentials. Treat it as an
explicit optional branch, not a default build path.

## Safe Validation Signals

- `RAGAgentBuilder.get_rag_params()` returns the default parameter dictionary.
- `RAGAgentBuilder.set_rag_params(top_k=4, chunk_size=256)` updates only the
  provided fields and returns "RAG parameters set successfully."
- `load_data(file_names=[...])` can load a tiny local text file into one or more
  LlamaIndex `Document` objects.
- `load_data(file_names=[...], directory=...)` should raise a `ValueError`
  because only one source kind is allowed.
