---
name: recipes-and-integrations
description: "Use when adapting DataDesigner tutorial notebooks, documented
  recipes, workflow chaining, trace ingestion, multimodal/image/VLM patterns, or
  Hugging Face export plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Recipes and Integrations

Use this sub-skill when the user wants to adapt a DataDesigner tutorial, recipe, or integration pattern rather than design a schema from scratch.
It is a route and safety guide, not a catalog of every config object.

## Typical triggers

- "Turn the text-to-SQL recipe into a safer dry-run plan"
- "Adapt the image generation notebooks for my product images"
- "Use MCP/tool calls in a dataset recipe"
- "Ingest agent traces into an SFT dataset"
- "Chain a review step between two generation stages"
- "Export a generated dataset to Hugging Face"
- "Which tutorial or advanced recipe should I start from?"

## What this sub-skill owns

- Selecting between tutorial notebooks, code/SQL recipes, MCP/tool-use recipes, image recipes, VLM long-document recipes, trace-ingestion recipes, workflow chaining, and Hugging Face export.
- Converting large source recipes into small, task-specific DataDesigner plans without depending on the original checkout.
- Classifying a recipe as safe local, credentialed, network-bound, GPU/Docker-bound, or reference-only.
- Planning external-data and seed handling at the recipe level.
- Planning human review gates and workflow chaining dry-runs.
- Calling out optional dependency groups, remote endpoints, API keys, downloads, and hardware before execution.

## Boundaries and required cross-links

- For exact column/config classes, seed source fields, person sampling, Pydantic schemas, Jinja expressions, validators, processors, or custom-column syntax, read [`../config-authoring/SKILL.md`](../config-authoring/SKILL.md).
- For `DataDesigner.validate`, `preview`, `create`, `check_models`, artifact loading, resume, local export, and base workflow APIs, read [`../generation-runtime/SKILL.md`](../generation-runtime/SKILL.md).
- For MCP provider setup, `ToolConfig`, plugin entry points, plugin install/discovery, or installed-plugin inspection, read [`../plugins-and-extensions/SKILL.md`](../plugins-and-extensions/SKILL.md).
- For CLI model/provider/persona state, especially `data-designer agent context`, read [`../cli-and-agent-tools/SKILL.md`](../cli-and-agent-tools/SKILL.md).

Do not duplicate detailed API tables from those sub-skills. This sub-skill explains how documented recipes are chosen, adapted, constrained, and exported.

## Read these first

- [`references/recipe-index.md`](references/recipe-index.md) — choose the right recipe family and see which source scripts are reference-only, excluded, or locally dry-runnable.
- [`references/multimodal-image-and-vlm.md`](references/multimodal-image-and-vlm.md) — adapt image context, image generation, image editing, rich document images, and long-document VLM recipes safely.
- [`references/workflow-chaining-and-trace-ingestion.md`](references/workflow-chaining-and-trace-ingestion.md) — plan composite workflows, review gates, selected stage outputs, and agent-rollout trace ingestion.
- [`references/huggingface-export.md`](references/huggingface-export.md) — export local artifacts or push generated datasets to Hugging Face Hub without leaking unsafe metadata.
- [`references/troubleshooting.md`](references/troubleshooting.md) — diagnose API keys, notebook cache/profile behavior, remote endpoints, image `extra_body`, base64 media, MCP servers, dependency groups, GPU/Docker VLM services, Hub tokens, and large downloads.

## Safe adaptation workflow

1. **Identify the recipe class.** Decide whether the user needs a beginner tutorial pattern, an advanced recipe pattern, an integration export, or only a reference-only plan.
2. **Classify execution risk before running anything.** Mark each dependency as local-only, remote model/API, MCP/server, network download, credentialed upload, GPU/Docker service, or large/private data.
3. **Reduce the recipe to the smallest plan.** Extract the relevant column graph, seed assumptions, model alias needs, validation points, and output artifacts. Do not copy large recipe scripts into the answer or generated project unless a small self-contained helper is truly needed.
4. **Route API details to the owning sub-skill.** Use config-authoring for object fields and generation-runtime for validate/preview/create/export calls.
5. **Use local dry-run checks whenever possible.** Validate readable local seed files, image/base64 shapes, expected output columns, workflow artifact names, and Hugging Face folder structure before any network or model call.
6. **Ask before credentialed or GPU-heavy execution.** API keys, Tavily web search, OpenRouter/OpenAI/NVIDIA endpoints, Hugging Face uploads, FinePDF/PDF downloads, local vLLM Docker services, and multi-H100 VLM recipes are not safe implicit actions.
7. **Preserve reviewability.** For adapted recipes, leave a concise plan that states what was executed, what was only validated locally, what remains unverified, and which credentials/hardware are required.

## Good finish line

A future agent should be able to choose the right recipe family, produce a self-contained adaptation plan or config script, avoid unsafe executions, know which sibling sub-skill owns exact API details, and explain how to verify or export artifacts without reopening the original repository.
