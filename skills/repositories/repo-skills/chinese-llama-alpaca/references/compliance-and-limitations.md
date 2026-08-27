# Compliance and Limitations

## Licensing and Access

This repository states that the original LLaMA model weights are not redistributed here because of the original license terms. The project provides LoRA adapters, tokenizer assets, scripts, and examples.

Treat the bundled material as research guidance. Do not claim it authorizes commercial use of the underlying model family. If a user needs actual model weights, they must supply a licensed copy or follow the relevant upstream policy.

## Safety and Service Boundaries

- Long-running training, serving, and large model reconstruction can consume substantial GPU, RAM, disk, and network resources.
- Public or shared Gradio/API deployment should be an explicit user decision.
- OpenAI-style prompt crawling requires credentials and network access and is intentionally not bundled as a runnable helper.
- Example benchmark tables are comparative and prompt-set-specific, not universal claims of truth.

## Citation

When the user needs to reference the repository academically, cite the paper listed in the README and note that the skill summarizes public scripts, example tables, and workflow guidance rather than redistributing original weights.

## Practical Limitations

- This skill cannot load or verify original model quality without the user-provided assets.
- CPU-only runs can help with parser/static checks, but they are not a substitute for GPU verification when model execution is the goal.
- The generated skill never embeds private environment paths, API keys, or original checkout-only dependencies.
