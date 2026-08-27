# Recipe Index and Selection Guide

## Purpose

Read this when a user asks which DataDesigner tutorial or recipe to adapt. The goal is to choose the smallest safe pattern, not to reproduce the large source notebooks or recipe generators.

If the task turns into exact column/class authoring, switch to [`../../config-authoring/SKILL.md`](../../config-authoring/SKILL.md). If it turns into validate/preview/create/export execution, switch to [`../../generation-runtime/SKILL.md`](../../generation-runtime/SKILL.md).

## Selection shortcuts

| User request | Start from | Why | Execution classification |
| --- | --- | --- | --- |
| First synthetic dataset, samplers, LLM text | Basics tutorial pattern | Shows `DataDesigner`, `DataDesignerConfigBuilder`, samplers, dependent LLM text, preview, create, and analysis | Credentialed if LLM columns run; config-only validation is local |
| Structured JSON, Jinja expressions, conditional generation | Structured outputs tutorial pattern | Shows Pydantic output, nested field expressions, `SkipConfig`, propagation, and review iteration | Credentialed if LLM columns run |
| Existing CSV/JSON/Parquet/JSONL as seed | Seeding tutorial pattern | Shows `LocalFileSeedSource`, seed columns used as Jinja variables, and preview-before-create | Local seed validation; model generation credentialed |
| Simple text-to-SQL | `text_to_sql.py` pattern | Sampler diversity + `LLMCodeColumnConfig` + code validator + judge | Reference-only: requires remote model/API keys |
| Enterprise text-to-SQL with dialects, distractors, dirty data | `enterprise_text_to_sql.py` pattern | Adds SQL dialect control, conditional sampling, distractor schema/data, data-quality challenges, and multi-judge scoring | Reference-only: large API-driven recipe |
| Text-to-Python or code SFT rows | `text_to_python.py` pattern | Uses code-generation column, code validation, and Pythonic/readability/efficiency judges | Reference-only: remote model/API keys |
| Local MCP toy tools | `basic_mcp.py` pattern | Minimal local stdio MCP server with allowed tools and trace capture | Reference-only in this skill; MCP setup belongs to plugins-and-extensions and model calls need credentials |
| PDF-grounded Q&A | `pdf_qa.py` pattern | Local/URL PDF extraction, BM25 lexical index, MCP `search_docs`, structured Q&A | Reference-only: network PDF path optional, model/API keys, recipe dependencies |
| Live search agent trajectories | `search_agent.py` pattern | Hosted Tavily MCP search, full tool traces, JSON formatting | Reference-only: Tavily key, remote web/network, model/API keys |
| Multi-turn or product info chat | QA/chat recipe patterns | Prompt and seed structures for conversational rows | Reference-only: model/API keys |
| Human review gate between stages | `document_review_gate.py` pattern | Local sample image/metadata generation, review candidate export, reviewed artifact, resume with stage override | Local dry-run pattern; large generator not bundled |
| Agent rollout trace distillation | `agent_rollout_distillation.py` pattern | `AgentRolloutSeedSource`, digest, SFT record, judge, flattened score columns | Reference-only: private traces and model/API keys |
| Rich synthetic images | Fern image recipe patterns | `ImageColumnConfig`, sampler-controlled prompts, OpenRouter image `extra_body`, image metadata | Reference-only: image provider key; synthetic-safety caveats |
| Long-document OCR/VQA/judge pipeline | VLM long-document recipe sequence | Seed parquets of base64 PNGs, OCR, page classification, text/visual QA, frontier judge | Reference-only: network seed prep and GPU/Docker/vLLM services |
| Export a generated dataset to Hugging Face | Hub export integration | Result-level `push_to_hub` or folder-level client upload | Credentialed upload; local structure checks are safe |
| Plugin package/custom seed reader | Plugin-development recipe | Extension and discovery are not owned here | Route to plugins-and-extensions |

## Tutorial notebook patterns

Use tutorial patterns when the user is learning the core workflow or wants a small end-to-end adaptation:

1. **Basics** — model configs, category/subcategory/person-from-faker/uniform samplers, LLM text columns, `validate`, `preview`, `create`, `load_dataset`, and `load_analysis`.
2. **Structured outputs/Jinja/conditional generation** — Pydantic schemas, nested field references, conditional sampler params, `skip.when`, default skip propagation, and `propagate_skip=False` for null-tolerant downstream columns.
3. **Seed dataset** — create or read a seed file, pass `LocalFileSeedSource`, reference seed columns directly in prompts, and use preview to inspect quality before create.
4. **Images as context** — turn image bytes into base64 seed columns, pass them through `ImageContext`, and use a VLM alias that supports the modality.
5. **Image generation** — use `ImageInferenceParams` and `ImageColumnConfig`; preview stores base64 in memory while create writes images and stores relative paths.
6. **Image editing** — chain one `ImageColumnConfig` into another with `ImageContext`; requires an autoregressive image model that accepts image context.

Do not execute notebooks just to adapt a recipe unless the user explicitly wants notebook execution and has provided the needed API keys, dependencies, and cache policy. For notebook cache/profile issues, read `troubleshooting.md`.

## Source-script decisions

No source recipe script is bundled in this sub-skill. The recipes are intentionally distilled into references because the useful future behavior is selecting and adapting patterns, not re-running large source files.

| Source recipe family | Decision | Concrete reason |
| --- | --- | --- |
| Tutorial notebook sources | Reference-only | Large notebook generators; most examples call remote model providers or datasets; distilled patterns are enough for future adaptation |
| Code/SQL recipes | Reference-only | Require OpenAI/NVIDIA model keys and contain large prompt/judge templates; adapt the column graph and rubric shape instead |
| MCP/tool-use recipes | Reference-only, route setup to plugins-and-extensions | Need MCP server/provider configuration, external model keys, and sometimes Tavily or PDF network access |
| QA/chat recipes | Reference-only | Model/API-backed examples; adapt prompt and seed structures only |
| `document_review_gate.py` | Reference-only with safe dry-run guidance | Local and test-backed, but it is a large demonstration generator; future agents should reuse the artifact pattern and validations, not copy the full generator |
| `agent_rollout_distillation.py` | Reference-only | Reads private/local assistant traces and uses LLM digest/judge columns; safe work is trace inventory and config planning |
| VLM long-document scripts | Reference-only | Seed prep downloads PDFs; OCR/VQA/judge scripts require local vLLM endpoints, Docker, GPUs, and large models |
| Fern image-generation recipes | Reference-only | Require image-generation provider keys; some domains include medical, autonomy, drone, or robotics caveats that need user review |
| Markdown seed-reader plugin recipe | Excluded from this sub-skill | It demonstrates custom seed-reader/extension mechanics owned by plugins-and-extensions |
| Hugging Face integration source | Distilled reference | Upload logic is small enough to summarize, but direct hub calls are credentialed and should be preflighted |

## Native verification candidates to preserve for later verification

These are useful verification candidates for the whole repo skill, not instructions to run original repo tests at runtime:

- Docs workflow invariants: notebook cache context, retry settings, cache disable behavior, and notebook snapshot behavior.
- Image recipe construction: image recipes build configs with OpenRouter chat image request shape: `extra_body` has `modalities` and `image_config`, and does not use `generationConfig`.
- Rich document image export: created image paths can be converted to a VQA-ready seed parquet with `image_base64`, `image_format`, MIME type, width/height, and metadata columns.
- Workflow review gate: local sample pages produce valid image bounds, supported labels, review candidates, reviewed artifacts, and final dataset rows.
- Hugging Face export tests: client handles repo creation/update, parquet upload, images upload, processor outputs, config files, dataset-card generation, invalid repo ids, missing files, invalid JSON, authentication, and permission errors.

## Synthetic usability cases this sub-skill should support

1. **Text-to-SQL route selection without network calls.** Given a user asking for a text-to-SQL dataset, choose between a tutorial-like basic plan and the enterprise recipe plan, then produce only a config-outline/dry-run validation plan that names required model aliases, validators, judges, and safe local checks.
2. **Workflow review gate dry-run.** Given a request to add human review before final generation, turn the review-gate pattern into a dry-run plan that checks local artifact names, required columns, reviewed parquet shape, and resume override logic without calling remote models.
