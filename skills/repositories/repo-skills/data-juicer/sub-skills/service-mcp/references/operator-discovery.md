# Operator discovery

## Search modes
`search_ops` can be used to discover operators by:
- tags
- regex
- BM25 / keyword ranking

Use tags when you already know the operator family.
Use regex when you know part of the name.
Use BM25 when you want fuzzy text matching.

## Related helpers
- `get_global_config_schema`
- `get_dataset_load_strategies`
- `run_data_recipe`
- `analyze_dataset`

## Plugin discovery
- Built-in operators come from the installed `data_juicer.ops` package.
- Custom operators should be added through the package/plugin mechanism rather than by editing the service script.
- If a search result looks wrong, confirm that the installed operator list matches the runtime environment.

## Choosing the right tool
- Use operator search when the question is "which operator should I use?"
- Use recipe-flow when the question is "run or analyze a recipe"
- Use granular-ops when the question is "call a small, specific action"
