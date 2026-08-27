# Demo Recipes

## Purpose

Read this when a user asks about the original Graph Nets tutorial notebooks, sorting, shortest path, physical dynamics, or the encode-process-decode demo architecture. This file distills the reusable workflow patterns without requiring the original notebook files.

## Notebook families

| Recipe | Runtime family | What it demonstrates | How to use this skill |
| --- | --- | --- | --- |
| Graph Nets basics | TF1 and TF2 variants | Build `GraphsTuple` data, convert dictionaries/NetworkX graphs, use `utils_tf`, feed graph modules | Start with [graph-data](../sub-skills/graph-data/SKILL.md), then [tensorflow-ops](../sub-skills/tensorflow-ops/SKILL.md), then [graph-models](../sub-skills/graph-models/SKILL.md). |
| Sort | TF1 and TF2 variants | Treat list sorting as graph prediction; use encode-process-decode with repeated message passing | Use graph-models demo scripts for the architecture; keep training-loop details small and fixture-driven. |
| Shortest path | TF1 variant | Predict nodes/edges on a shortest path over generated graphs | Use graph-data to prepare graph features and graph-models for message-passing architecture. |
| Physics | TF1 variant | Predict next-step mass-spring dynamics and rollouts | Use graph-data for state graphs and graph-models for encode-process-decode; treat full rollout training as expensive. |

## Common architecture pattern

The demos use three components:

1. **Encoder**: a `GraphIndependent` module independently embeds edge, node, and global attributes.
2. **Core**: a `GraphNetwork` module applies message passing for one processing step.
3. **Decoder/output transform**: another `GraphIndependent` decodes each processing step and optionally projects output sizes.

The bundled model helpers preserve this pattern:

```bash
python path/to/graph-nets/sub-skills/graph-models/scripts/demo_models_tf1.py --processing-steps 1 --pretty
python path/to/graph-nets/sub-skills/graph-models/scripts/demo_models_tf2.py --processing-steps 1 --pretty
```

Use the TF1 helper only with Sonnet 1. Use the TF2 helper only with Sonnet 2.

## Adapting a notebook safely

1. Choose the runtime family from [compatibility](compatibility.md).
2. Convert the notebook's graph construction into explicit data dictionaries or NetworkX graphs; validate with the graph-data sub-skill.
3. Convert to tensor `GraphsTuple`s, then use the TensorFlow ops sub-skill for batching, padding, masks, or `tf.function` signatures.
4. Use graph-models for the encode-process-decode stack and model factories.
5. Keep first verification tiny: one or two graphs, one processing step, no external downloads, no full training loop.
6. Only run long training loops, plotting, Jupyter, or dataset generation after the tiny checks pass and the user accepts the runtime cost.

## Common omissions from the full notebooks

- Plotting, animations, and figures are presentation details; they are not needed to validate a Graph Nets data/model pipeline.
- Notebook install cells include broad dependencies for Colab convenience. For package/API work, install only the selected TensorFlow/Sonnet stack and the small extras actually used by the task.
- The full sorting, shortest-path, and physics notebooks train models. Treat them as optional/expensive native examples rather than default smoke tests.
