---
name: primitives-and-feature-definitions
description: "Define custom Featuretools primitives and work with feature
  objects, descriptions, graphs, and saved feature definitions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Primitives And Feature Definitions

Use this sub-skill when the task is about authoring custom primitives, inspecting feature lineage, generating descriptions, rendering graphs, or saving and reloading feature definitions.

## Route Here For

- Defining a `TransformPrimitive` or `AggregationPrimitive`.
- Understanding `Feature`, `IdentityFeature`, `DirectFeature`, `TransformFeature`, `AggregationFeature`, `GroupByTransformFeature`, or `FeatureOutputSlice`.
- Explaining a feature with `describe_feature`.
- Rendering a lineage graph with `graph_feature`.
- Persisting or reloading a feature definition list with `save_features` / `load_features`.
- Handling plugin or entry-point loading behavior for custom extensions.

## Start With These References

- `../../references/api-reference.md`: the feature, primitive, description, graph, and serialization signatures.
- `references/workflows.md`: the custom-primitive and feature-definition workflow.
- `references/custom-primitives.md`: the primitive class contract and multi-output naming rules.
- `references/feature-objects.md`: the feature object model and dependency/slice behavior.
- `references/troubleshooting.md`: graphviz, serialization, naming, and plugin recovery notes.
- `scripts/primitives_smoke.py`: a tiny smoke script for custom primitives and feature serialization.

## Boundaries

- Stay inside primitive authoring, feature objects, descriptions, graphs, and saved feature lists.
- Route DFS and feature-matrix creation to `../deep-feature-synthesis/`.
- Route primitive discovery, primitive recommendations, and matrix pruning to `../feature-inspection-and-selection/`.
- Route EntitySet modeling and demo data to `../entitysets-and-data/`.

## Minimal Workflow

1. Define the primitive class and keep any constructor arguments on `self`.
2. Build a `Feature` or `TransformFeature`/`AggregationFeature` around it.
3. Use `describe_feature` to inspect the human-readable description.
4. Use `graph_feature` when you need a lineage graph and Graphviz is available.
5. Use `save_features` / `load_features` when the feature definitions need to be reused later.

## Common Decision Points

- Add `number_output_features` and `generate_names` when a custom primitive returns multiple columns.
- Use `FeatureOutputSlice` through the `feature[i]` syntax when you need one output from a multi-output feature.
- Keep the feature list and the serialized file aligned so `load_features` reloads the same objects you saved.
- Treat `featuretools` entry-point plugins as optional extension behavior, not as part of the base install.

## Quality Bar

Future agents should be able to define and reuse feature definitions, explain them, and recover them from disk without reopening the original repository.
