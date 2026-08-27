---
name: specialized-workflows
description: "Route mergekit's first-class specialty commands for raw tensor,
  MoE, multi-stage, LoRA, tokenizer-transplantation, layer-shuffle, and
  compatibility workflows with exact inputs, outputs, prerequisites, and safe
  stop conditions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Specialized Workflows

Use this route when the request names a mergekit specialty entry point or asks
for raw checkpoint merging, dense-to-MoE conversion, a multi-document merge
pipeline, PEFT-compatible LoRA extraction, tokenizer transplantation, random
layer assembly, or a legacy compatibility wrapper. This is a command-routing
skill, not a replacement for core merge configuration or model loading.

## Route quickly

- `mergekit-pytorch`: merge arbitrary local `.pt`, pickle, or safetensors
  tensors from a raw merge YAML. Use `--tensor-intersection` or
  `--tensor-union`; raw configs do not support slices or tokenizer settings.
- `mergekit-moe`: combine same-family dense models into a Mixtral, DeepSeek,
  Qwen2, or Qwen3 MoE when the installed transformers and architecture probes
  support it. Select gate mode deliberately; random gates are a training
  initialization, not a finished model.
- `mergekit-multi`: execute YAML documents as a named intermediate dependency
  graph. Keep names unique and reserve one unnamed document for the final
  output.
- `mergekit-extract-lora`: subtract a base checkpoint from a fine-tuned model,
  decompose the task vectors, and write a PEFT-style adapter.
- `mergekit-tokensurgeon`: transplant the donor tokenizer and vocabulary into
  the base model, choosing an approximation method for donor-only tokens.
- `mergekit-layershuffle`: generate a random passthrough slice configuration;
  use `--dry-run` or `--write-yaml` before allowing an actual merge.
- `mergekit-legacy` and `bakllama`: compatibility-only routes. Prefer modern
  YAML and use these only when an old invocation/config must be preserved and
  its installed entry point is verified.

Start with [cli-reference.md](references/cli-reference.md), then open only the
workflow reference that matches the route. Use
[multistage-and-raw-pytorch.md](references/multistage-and-raw-pytorch.md) for
raw and multi-stage work, [moe.md](references/moe.md) for MoE, and
[lora-and-tokensurgeon.md](references/lora-and-tokensurgeon.md) for LoRA or
tokenizer transplantation. Keep failure recovery in
[troubleshooting.md](references/troubleshooting.md).

## Operating protocol

1. Record the input paths or Hub references, config path, intended output path,
   architecture/family, available device, and whether network or credentials
   are allowed. Resolve local files before constructing a command.
2. Validate the specialty-specific contract without downloading models or
   running a full merge. Use the bundled safe help/config probe when a command
   surface or local multi-stage naming graph needs a preflight:
   `python scripts/specialized_cli_probe.py --help-check` or
   `--check-multistage CONFIG`.
3. Construct the exact command from the reference. Add only justified common
   performance/output flags. Treat `--trust-remote-code`, `--allow-crimes`,
   remote model resolution, and output-overwrite choices as explicit approvals,
   not defaults.
4. Stop before execution when a required model, donor, tokenizer, config,
   optional extra, supported architecture, tensor shape contract, or output
   safety decision is unresolved. Prefer a tiny local fixture for verification;
   do not use a full merge as a smoke test.
5. After a permitted run, check the documented output markers and preserve the
   generated config/card/adapter metadata. Do not claim that a model is
   usable merely because a writer completed; validate architecture and the
   downstream loader separately.

## Boundaries and links

- Core YAML schema, merge-method semantics, parameter precedence, tokenizer
  fields, and chat templates belong to
  [merge-configs](../merge-configs/SKILL.md). Link there rather than explaining
  ordinary merge configuration here.
- Model references, architecture inference/conversion, checkpoint IO, memory,
  devices, sharding, and backend debugging belong to
  [model-io-and-architecture](../model-io-and-architecture/SKILL.md).
- Custom methods, graph extensions, and `mergekit-evolve` belong to
  [extension-and-evolution](../extension-and-evolution/SKILL.md); `cma`-blocked
  evolution is not a specialty workflow in this route.
- For common configuration or model failures, cross-link
  [troubleshooting.md](references/troubleshooting.md) and then hand off to the
  owning sibling instead of duplicating its contract.

The command surface and caveats in the bundled references are version-bound to
the inspected mergekit checkout. They are intentionally self-contained and do
not require reopening that checkout.
