---
name: model-runtime
description: "Explain LightLLM model-family support, backend selection,
  quantization, and registry behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# model-runtime

Use this sub-skill when the question is about whether a model family is
supported, which backend or quantization mode to choose, how the registry picks
an implementation, or how to add a new model support path.

## Covers

- Model registry behavior and conditional model selection.
- Supported model families and multimodal / reward / RL variants.
- Backend and quantization compatibility choices.
- Tokenizer, load-way, and runtime flag selection for a model class.
- Guidance for adding or refreshing a model integration.
- Operational use of backend validators and fallback flags.

## Does not cover

- Launch topology, port planning, or PD process sequencing.
- HTTP request payloads and client-facing API syntax.
- Benchmark procedures beyond the model support assumptions they require.

## Read first

- [references/model-support.md](references/model-support.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [../../references/cli-reference.md](../../references/cli-reference.md)
- [../../references/troubleshooting.md](../../references/troubleshooting.md)

## Use this route when the user says

- “is model X supported?”
- “which backend should I use for this model?”
- “why does the registry pick a different class?”
- “how do I add a new model implementation?”
- “what does this quantization or multimodal flag mean?”

## Minimal working sequence

1. Identify the model family and modality from the user request.
2. Check the support notes and any conditional registry rules.
3. Confirm the chosen backend, quantization, and tokenizer/load strategy.
4. If a backend is optional or unavailable, say so explicitly rather than
   treating a CPU import as proof of GPU support.
5. If the user wants a new model integration, use the add-new-model guidance as
   the checklist for source files, config hooks, and tests.

## Decision points

- Use `--trust_remote_code` only when the model cards or docs require it.
- Prefer the model family’s documented tokenizer mode and load strategy.
- Treat `--enable_multimodal`, `--disable_vision`, and `--disable_audio` as
  model-selection controls, not mere service flags.
- When backend probes fail, separate the supported-model claim from the
  runtime-host claim.
- Keep fallback flags (`--enable_torch_fallback`, `--enable_triton_fallback`)
  explicit in the final recommendation.

## Related helpers

- `../../scripts/model_module_roster.py` lists the installed package’s model
  subpackages without depending on the original checkout.
- `../../scripts/inspect_start_args.py` helps confirm the runtime flags that
  influence backend selection.

## Troubleshooting highlights

- A registry miss usually means the model family is not registered or the
  conditional match did not fire.
- A successful import does not prove the requested backend is valid.
- Quantization mismatches often show up as backend validator failures or model
  load-time assertions.
- Multimodal models may need explicit vision/audio enablement or disablement.
- Unsupported combination errors are more useful than a silent CPU fallback;
  treat them as the source of truth.

## Review standard

This sub-skill is complete when a future agent can:

- identify the right model family,
- explain why the registry picked a given implementation,
- choose an appropriate backend or fallback,
- and outline the steps for a new model integration without reopening the
  source repository.
