# Primitives And Feature Definitions Workflows

## What This Route Solves

This route covers the life cycle of a feature definition:

1. Define the primitive or feature object.
2. Explain what it means.
3. Optionally render the lineage graph.
4. Save the feature list for reuse.
5. Reload it later for another feature-matrix run.

## Recommended Order

### 1. Define The Primitive

Start with a primitive class when the built-in catalog does not provide the exact behavior you need.

Keep constructor arguments on `self` so `get_args_string` can reproduce the public argument list.

### 2. Build The Feature Objects

Wrap the base column in a `Feature`, `IdentityFeature`, `TransformFeature`, or `AggregationFeature` depending on the direction of the dependency.

Use `feature[i]` to access a slice of a multi-output feature.

### 3. Describe Or Render The Feature

- `describe_feature` produces a readable sentence.
- `graph_feature` produces a lineage graph when Graphviz is available.

### 4. Save And Reload The Feature List

Use `save_features` when the feature definitions should be reused later, then `load_features` before the next matrix calculation.

Typical workflow:

```python
features = ft.dfs(entityset=es, target_dataframe_name="customers", features_only=True)
ft.save_features(features, "feature_definitions.json")
reloaded = ft.load_features("feature_definitions.json")
```

## Custom Primitive Checklist

- Define the input and output logical types.
- Keep public constructor arguments on `self`.
- Return a callable from `get_function`.
- Add `number_output_features` and `generate_names` when the primitive returns multiple outputs.
- Use a short, stable `name` that makes sense in feature strings.

## Feature-Object Checklist

- Use `IdentityFeature` for a direct column reference.
- Use `DirectFeature` when a feature crosses a relationship.
- Use `TransformFeature` for same-table transformations.
- Use `AggregationFeature` for parent-table rollups.
- Use `GroupByTransformFeature` for grouped same-table transforms.

## When To Read The Troubleshooting File

Switch to `troubleshooting.md` when:

- A custom primitive cannot reproduce its constructor args.
- A feature description is too generic.
- Graph rendering fails.
- A saved feature file does not reload cleanly.
- A plugin or entry-point package logs a warning on import.
