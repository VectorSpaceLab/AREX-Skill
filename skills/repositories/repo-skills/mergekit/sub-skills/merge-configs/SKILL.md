---
name: merge-configs
description: "Author, validate, and run mergekit YAML configurations for core
  model merges, layer slices, methods, tokenizer construction, chat templates,
  and resource-aware execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Core merge configuration route

Use this route when the task is to author or execute a standard
`mergekit-yaml` merge from local or Hub model references. The input is a YAML
configuration and the output is a merged model directory, with tokenizer,
model card, and validation signals according to the configuration and CLI
options.

## Route first

- Send model-reference resolution, architecture conversion, graph/IO internals,
  checkpoint serialization, and memory planning to
  [model-io-and-architecture](../model-io-and-architecture/SKILL.md).
- Send raw PyTorch, MoE, multi-stage, LoRA, tokensurgeon, and layer-shuffle
  workflows to [specialized-workflows](../specialized-workflows/SKILL.md).
- Send custom method implementation, registry evolution, graph extensions, and
  evolutionary search to [extension-and-evolution](../extension-and-evolution/SKILL.md).
- Keep this route responsible for the YAML contract, method choice, parameter
  resolution, tokenizer/chat configuration, output dtype, and execution flags.

Do not reopen a source checkout: the bundled references are the operating
catalog. Use the bundled validator before a merge; it parses YAML and validates
the Pydantic configuration without resolving or downloading any model.

## Operating procedure

1. **Normalize the request.** Record input model references, intended topology
   (`models`, `slices`, or `modules`), method, base model, tokenizer/chat
   requirements, output directory, dtype, device, and safety constraints.
2. **Validate the document.** Run
   `python scripts/validate_merge_config.py CONFIG.yml` when running from this sub-skill's directory, or `python sub-skills/merge-configs/scripts/validate_merge_config.py CONFIG.yml` from the generated skill root.
   A successful parse is necessary, not sufficient: it does not inspect model
   files, architecture compatibility, tensor shapes, or tokenizer availability.
3. **Choose one topology.** A top-level configuration must contain exactly one
   of `models`, `slices`, or `modules`. Use `models` for whole-model merges,
   `slices` for a single-module layer assembly, and `modules` for explicit
   multi-module layouts. Never combine these fields at the same level.
4. **Choose a registered method.** Match model count and `base_model` rules in
   [merge-methods.md](references/merge-methods.md). Put required per-model
   values such as `weight` on each model/source and global values in
   `parameters`.
5. **Resolve parameters deliberately.** Apply the source-model, output-slice,
   module, then top-level precedence order. Use filtered conditional settings
   for tensor names and numeric lists for layer gradients; test fallback values
   for tensors that do not match a filter.
6. **Configure tokenizer and chat separately.** Prefer modern `tokenizer` for
   union/base/model selection and per-token embeddings. Use legacy
   `tokenizer_source` only for compatibility; they are mutually exclusive. Set
   `chat_template` only when a tokenizer will be saved.
7. **Set compute and output policy.** `dtype` controls input tensor loading and
   is also the output config fallback; `out_dtype` controls saved tensors and
   takes precedence in the output config. Select CPU or CUDA flags from actual
   RAM/VRAM and backend availability, not from model size alone.
8. **Run and inspect.** Use the exact CLI shape below, retain the command and
   validator output, and inspect the output config, shard files, tokenizer, and
   model card. Treat warnings about missing tokenizers, unsupported templates,
   optional dependencies, or memory as actionable signals.

## Core command

```text
mergekit-yaml CONFIG.yml OUT_DIR [OPTIONS]
```

Important flags are `--device TEXT`, `--cuda/--no-cuda`, `--low-cpu-memory`,
`--read-to-gpu`, `--multi-gpu`, `--gpu-rich`, `--lazy-unpickle`,
`--num-threads/-j`, `--out-shard-size SIZE`, `--safe-serialization`,
`--copy-tokenizer/--no-copy-tokenizer`, `--write-model-card/--no-write-model-card`,
`--async-write`, `--write-threads`, `--transformers-cache`,
`--lora-merge-cache`, `--lora-merge-dtype`, `--random-seed`, `-v`, `--quiet`,
`--trust-remote-code`, and `--allow-crimes`. Confirm the installed help before
using a flag in automation; the bundled reference records the inspected
interface.

## Success and failure gates

A merge is usable only when YAML validation succeeds, all references resolve,
the selected method accepts the effective input set, tensors are written
without NaN/shape/device errors, and the output metadata matches the requested
configuration. For tokenizer work also check vocabulary size, forced token
embeddings, `config` vocabulary size when padding was requested, and the saved
chat template. For a failed run, classify it with
[troubleshooting.md](references/troubleshooting.md) before changing the YAML.

Read the focused details progressively:

- [configuration.md](references/configuration.md): schema, topology, precedence,
  gradients, dtype, and a minimal authoring checklist.
- [merge-methods.md](references/merge-methods.md): registered methods, model
  cardinality, base-model constraints, and parameters.
- [tokenizer-and-chat.md](references/tokenizer-and-chat.md): modern/legacy
  tokenizer semantics, embeddings, padding, and chat templates.
- [troubleshooting.md](references/troubleshooting.md): concrete symptoms,
  diagnoses, and recoveries for install, schema, references, methods,
  tokenizer/chat, serialization, and devices.

## Minimal handoff

Report the config path, chosen topology and method, effective base model,
parameter overrides and filters, tokenizer/chat policy, exact command flags,
output directory, validator result, run result, and any unresolved warning.
Do not claim success from a parse-only check or from an output directory that
lacks the expected model/config artifacts.
