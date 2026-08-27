---
name: model-io-and-architecture
description: "Resolve mergekit model references, infer compatible architectures,
  plan task graphs, choose devices and serialization, and diagnose checkpoint
  and IO failures without the source checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Model IO and architecture route

Use this route when a merge depends on **what a model reference resolves to**,
**which checkpoint names and architecture the output uses**, or **where tensor
bytes live while the graph runs**. This is operating guidance for an installed
mergekit 0.1.4 environment; it does not require reopening the source checkout or
downloading a model merely to understand the decisions.

## Route boundaries

- Send YAML topology, merge-method selection, parameter precedence, tokenizer
  configuration, chat templates, and output dtype to
  [merge-configs](../merge-configs/SKILL.md).
- Send named specialty CLIs, raw PyTorch/MoE/multi-stage/LoRA workflows,
  tokensurgeon, and layer-shuffle to
  [specialized-workflows](../specialized-workflows/SKILL.md).
- Send custom task or method implementation, registry changes, graph
  extensions, and evolutionary search to
  [extension-and-evolution](../extension-and-evolution/SKILL.md).

Do not use `--allow-crimes` as a substitute for architecture analysis. Do not
turn on `--trust-remote-code` for an unfamiliar Hub repository. The detailed API
and safety tables live in the references below.

## Operating procedure

1. **Normalize the references.** Record every model, optional base model, LoRA,
   local path or Hub ID, and revision. Parse each with
   `ModelReference.parse`; preserve revisions rather than relying on a mutable
   branch. A `model+lora` reference needs a configured LoRA merge cache before
   it can become a local merged checkpoint.
2. **Resolve without guessing.** For a local path, verify configuration and a
   supported single model file or index. For a Hub ID, verify the requested
   revision and cache policy before downloading. Inspect `config.json` and the
   checkpoint index before selecting an architecture. A malformed reference,
   missing revision, missing model file, or unexpected model type is a
   resolution failure, not an architecture mismatch to suppress.
3. **Establish the output architecture.** Prefer the bundled JSON definition
   selected from `config.architectures` and `config.model_type`. It must be
   compatible across referenced models unless the user explicitly accepts the
   risk of `allow_crimes`; that flag only bypasses the guard. If a definition is
   absent, the auto-inference path inventories checkpoint names, optionally
   compares a Transformers meta-layout, and marks missing/tied/ignored weights
   optional where evidence supports it. Verify layer counts, modules, tensor
   shapes, embeddings, tied names, aliases, and output config keys.
4. **Check checkpoint layout.** Architecture names are the output model layout.
   Loaders first look for the requested key, then aliases/tied names, then use
   Transformers checkpoint conversion when the model type has a conversion
   mapping. Conversion is valid only when every required wildcard/pattern group
   is present; a partial expert group must fail or remain optional, not be
   silently averaged.
5. **Plan memory and devices.** Choose a compute device and a storage device
   separately. CPU is the safe baseline. CUDA math requires a usable CUDA
   backend; `read_to_gpu` loads input tensors directly to the selected device,
   while `low_cpu_memory` stores intermediates on the accelerator. Use
   `multi_gpu` only after a device-count check and with enough VRAM for the
   assigned islands. `gpu_rich` is a compound policy, not a proof that the host
   has GPUs. See [resource-and-backend-planning.md](references/resource-and-backend-planning.md).
6. **Execute and inspect the artifact.** `MergePlanner` normalizes whole-model
   and slice forms into module/slice work, creates tensor tasks, and returns
   streaming or in-memory targets. The graph executor frees values after their
   last use. For disk output, verify the model shard(s), index when sharded,
   `config.json`, tokenizer files or a deliberate no-tokenizer decision,
   `README.md`/merge config when model-card writing is enabled, and tagalong
   files. Never reuse a non-empty output directory without checking for shard
   name collisions.
7. **Recover by classification.** Use
   [troubleshooting.md](references/troubleshooting.md) to distinguish install
   and import issues, bad references, architecture/key conversion, resource
   exhaustion, lazy-unpickle limits, and incomplete output. Change one cause at
   a time and retain the exact options and revision in the run record.

## Safe diagnostic

From any working directory, run:

```text
python scripts/mergekit_model_diagnostic.py --help
python scripts/mergekit_model_diagnostic.py --check --model-ref MODEL@REVISION --checkpoint MODEL_DIR --device auto
```

The script parses references, inspects a local checkpoint index without loading
model tensors, and reports the requested device/backend. It does not download
Hub models, execute remote model code, write output, or trust pickle payloads.
Use it as a preflight, not as proof that tensor shapes or a full merge will fit.

## Completion handoff

Report the normalized references and revisions, architecture source and
compatibility verdict, key-conversion result, selected math/storage devices,
RAM/VRAM rationale, lazy/safe serialization and shard settings, output files
checked, and any unresolved warning. Link the relevant reference section rather
than copying deep API tables into this router.

Read progressively:

- [api-reference.md](references/api-reference.md): verified signatures and
  object contracts.
- [architecture-and-checkpoints.md](references/architecture-and-checkpoints.md):
  architecture selection, JSON definitions, inference, and key conversion.
- [resource-and-backend-planning.md](references/resource-and-backend-planning.md):
  CPU/CUDA/multi-GPU decisions, lazy loading, sharding, and output policy.
- [troubleshooting.md](references/troubleshooting.md): symptoms, evidence, and
  recovery actions.
