# Block authoring reference

## Block types and decorators

Mage's block decorators are lightweight markers imported from `mage_ai.data_preparation.decorators`. The common batch block types are `@data_loader`, `@transformer`, `@data_exporter`, and `@test`.

## Typical Python block shape

```python
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_data(*args, **kwargs):
    return {}
```

Recommended patterns:

- Keep imports at the top of the block.
- Use `**kwargs` to access runtime variables and execution metadata.
- Return a dataframe, list, dict, or other serializable output that downstream blocks can consume.
- Add a `@test` block when the generated template includes one.

## Runtime variables

| Variable source | How to read it |
| --- | --- |
| Runtime variables passed to the block | `kwargs.get('name')` |
| Environment variables | `{{ env_var('NAME') }}` |
| Pipeline/runtime variables in interpolation | `{{ variables('name') }}` |
| Secrets | `{{ mage_secret_var('secret_name') }}` |

Rules to remember:

- Variable names must be valid Python identifiers.
- Runtime variables must use primitive values or simple containers.
- Default runtime context includes `execution_date` and, for event-triggered pipelines, `event`.

## SQL blocks

SQL blocks run against a configured data provider and profile. They can render upstream block outputs as `{{ df_1 }}`, `{{ df_2 }}`, and so on, use `{{ execution_date }}` in the query, and save results into an automatically generated table unless raw SQL handling is enabled.

## R blocks

R blocks are supported in Docker-based Mage setups. Use `pacman::p_load(...)` or `library("pacman")` / `p_load(...)` at the top of the R block, and read runtime variables through `global_vars`.

## Dynamic blocks

Dynamic blocks return lists of records that Mage fans out into child blocks. Limit fan-out with `DYNAMIC_BLOCKS_MAX_CHILD_BLOCKS` and `DYNAMIC_BLOCKS_MAX_CONCURRENT_CHILD_BLOCKS` or the pipeline/block-level metadata settings.

## Templates and transformer actions

Useful pieces:

- `fetch_template_source(...)` for block templates
- `build_template_from_suggestion(...)` for suggested transformations
- `mage_ai.data_cleaner.transformer_actions.utils.build_transformer_action(...)` for transformer-action payloads
- `BaseAction(payload).execute(df)` to run the transformation

## Programmatic pipeline execution

`mage_ai.run(...)` is the Python helper for running a pipeline from code. It resolves the project path, appends the parent directory to `sys.path`, and executes either the whole pipeline or a single block depending on `block_uuid`.
