# Primitives And Feature Definitions Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `graph_feature` fails to render | The Graphviz Python package or system binary is missing | Install Graphviz or keep the workflow on the non-graph path. |
| `graph_feature(..., to_file=...)` errors about file extensions | The output path does not include an extension | Use `.png`, `.pdf`, `.svg`, or `.dot`. |
| `get_args_string()` omits a constructor argument | The primitive did not store the argument on `self` | Save every public constructor argument as an attribute and retry. |
| Multi-output feature names look wrong | `number_output_features` or `generate_names` does not match the function output | Return one generated name per output column in the same order as the primitive output. |
| `save_features` / `load_features` round-trip changes names | The feature list was modified before serialization or a custom rename was not preserved | Rebuild the list from the intended objects and serialize again. |
| `save_features` refuses a URL | The helper does not support arbitrary write URLs | Save to a local file or to a supported remote store instead. |
| Importing `featuretools` logs plugin warnings | An entry-point plugin failed to load or raised during import | Treat the warning as extension-specific, then inspect the plugin package separately. |
| `describe_feature` is too generic | The feature descriptions or primitive templates were not provided | Pass `feature_descriptions`, `primitive_templates`, or a metadata file. |
| `load_features` cannot restore a custom primitive | The primitive class is missing from the current environment | Install the package that defines the custom primitive before loading the feature file. |

## Extra Notes

- If the feature graph needs to be shared, prefer `describe_feature` text first and render the graph only when Graphviz is available.
- If the primitive is a package extension, verify the entry point separately before assuming the base Featuretools install is broken.
- Save and reload a tiny feature list locally before trying a remote store or a larger graph.
