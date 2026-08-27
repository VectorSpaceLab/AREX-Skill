---
name: graph-models
description: "Build Graph Nets blocks and high-level Sonnet model architectures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Graph Models

Use this sub-skill when the task is to assemble, adapt, or debug Graph Nets neural-network modules: low-level broadcasters/aggregators, `EdgeBlock` / `NodeBlock` / `GlobalBlock`, high-level `graph_nets.modules` architectures, or Sonnet model factories for Graph Nets demos.

## Route here for

- Choosing and wiring `graph_nets.blocks` broadcasters, aggregators, reducers, or update blocks.
- Building `GraphIndependent`, `GraphNetwork`, `InteractionNetwork`, `RelationNetwork`, `DeepSets`, `CommNet`, or `SelfAttention` modules.
- Writing Sonnet 1 or Sonnet 2 `*_model_fn` factories for edge, node, global, encoder, core, decoder, or output transforms.
- Adapting the bundled demo architectures in [`scripts/demo_models_tf1.py`](scripts/demo_models_tf1.py) or [`scripts/demo_models_tf2.py`](scripts/demo_models_tf2.py).
- Running a tiny installed-package model smoke with [`scripts/graph_model_smoke.py`](scripts/graph_model_smoke.py).

## Route elsewhere

- Raw `GraphsTuple` construction, dictionary batching, and NetworkX conversion belong in [`../graph-data/SKILL.md`](../graph-data/SKILL.md).
- TensorFlow utilities, placeholders, padding, masks, `utils_tf.concat`, `tf.function` signatures, and session/feed details belong in [`../tensorflow-ops/SKILL.md`](../tensorflow-ops/SKILL.md).
- Full training-loop or notebook reproduction work should use the root Graph Nets recipe guidance first, then return here only for the model/module layer.

## Required reading for model work

1. [`references/api-reference.md`](references/api-reference.md) for constructor contracts, field requirements, reducer defaults, and Sonnet version differences.
2. [`references/workflows.md`](references/workflows.md) for practical recipes: independent encoders/decoders, generic message passing, relation/set/communication modules, self-attention, and encode-process-decode.
3. [`references/troubleshooting.md`](references/troubleshooting.md) when a graph field is `None`, senders/receivers are absent, reducers are missing, concatenation shapes fail, or TF/Sonnet major versions mismatch.

## Operating checklist

- Confirm the installed stack before choosing code style: Sonnet 1 uses `snt.AbstractModule` and TF1 sessions/placeholders; Sonnet 2 uses `snt.Module`, eager tensors, and optional `tf.function` wrapping.
- Decide which graph fields the module is allowed to read. Match every `use_*` flag to non-`None` input fields and to required reducers.
- Keep model factories as zero-argument callables that return a Sonnet module or callable. Do not instantiate a fresh submodule inside every call of an already-built model.
- Validate all concatenated features share the same rank and all non-last axes after broadcasting/aggregation; only the last feature axis should differ.
- Preserve sub-skill boundaries: fix invalid graph data before model assembly and delegate padding/session mechanics to the TensorFlow ops sub-skill.
