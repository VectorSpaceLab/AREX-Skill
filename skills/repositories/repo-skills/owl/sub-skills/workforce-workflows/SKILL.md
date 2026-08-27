---
name: workforce-workflows
description: "Guides OWL Workforce and CAMEL multi-agent workflows, provider
  selection, model configuration, worker/tool composition, and safe task
  execution planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OWL Workforce Workflows

Use this route when the task is to configure or run OWL's hierarchical
CAMEL Workforce, select a remote model provider, assemble specialist workers,
or understand the custom role-playing loop. It covers the provider-backed
runtime; it does not claim that a model call or browser session is available.

## Start here

1. Install OWL in an isolated Python 3.10–3.12 environment and run the root
   environment check before constructing a model.
2. Choose one provider in [provider-recipes.md](references/provider-recipes.md).
   Keep provider credentials separate from optional search, crawling, or
   document-service credentials.
3. Validate a non-secret environment file with
   [validate_provider_config.py](scripts/validate_provider_config.py) before
   calling CAMEL's `ModelFactory`.
4. Read [toolkit-composition.md](references/toolkit-composition.md) when the
   task needs browser, search, code, spreadsheet, file, image, or document
   tools.
5. Use [scaffold_workforce.py](scripts/scaffold_workforce.py) when a safe,
   non-executing configuration skeleton is more useful than copying a
   credentialed example.
6. Build the Workforce and pass a `camel.tasks.Task` containing the complete
   user request. Use [role-playing-api.md](references/role-playing-api.md)
   only when the task needs OWL's custom two-agent loop or GAIA mode.

## Canonical workflow

- Create provider-specific model backends with `camel.models.ModelFactory`.
- Construct specialist models for web, document, reasoning, image, browsing,
  and planning roles as needed. A model that cannot call tools is not a valid
  substitute for a tool-intensive worker.
- Create toolkit instances, wrap individual methods with `FunctionTool` when
  required, and add toolkit tools to the appropriate `ChatAgent`.
- Add worker agents to a `camel.societies.Workforce` with descriptions that
  make their boundaries discoverable. Add a task and call `workforce.process_task`.
- Pass a user question as the first command-line argument to a provider example
  rather than editing a credential into code. For a reusable starting point,
  generate a non-executing skeleton with `scaffold_workforce.py`.
- For local files, route document-specific behavior to
  [document-processing](../document-processing/SKILL.md). For the Gradio
  front end or Docker, route to
  [web-ui-and-deployment](../web-ui-and-deployment/SKILL.md).

## Safety and limits

Remote provider calls, search, Firecrawl, browser automation, and code
execution can incur cost or perform external side effects. Confirm credentials,
network access, browser policy, and output paths before execution. Keep
`CodeExecutionToolkit` in its intended sandbox and do not expose unrestricted
file or terminal tools to untrusted tasks. A CPU import check proves only that
OWL and CAMEL import; it does not prove provider tool calling or multimodal
quality.

Read [troubleshooting.md](references/troubleshooting.md) when import errors,
missing keys, endpoint failures, stale example names, or tool capability
mismatches appear. The source examples are evidence for this skill, not files a
future agent must reopen or execute from the original checkout.
