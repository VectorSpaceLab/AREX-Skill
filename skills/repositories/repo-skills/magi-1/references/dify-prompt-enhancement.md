# Dify prompt enhancement asset

The repository bundles a Dify workflow DSL for improving prompt quality before MAGI-1 generation. Use this reference when the user asks about prompt enhancement, Dify import, or adapting the MAGI-1 prompt-rewrite workflow.

## Bundled asset

The DSL is copied into this generated skill at:

- [prompt_enhancement_dify_dsl.yml](prompt_enhancement_dify_dsl.yml)

It is a Dify workflow app definition. The source README describes importing it into Dify to set up a prompt enhancement pipeline.

## When to use it

Use the Dify DSL when:

- The user wants to improve a terse image/video prompt before passing it to MAGI-1.
- The user already operates Dify and wants an importable workflow asset.
- The task is to explain or adapt the prompt enhancement flow rather than run MAGI inference directly.

Do not use the DSL as a replacement for MAGI config validation, model weights, or source/ComfyUI runtime setup. The output prompt still needs to be supplied to source CLI/API inference or the ComfyUI prompt node.

## Import and adaptation checklist

1. Open Dify and create/import an app from a DSL/YAML file.
2. Import the bundled `prompt_enhancement_dify_dsl.yml`.
3. Configure any LLM provider credentials required by the Dify installation.
4. Test with a short prompt and inspect the enhanced output.
5. Copy the enhanced prompt into the MAGI source CLI/API or ComfyUI `Load Prompt` node.

## Safety notes

- The DSL may refer to provider-specific marketplace plugins and model settings. Adapt those to the user's Dify deployment instead of assuming provider credentials are already configured.
- Do not paste private image paths, credentials, or user-sensitive prompt content into shared Dify instances without user approval.
- Prompt enhancement can change style and specificity; preserve user intent when adapting the system prompt or workflow nodes.
