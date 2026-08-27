# Feature Objects

## Object Hierarchy

- `FeatureBase` is the common base for feature definitions.
- `Feature` is the convenience constructor used by most callers.
- `IdentityFeature`, `DirectFeature`, `TransformFeature`, `AggregationFeature`, and `GroupByTransformFeature` are the concrete feature types.
- `FeatureOutputSlice` represents one output from a multi-output feature.

## What Each Class Means

- `IdentityFeature`: a direct column reference.
- `DirectFeature`: a feature carried across a relationship.
- `TransformFeature`: a same-table transformation.
- `AggregationFeature`: a child-to-parent rollup.
- `GroupByTransformFeature`: a transform performed inside a group.
- `FeatureOutputSlice`: a single output column from a multi-output primitive.

## Useful Methods

- `to_dictionary()` for serialization or debugging.
- `get_name()` for a stable display name.
- `get_feature_names()` for the per-output names.
- `get_dependencies()` for the transitive feature graph.
- `get_depth()` for the feature depth.
- `copy()` for a lightweight clone.
- `unique_name()` for an identity-like string.
- `__getitem__()` for slice access on multi-output features.

## Dependency And Depth Rules

- `get_dependencies(deep=False)` returns the immediate parents.
- `get_dependencies(deep=True)` returns the full chain.
- `get_depth()` counts how far the feature is from its base inputs.
- `get_depth(stop_at=...)` is useful when you want to compare a feature against a smaller stop set.

## Serialization And Explanation Notes

- `describe_feature` uses the feature objects, optional feature descriptions, and primitive templates to build a human-readable sentence.
- `graph_feature` walks the same object graph and renders a lineage diagram.
- `save_features` and `load_features` persist a list of feature objects and reload them later.

## Multi-Output Notes

- Multi-output features should behave like a base feature plus one slice per output.
- The slice names should be stable and line up with the primitive's generated names.
- The `feature[i]` syntax should return one output slice without changing the original feature.

## Practical Guidance

- Use `IdentityFeature` when you want to anchor a feature manually before passing it into a primitive.
- Use `DirectFeature` when you need to traverse a relationship rather than apply a transform.
- Use `FeatureOutputSlice` only when the primitive really returns multiple outputs.
- Save and reload the feature list after you are happy with the names, because downstream matrix generation depends on those stable names.
