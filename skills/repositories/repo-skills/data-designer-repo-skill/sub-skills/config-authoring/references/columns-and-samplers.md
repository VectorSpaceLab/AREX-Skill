# Columns, Samplers, Validators, Skip/Drop, and Jinja

Use this reference when authoring or repairing `DataDesignerConfigBuilder` columns. API signatures and non-column families are summarized in [`api-reference.md`](api-reference.md); seed/person workflows are in [`seed-and-person-data.md`](seed-and-person-data.md).

## Core column rules

All built-in single-column configs share these fields:

```text
name, drop, column_type, skip, propagate_skip
```

Rules:

- `name` is the column name and must be unique in the builder; re-adding the same `name` replaces the previous config.
- `column_type` is the Pydantic discriminator for deserialization. Use kebab-case strings such as `"sampler"`, `"llm-text"`, or the matching `dd.DataDesignerColumnType` enum value.
- `drop=True` keeps the column available to downstream columns during generation but removes it from final output.
- `skip=dd.SkipConfig(when="{{ ... }}", value=None)` is an expression gate for non-sampler/non-seed columns. The `when` expression must use Jinja delimiters and reference another column.
- `propagate_skip=True` by default: when any required upstream column is skipped, this column skips too. Set `propagate_skip=False` only when the prompt/expression is explicitly null-tolerant.
- Sampler and seed-dataset columns do not support `skip`; gate downstream columns instead.

## Column type field catalog

| `column_type` | Config class | Specific fields beyond common | Model call? | Notes |
| --- | --- | --- | --- | --- |
| `sampler` | `SamplerColumnConfig` | `sampler_type`, `params`, `conditional_params`, `convert_to` | No | Built-in statistical/person/time generators. `params`, not `sampler_params`. |
| `llm-text` | `LLMTextColumnConfig` | `prompt`, `model_alias`, `system_prompt`, `multi_modal_context`, `tool_alias`, `with_trace`, `extract_reasoning_content` | Yes | Prompt/system prompt are Jinja templates. |
| `llm-code` | `LLMCodeColumnConfig` | all `llm-text` fields + `code_lang` | Yes | Extracts a code block for the selected `CodeLang`. |
| `llm-structured` | `LLMStructuredColumnConfig` | all `llm-text` fields + `output_format` | Yes | `output_format` can be a Pydantic model class or JSON schema dict; Pydantic models are converted to JSON schema. |
| `llm-judge` | `LLMJudgeColumnConfig` | all `llm-text` fields + `scores` | Yes | `scores` is a non-empty list of `Score(name, description, options)`. |
| `embedding` | `EmbeddingColumnConfig` | `target_column`, `model_alias` | Yes | Requires the target text column. |
| `image` | `ImageColumnConfig` | `prompt`, `model_alias`, `multi_modal_context` | Yes | Prompt is Jinja; multimodal context uses `ImageContext`, `AudioContext`, or `VideoContext`. |
| `validation` | `ValidationColumnConfig` | `target_columns`, `validator_type`, `validator_params`, `batch_size` | Usually no/remote optional | Runs validation logic against existing columns; see validator table below. |
| `expression` | `ExpressionColumnConfig` | `expr`, `dtype` | No | Jinja expression evaluated row-by-row, then coerced to `int`, `float`, `str`, or `bool`. |
| `seed-dataset` | `SeedDatasetColumnConfig` | none | No | Created by the engine when a seed source is compiled; do not add manually. |
| `custom` | `CustomColumnConfig` | `generator_function`, `generation_strategy`, `generator_params` | Optional | Function must be decorated with `@dd.custom_column_generator(...)`. |

## Builder shorthand examples

Both forms are valid:

```python
# Concrete config object
builder.add_column(
    dd.SamplerColumnConfig(
        name="category",
        sampler_type=dd.SamplerType.CATEGORY,
        params=dd.CategorySamplerParams(values=["A", "B"]),
    )
)

# Shorthand; builder resolves column_type -> class and sampler_type -> params class.
builder.add_column(
    name="category",
    column_type="sampler",
    sampler_type="category",
    params={"values": ["A", "B"]},
)
```

For sampler shorthand, `params` can be a dict or the correct params object. A dict does not need to repeat `sampler_type`; the sampler column injects it for Pydantic union resolution.

## Sampler params catalog

Every sampler params object has a `sampler_type` discriminator. Use `SamplerColumnConfig(..., sampler_type=..., params=...)`.

| `sampler_type` | Params class | Required/key fields | Notes |
| --- | --- | --- | --- |
| `uuid` | `UUIDSamplerParams` | `prefix`, `short_form`, `uppercase` | UUID4 strings; `short_form=True` truncates to 8 chars. |
| `category` | `CategorySamplerParams` | `values`, `weights` | `values` must be non-empty. Weights are optional, length-matched, and normalized; zero-sum weights fail. |
| `subcategory` | `SubcategorySamplerParams` | `category`, `values` | `category` must name a parent category sampler when present in config. |
| `uniform` | `UniformSamplerParams` | `low`, `high`, `decimal_places` | Numeric sampler; use `convert_to="int"` if integer-like output is desired. |
| `gaussian` | `GaussianSamplerParams` | `mean`, `stddev`, `decimal_places` | Numeric sampler. |
| `bernoulli` | `BernoulliSamplerParams` | `p` | `p` must be between 0 and 1. |
| `bernoulli_mixture` | `BernoulliMixtureSamplerParams` | `p`, `dist_name`, `dist_params` | Samples 0 or a SciPy distribution draw. |
| `binomial` | `BinomialSamplerParams` | `n`, `p` | Count sampler. |
| `poisson` | `PoissonSamplerParams` | `mean` | Count sampler. |
| `scipy` | `ScipySamplerParams` | `dist_name`, `dist_params`, `decimal_places` | Flexible `scipy.stats` sampler. |
| `datetime` | `DatetimeSamplerParams` | `start`, `end`, `unit` | `start`/`end` must parse as datetimes; units: `Y`, `M`, `D`, `h`, `m`, `s`. |
| `timedelta` | `TimeDeltaSamplerParams` | `dt_min`, `dt_max`, `reference_column_name`, `unit` | Adds a delta to an existing datetime column; `dt_min < dt_max`; units: `D`, `h`, `m`, `s`. |
| `person` | `PersonSamplerParams` | `locale`, `sex`, `city`, `age_range`, `select_field_values`, `with_synthetic_personas` | Uses managed persona datasets for supported locales; see [`seed-and-person-data.md`](seed-and-person-data.md). |
| `person_from_faker` | `PersonFromFakerSamplerParams` | `locale`, `sex`, `city`, `age_range` | Faker fallback; less demographically grounded, no synthetic persona fields. |

## Conditional sampler params

`conditional_params` is a mapping from condition strings to params. It is sampler-only.

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="review_style",
        sampler_type="category",
        params=dd.CategorySamplerParams(values=["brief", "detailed"]),
        conditional_params={
            "target_age_range == '18-25'": dd.CategorySamplerParams(values=["informal"]),
        },
    )
)
```

Conditions are evaluated against existing values. Keep dependencies acyclic: the condition should only refer to columns generated before this sampler.

## Sampler constraints

Builder constraints apply to numerical sampler columns and are enforced by sampler rejection logic during runtime:

```python
builder.add_constraint(
    dd.ScalarInequalityConstraint(target_column="age", operator="ge", rhs=18)
)
builder.add_constraint(
    dd.ColumnInequalityConstraint(target_column="end_day", operator="gt", rhs="start_day")
)
```

Use `constraint_type="scalar_inequality"` or `"column_inequality"` for shorthand. Serialized legacy shapes may be inferred from `rhs`, but explicit `constraint_type` is clearer.

## Jinja reference rules

Jinja templates appear in `prompt`, `system_prompt`, `expr`, `skip.when`, and processor templates.

- Reference columns as `{{ column_name }}`.
- Reference nested dict/object fields with dot syntax: `{{ person.first_name }}`, `{{ product.price }}`.
- Use Jinja control flow inside prompt/expression strings when needed: `{% if complaint_analysis %}...{% endif %}`.
- `LLMJudgeColumnConfig` returns nested score objects. For a judge column named `quality` and score named `correctness`, use `{{ quality.correctness.score }}` for the numeric score; `{{ quality.correctness }}` is the full score dict.
- The builder's `allowed_references` includes column names and side-effect columns such as `name__trace` and `name__reasoning_content` when configured.

Bad Jinja syntax is caught at config object construction for built-in prompt/expression fields. Unknown references may not fail until compile/runtime; check spelling against builder column names and seed fields.

## Skip propagation patterns

```python
# Gate an expensive column.
builder.add_column(
    dd.LLMTextColumnConfig(
        name="complaint_analysis",
        model_alias="text",
        prompt="Analyze {{ review }}",
        skip=dd.SkipConfig(when="{{ rating > 2 }}"),
    )
)

# Default: downstream auto-skips if complaint_analysis skipped.
builder.add_column(
    dd.ExpressionColumnConfig(name="has_analysis", expr="{{ complaint_analysis is not none }}", dtype="bool")
)

# Opt out only when you guard nulls yourself.
builder.add_column(
    dd.LLMTextColumnConfig(
        name="safe_summary",
        model_alias="text",
        propagate_skip=False,
        prompt="Review: {{ review }}{% if complaint_analysis %}\nAnalysis: {{ complaint_analysis }}{% endif %}",
    )
)
```

`ExpressionColumnConfig` coerces `skip.value` to the configured `dtype`; incompatible sentinel values raise validation errors.

## Drop versus processors

Prefer column-level `drop=True` for helper columns that should remain available to downstream columns but disappear from final output:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="person",
        sampler_type="person_from_faker",
        params=dd.PersonFromFakerSamplerParams(),
        drop=True,
    )
)
builder.add_column(dd.ExpressionColumnConfig(name="first_name", expr="{{ person.first_name }}"))
```

Use `DropColumnsProcessorConfig` when you need processor artifacts or glob-based cleanup across already-added columns:

```python
builder.add_processor(
    dd.DropColumnsProcessorConfig(name="drop_helpers", column_names=["helper_*"])
)
```

The builder expands glob patterns against known columns and marks matches `drop=True`. If a column is not yet known, the processor cannot mark it until it is re-added/reprocessed.

## Validation columns and validator params

```python
builder.add_column(
    dd.ValidationColumnConfig(
        name="code_validation",
        target_columns=["generated_code"],
        validator_type="code",
        validator_params=dd.CodeValidatorParams(code_lang=dd.CodeLang.PYTHON),
        batch_size=10,
    )
)
```

| `validator_type` | Params class | Fields | Config-time checks |
| --- | --- | --- | --- |
| `code` | `CodeValidatorParams` | `validator_type`, `code_lang` | Only Python and SQL dialects are supported. |
| `local_callable` | `LocalCallableValidatorParams` | `validator_type`, `validation_function`, `output_schema` | `validation_function` must be callable. Runtime output should include `is_valid: bool`. |
| `remote` | `RemoteValidatorParams` | `validator_type`, `endpoint_url`, `output_schema`, `timeout`, `max_retries`, `retry_backoff`, `max_parallel_requests` | Field bounds: timeout > 0, retries >= 0, backoff > 1, parallel requests >= 1. |

A validator params dict may omit `validator_type` when the outer `ValidationColumnConfig.validator_type` is set; the config model injects it.

## Custom columns

Use `@dd.custom_column_generator(...)`; undecorated functions are rejected.

```python
@dd.custom_column_generator(
    required_columns=["raw_text"],
    side_effect_columns=["raw_text_length"],
    model_aliases=[],
)
def normalize(row: dict) -> dict:
    row["normalized_text"] = row["raw_text"].strip().lower()
    row["raw_text_length"] = len(row["raw_text"])
    return row

builder.add_column(
    dd.CustomColumnConfig(
        name="normalized_text",
        generator_function=normalize,
        generation_strategy=dd.GenerationStrategy.CELL_BY_CELL,
    )
)
```

Signature rules from the decorator validator:

- 1 to 3 positional parameters only.
- Parameter 1 must be named `row` or `df`.
- Parameter 2, if present, must be named `generator_params`.
- Parameter 3, if present, must be named `models`.
- Declare all inputs in `required_columns`; declare any extra output columns in `side_effect_columns`.
- If the custom generator needs LLM clients, declare `model_aliases=[...]` so readiness checks know all aliases.

`generation_strategy="cell_by_cell"` receives row-shaped input. `generation_strategy="full_column"` is batch/DataFrame-oriented; keep function naming (`df`) aligned with the strategy to avoid future-reader confusion.
