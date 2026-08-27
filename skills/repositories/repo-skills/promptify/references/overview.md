# Promptify Overview

## Purpose

Read this for a quick map of the current public API before diving into the sub-skills. It summarizes the import paths that matter most for day-to-day Promptify use.

## Current public surface

### Top-level imports
These are available from `from promptify import ...`:

- NER
- Classify
- QA
- Summarize
- Task
- ExtractRelations
- ExtractTable
- GenerateQuestions
- GenerateSQL
- NormalizeText
- ExtractTopics
- ModelConfig
- setup_logging
- get_cost_summary
- __version__

### Submodule imports
These are available from their home modules when a task needs lower-level control:

- promptify.core: ModelConfig, CacheConfig, PromptifyError, setup_logging
- promptify.core.config: ModelConfig, CacheConfig
- promptify.engine.llm: LLMEngine, LLMResponse
- promptify.parser: Parser
- promptify.prompts: PromptBuilder
- promptify.eval: evaluate
- promptify.eval.datasets: load_dataset

## How to choose a route

- Use structured-tasks when the user is creating a task object, customizing prompt variables, or debugging JSON output from a model call.
- Use evaluation when the user wants to score task outputs against labeled examples or load a CSV or JSON evaluation dataset.

## Advanced note

CacheConfig exists in promptify.core, but task execution does not automatically wire PromptCache into BaseTask. Treat cache support as an advanced extension point, not a first-class workflow.

## Legacy API warning

The old tutorial material in the repository may mention Prompter, OpenAI, and Pipeline. Those names are not part of the current exported API. Use the task classes and evaluation helpers listed above.
