---
name: structured-tasks
description: "Routes Promptify task construction, prompt building, parsing,
  async and batch execution, custom Pydantic schemas, and provider-side task
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Structured Tasks

Use this sub-skill when the user wants to create or run Promptify task objects, customize prompts, debug structured JSON output, or understand how task kwargs flow into the model and template layers.

## Covered workflows

- NER, classification, QA, summarization, extraction, question generation, SQL generation, text normalization, topic extraction, and generic custom Task objects.
- Prompt rendering with built-in Jinja templates or custom template files.
- Parsing model output into Pydantic models, including fallback parsing when a provider does not return strict JSON.
- Sync, async, and batch task execution.
- Provider and LiteLLM failures such as auth, timeout, rate limit, and malformed response errors.

## Read first

- `references/task-catalog.md` for the built-in task families and their key arguments.
- `references/api-reference.md` for verified signatures and the split between model kwargs and template kwargs.
- `references/workflows.md` for practical recipes, mock-engine usage, async calls, and batch patterns.
- `references/troubleshooting.md` for provider, parse, template, and legacy-API mismatch errors.
- `../../scripts/check_promptify.py --mode tasks` for a no-network smoke test.

## Route boundaries

### Include here
- Choosing the correct task class for a natural-language request.
- Supplying domain, labels, examples, schema, rules, max_length, key_points, num_questions, and num_topics.
- Building prompts with built-in or custom templates.
- Handling model kwargs such as temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, timeout, and max_retries.
- Interpreting `ParserError`, `TemplateNotFoundError`, and provider-level LiteLLM errors.

### Exclude or route elsewhere
- Dataset loading, metric selection, ROUGE, and evaluator results go to `../evaluation/SKILL.md`.
- Repo maintenance or publication tasks do not belong here.
- Archived notebook or tutorial names such as Prompter, OpenAI, and Pipeline are not the current API.

## Mental model

Promptify task objects are thin routers around a shared execution stack:

1. A task class chooses a built-in template and output schema.
2. `BaseTask` splits model kwargs from template kwargs.
3. `PromptBuilder` renders the prompt into OpenAI-style messages.
4. `LLMEngine` sends the messages to LiteLLM.
5. The response is parsed into the requested Pydantic shape.

This sub-skill exists so future agents do not need to reopen the source code to remember that flow.

## Use this route when the user asks for

- "Create a medical NER task with labels and examples"
- "Run QA with a custom question and domain"
- "Build a custom structured output schema"
- "Use batch mode or async with Promptify"
- "Fix a parser or template failure"
- "Understand which kwargs belong to the model and which belong to the template"

## When to switch to evaluation

If the user asks about `load_dataset`, `evaluate`, exact match, accuracy, F1, precision, recall, or ROUGE, switch to the evaluation sub-skill instead of expanding this one.
