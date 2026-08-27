# PaperQA Settings Reference

This reference distills the runtime configuration surface for PaperQA. It is self-contained: use the bundled scripts in `../scripts/` to inspect the installed package instead of reopening source docs or tests.

## Core model

PaperQA configuration is represented by `paperqa.settings.Settings`, a Pydantic settings model. It can be supplied directly, as a nested dictionary, as JSON, or by named bundled config.

Common constructors and helpers:

```python
from paperqa import Settings
from paperqa.settings import get_settings

settings = Settings()
fast = Settings.from_name("fast")
from_dict = Settings.model_validate({"answer": {"evidence_k": 5}})
same = get_settings("fast")          # name, dict, Settings, or None
```

Important validation behavior:

- Root `Settings` ignores unknown top-level keys. A misplaced top-level field can therefore be silently ignored. Put index fields under `agent.index`, prompt fields under `prompts`, answer fields under `answer`, and parser fields under `parsing`.
- Nested models (`AnswerSettings`, `ParsingSettings`, `PromptSettings`, `AgentSettings`, `IndexSettings`) forbid unknown keys.
- `Settings.from_name("default")` is CLI-oriented; for Python defaults, use `Settings()`.
- `Settings.from_name("<name>")` first checks user settings storage, then bundled configs shipped with PaperQA.
- JSON-safe parser functions should be represented as importable fully qualified strings, for example a PDF parser function path. Arbitrary callables, callback functions, custom context serializers, and file filters are Python-only objects and are not portable settings JSON.

## Built-in named configs

The following summaries reflect installed package facts for this PaperQA version. “Default” means the field is inherited from `Settings()` unless the named config overrides it.

| Config | Main purpose | LLM roles | Embedding | Retrieval/answer shape | Notes |
| --- | --- | --- | --- | --- | --- |
| `default` | General PaperQA use | `llm`, `summary_llm`, and `agent.agent_llm` default to `gpt-4o-2024-11-20` | `text-embedding-3-small` | `evidence_k=10`, `answer_max_sources=5`, `agent_type="ToolSelector"` | Requires OpenAI-compatible credentials unless roles are changed. |
| `fast` | Cheaper/faster answers | LLM roles inherit defaults | Default | `evidence_k=5`, `answer_max_sources=3`, short summaries/answers, `agent_type="fake"` | Disables metadata lookup with `parsing.use_doc_details=false`; prompt JSON disabled. |
| `high_quality` | More evidence and larger chunks | LLM roles inherit defaults | Default | `evidence_k=20`, `answer_max_sources=5`, `max_concurrent_requests=10` | Uses `chunk_chars=7000`, `overlap=250`, metadata details enabled. |
| `debug` | Small debug runs | `llm` and `summary_llm` set to `claude-3-haiku-20240307`; `agent.agent_llm` inherits default | Default | `evidence_k=2`, `answer_max_sources=2`, `defer_embedding=true` | Still needs default provider credentials for `agent.agent_llm` and default embedding unless changed. |
| `clinical_trials` | Agent has clinical-trials search available | LLM roles inherit defaults | Default | `evidence_k=15`, `answer_max_sources=5`, `max_concurrent_requests=10` | Tool names include `clinical_trials_search`, `paper_search`, evidence, answer, and complete. Source semantics belong to `../metadata-and-sources/`. |
| `search_only_clinical_trials` | Clinical-trials-only search path | LLM roles inherit defaults | Default | `evidence_k=15`, `answer_max_sources=5` | Omits `paper_search` from tool names; source details still belong to `../metadata-and-sources/`. |
| `contracrow` | Contradiction-oriented answers | `llm`/`summary_llm=claude-3-5-sonnet-20240620`; `agent.agent_llm=gpt-4o-2024-08-06` | `hybrid-text-embedding-3-large` | `evidence_k=30`, `answer_max_sources=15` | Uses specialized contradiction prompts and direct expert tone. Mixed providers mean multiple keys may be needed. |
| `wikicrow` | Wikipedia-style article answers | `gpt-4-turbo-2024-04-09` for main, summary, and agent | `hybrid-text-embedding-3-small` | `evidence_k=25`, `answer_max_sources=12` | Uses specialized Wikipedia-style prompts and larger overlap. |
| `openreview` | OpenReview-oriented review workflows | `gemini/gemini-2.0-flash-exp` for main, summary, and agent | `ollama/granite3-dense` | Inherits default evidence counts | Uses high verbosity and very large chunk size. Configure paper directory under `agent.index.paper_directory`; do not rely on a top-level `paper_directory` key. |
| `tier1_limits` | OpenAI tier-1 throttling | LLM roles inherit defaults | Default | `evidence_k=5`, `answer_max_sources=3`, `max_concurrent_requests=5` | Adds rate limits for `llm_config`, `summary_llm_config`, and `embedding_config`; consider agent LLM limits separately. |
| `tier2_limits` | OpenAI tier-2 throttling | LLM roles inherit defaults | Default | `evidence_k=8`, `answer_max_sources=3`, `max_concurrent_requests=8` | Uses metadata details and larger chunks. |
| `tier3_limits` | OpenAI tier-3 throttling | LLM roles inherit defaults | Default | `evidence_k=8`, `answer_max_sources=3`, `max_concurrent_requests=8` | Higher token-per-minute limits than tier 2. |
| `tier4_limits` | OpenAI tier-4 throttling | LLM roles inherit defaults | Default | `evidence_k=10`, `answer_max_sources=5`, `max_concurrent_requests=8` | Higher token-per-minute limits than tier 3. |
| `tier5_limits` | OpenAI tier-5 throttling | LLM roles inherit defaults | Default | `evidence_k=15`, `answer_max_sources=5`, `max_concurrent_requests=8` | Highest bundled OpenAI limits; still verify real account limits. |

Print live summaries from the installed package:

```bash
python sub-skills/settings-and-configuration/scripts/print_named_settings.py
python sub-skills/settings-and-configuration/scripts/print_named_settings.py --json --names fast high_quality tier1_limits
```

## Settings field map

### Root `Settings`

| Field | Purpose | Operating notes |
| --- | --- | --- |
| `llm` | Main LLM for metadata inference, pre/post prompts, final answer generation, and the fake agent’s proposed searches. | Changing only this is not enough when `summary_llm`, `agent.agent_llm`, or `embedding` still point to another provider. |
| `llm_config` | LiteLLM Router-style config for `llm`. | Use `model_list` for custom providers/local servers; rate limits can live here. |
| `summary_llm` | LLM used to summarize evidence chunks. | Often the first hidden source of a missing default-provider API key. |
| `summary_llm_config` | Router/rate-limit config for `summary_llm`. | Mirror provider changes here unless intentionally mixing providers. |
| `embedding` | Embedding model name for chunk retrieval. | Defaults to an OpenAI embedding; local and hybrid forms are covered in `model-and-embedding-config.md`. |
| `embedding_config` | Extra embedding-model config. | May contain a `rate_limit` string or provider-specific arguments. |
| `temperature` | Temperature passed to LLM model construction. | Auto-overridden to `1` when top-level `llm` starts with `o1` or `gpt-5`; set it explicitly for reasoning models in other roles. |
| `batch_size` | Batch size for LLM calls. | Keep low when provider rate limits are strict. |
| `texts_index_mmr_lambda` | MMR lambda for text-vector retrieval. | Values at or above `1.0` effectively disable diversity penalty in MMR search. |
| `verbosity` | Logging verbosity, 0-3. | Level 3 logs all LLM/embedding calls; avoid using it when secrets could appear in surrounding logs. |
| `custom_context_serializer` | Python callable to serialize answer contexts. | Python-only; do not put in JSON. |

### `answer: AnswerSettings`

Use this group to control retrieval breadth, summarization, answer length, and LLM concurrency:

- `evidence_k`: number of evidence chunks to retrieve.
- `evidence_retrieval`: `false` processes all docs instead of embedding retrieval.
- `evidence_summary_length`: natural-language summary target, such as `"about 100 words"`.
- `evidence_skip_summary`: skip summarization when evidence text should be passed through.
- `evidence_text_only_fallback`: allow retrying context creation without media when a multimodal provider rejects images.
- `answer_max_sources`: maximum sources in the final answer context.
- `max_answer_attempts`: optional cap on answer-generation attempts.
- `answer_length`: natural-language final answer target.
- `max_concurrent_requests`: maximum concurrent LLM requests.
- `answer_filter_extra_background`, `get_evidence_if_no_contexts`, `group_contexts_by_question`, `evidence_relevance_score_cutoff`, `skip_evidence_citation_strip`: advanced answer/context filtering controls.

### `parsing: ParsingSettings`

Parser selection and chunking details are owned by `../docs-and-parsing/`, but these settings affect provider and prompt choices:

- `use_doc_details`: whether adding a doc should try metadata enrichment.
- `reader_config`: parser/chunker kwargs such as `chunk_chars`, `overlap`, `dpi`, `page_range`, or `full_page` when supported by the parser.
- `multimodal`: off / on without enrichment / on with enrichment. When enrichment is on, configure `enrichment_llm` and `enrichment_llm_config` as another provider role.
- `defer_embedding`: postpone embeddings until summarization/query time.
- `parse_pdf`: PDF parser function or importable string in JSON.
- `citation_prompt`, `structured_citation_prompt`, `enrichment_prompt`: prompt templates used during parsing/enrichment.
- `disable_doc_valid_check`, `doc_filters`, `use_human_readable_clinical_trials`: specialized controls; route source-specific behavior to the source or parser sub-skill.

### `prompts: PromptSettings`

Prompt settings are assignment-validated. Do not add arbitrary format variables.

| Prompt field | Allowed variable rule |
| --- | --- |
| `summary` | Variables must be a subset of the default summary prompt variables: citation, text, question, and summary length variables used by PaperQA. |
| `qa` | Variables must be a subset of the default QA prompt variables, including question/context/citation and prior-answer fields used by PaperQA. |
| `select` | Variables must be a subset of the default paper-selection prompt variables. |
| `pre` | Can use `{question}`. |
| `post` | Variables must be fields on `PQASession`. |
| `context_outer` | Variables must match the outer context formatter variables. |
| `context_inner` | Must include at least `{name}` and `{text}`. |

Fast prompt smoke check:

```python
from paperqa.settings import PromptSettings

PromptSettings(pre="Add this user constraint before answering: {question}")
PromptSettings(context_inner="{name}: {text}")
```

### `agent: AgentSettings`

Agent settings affect the agent runner and tool selection; actual query workflows belong to `../agentic-rag/`.

| Field | Purpose |
| --- | --- |
| `agent_llm`, `agent_llm_config` | LLM and Router config used by the tool-selecting agent. |
| `agent_type` | `"ToolSelector"`, `"fake"`, or supported LDP/HTTP agent classes when corresponding extras are installed. |
| `agent_config` | Extra constructor config for the selected agent. |
| `agent_system_prompt`, `agent_prompt` | System/reset prompts for the agent. |
| `tool_names` | Optional explicit tool list. If non-default, include answer generation (`gen_answer`) unless intentionally preventing answers. |
| `callbacks` | Mapping from callback names to Python callables. Python-only; not JSON. |
| `index` | `IndexSettings` controlling paper directory, manifest, index location/name, recursion, concurrency, syncing, and file filtering. Index operation belongs to `../cli-and-indexing/`. |

Known callback names include `gen_answer_initialized`, `gen_answer_aget_query`, `gen_answer_completed`, `gather_evidence_initialized`, `gather_evidence_aget_evidence`, and `gather_evidence_completed`.

## JSON examples

Minimal low-cost local JSON that changes nested fields correctly:

```json
{
  "llm": "gpt-4o-mini",
  "summary_llm": "gpt-4o-mini",
  "agent": {
    "agent_llm": "gpt-4o-mini",
    "index": {
      "paper_directory": "papers",
      "name": "my-index"
    }
  },
  "answer": {
    "evidence_k": 5,
    "answer_max_sources": 3
  },
  "parsing": {
    "use_doc_details": false,
    "reader_config": {
      "chunk_chars": 5000,
      "overlap": 250
    }
  },
  "prompts": {
    "use_json": false,
    "context_inner": "{name}: {text}"
  }
}
```

Validate before use:

```bash
python sub-skills/settings-and-configuration/scripts/validate_settings_json.py my-settings.json
```

If a setting appears to have no effect, check for a misplaced top-level key. For example, use `agent.index.paper_directory`, not a root `paper_directory` key.
