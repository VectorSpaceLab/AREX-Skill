# Configuration and Environment

## Runtime dependency set

The repository is source-first and does not declare packaging metadata. Install a path-aware environment that makes `pageindex` importable and includes the runtime dependency set below:

- `litellm==1.84.0`
- `pymupdf==1.26.4`
- `PyPDF2==3.0.1`
- `pypdfium2==4.30.0`
- `python-dotenv==1.2.2`
- `pyyaml==6.0.2`
- `regex>=2024.0.0`
- `sortedcontainers==2.4.0`

Useful extras:

- `pytest` for the repo's regression tests and local verification.
- `openai-agents` only for the agentic vectorless RAG demo pattern.

## Model and config defaults

The package loads defaults through `pageindex.utils.ConfigLoader`.

| Key | Default | Applies to |
| --- | --- | --- |
| `model` | `gpt-4o-2024-11-20` | Classic PDF, Markdown summaries, and default model-backed calls. |
| `summary_model` | `gpt-5.6-luna` | Summary generation when not overridden. |
| `retrieve_model` | `gpt-5.4` | `PageIndexClient` agent retrieval model default. |
| `toc_check_page_num` | `20` | Classic PDF TOC scan window. |
| `max_page_num_each_node` | `10` | Classic PDF recursive splitting threshold. |
| `max_token_num_each_node` | `20000` | Classic PDF recursive splitting threshold. |
| `if_add_node_id` | `yes` | PDF/Markdown output. |
| `if_add_node_summary` | `yes` | Default summary generation for CLI/config-driven paths. |
| `if_add_doc_description` | `no` | Default document description generation. |
| `if_add_node_text` | `no` | Default text retention in output nodes. |

Model names without a provider prefix use the OpenAI SDK. Provider/model names such as `anthropic/claude-sonnet-4-6` are routed through LiteLLM. `litellm/` and `openai/` prefixes are handled explicitly by the helper functions.

## Credentials

- `OPENAI_API_KEY` is the primary key used by OpenAI SDK-backed calls.
- `CHATGPT_API_KEY` is accepted as a backward-compatible alias when `OPENAI_API_KEY` is unset.
- The notebooks use variables named `PAGEINDEX_API_KEY`, but the core client code sets or reads `OPENAI_API_KEY`; do not assume `PAGEINDEX_API_KEY` is a special environment variable unless user code wires it in.

## Offline-friendly modes

Use these paths when credentials are unavailable:

- Flash structure only: `page_index_flash(pdf, summary=False, use_embedded_toc=False)`.
- Flash merge-only optimization: `page_index_flash(pdf, summary=False, optimize=True, optimize_expand=False)`.
- Markdown tree only: `md_to_tree(..., if_add_node_summary='no', if_add_doc_description='no')`.
- Workspace retrieval over cached JSON with `PageIndexClient(workspace=...)`.
