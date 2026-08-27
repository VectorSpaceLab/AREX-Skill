# AI workflows reference

## What the AI helpers do

Mage's AI helpers can generate pipelines from descriptions, generate blocks from descriptions, generate block documentation, generate pipeline documentation, and generate comments for existing code.

## Main entry points

### CLI command group

`mage_ai.ai.generator_cmds` exposes commands for block documentation, pipeline documentation, block generation from a description, pipeline generation from a description, and comment generation for a block file.

### Wizard class

`LLMPipelineWizard` is the higher-level async orchestrator that coordinates prompt construction and output shaping.

## Configuration model

The config objects in `mage_ai.orchestration.ai.config` are simple dataclasses: `AIConfig`, `OpenAIConfig`, and `HuggingFaceConfig`.

## OpenAI path

- Requires an API key.
- Can read the key from the repo config or from the `OPENAI_API_KEY` environment variable.
- Uses the OpenAI client path for pipeline/block generation and docs.

## Hugging Face path

- Requires an endpoint and token.
- Reads its settings from the repo config or from the Hugging Face environment variables.
- The endpoint must be reachable for any live generation.

## Prompted workflow summary

1. Resolve the AI mode.
2. Build a prompt from the description or source code.
3. Ask the selected client for a structured response.
4. Turn that response into block or documentation output.
