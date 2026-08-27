---
name: ai-workflows
description: "Mage AI-assisted pipeline generation, documentation, and model configuration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# AI Workflows

Use this route for Mage's AI-assisted code and documentation helpers.

## Owns

- Pipeline generation from descriptions
- Block generation from descriptions
- Block and pipeline documentation generation
- Comment generation for existing code
- OpenAI and Hugging Face AI client configuration
- AI setup and credential troubleshooting

## Excludes

- Manual block authoring, which belongs in `pipeline-authoring`
- Connector or `io_config` setup, which belongs in `batch-integrations`
- Streaming connectors, which belong in `streaming`
- dbt orchestration, which belongs in `dbt-workflows`
- CLI/bootstrap/auth/logging, which belongs in `platform-ops`

## Use this route when

- The user asks Mage to generate a pipeline or block from a prompt
- The user wants docs or comments generated for code already in the repo
- The user needs to configure or debug AI model access for Mage features

## Bundled reference

Read `references/ai-workflows.md` for the AI command matrix, config objects, and setup notes.

## Bundled script

- `scripts/check_ai_config.py` — safe AI-mode and credential inspection without calling a live model

## Core reminders

- The code supports both OpenAI and Hugging Face client paths.
- AI features require a valid API key or endpoint configuration.
- Mage Pro chat features exist in the repo, but the OSS generation helpers are the main workflow in this skill.
