# Custom Primitive Contract

## Base Class Pattern

Featuretools custom primitives inherit from either `TransformPrimitive` or `AggregationPrimitive`.

The important public attributes and methods are:

- `name`
- `input_types`
- `return_type`
- `number_output_features`
- `get_function()`
- `get_args_string()`
- `generate_name(...)`
- `generate_names(...)`
- `get_filepath(filename)`

## Constructor Rules

- Store every public constructor argument on `self`.
- Use plain values that can be represented in a feature string.
- Keep the constructor small and side-effect free.

If a constructor argument is not stored on the instance, `get_args_string()` cannot reproduce it later.

## Single-Output Example Shape

```python
class StringCount(TransformPrimitive):
    name = "string_count"
    input_types = [ColumnSchema(logical_type=NaturalLanguage)]
    return_type = ColumnSchema(semantic_tags={"numeric"})

    def __init__(self, string=None):
        self.string = string

    def get_function(self):
        def string_count(column):
            return [text.lower().count(self.string) for text in column]
        return string_count
```

## Multi-Output Example Shape

When a primitive returns more than one column, set `number_output_features` and implement `generate_names`.

```python
class CaseCount(TransformPrimitive):
    name = "case_count"
    input_types = [ColumnSchema(logical_type=NaturalLanguage)]
    return_type = ColumnSchema(semantic_tags={"numeric"})
    number_output_features = 2

    def generate_names(self, base_feature_names):
        name = self.generate_name(base_feature_names)
        return f"{name}[upper]", f"{name}[lower]"
```

## Naming Rules

- Primitive names should be short and stable.
- `generate_name` should read naturally in a feature string.
- `generate_names` should return one name per output column, in the same order as the function output.

## File-Path Helper

`get_filepath(filename)` resolves primitive-data files relative to the configured primitive-data folder.

Use it for package-bundled resources, not for local project files.

## Practical Guidance

- If the primitive depends on a runtime parameter, expose it as a constructor argument and store it on `self`.
- If the primitive is multi-output, verify the slice names as well as the base feature name.
- If you need custom descriptions, pair the primitive with `describe_feature` templates in the feature-description workflow.
