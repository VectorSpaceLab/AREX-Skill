# Config Authoring Troubleshooting

Use this for errors while constructing, loading, validating, or serializing DataDesigner configs. If the failure happens during `preview`, `create`, `check_models`, result export, resume, or artifact access, switch to [`generation-runtime`](../../generation-runtime/SKILL.md). For install/import/package-level problems, use root [troubleshooting](../../../references/troubleshooting.md).

## First split: config error or generation error?

| Observation | Treat as | Next action |
| --- | --- | --- |
| Pydantic `ValidationError`, `InvalidConfigError`, `BuilderConfigurationError`, missing field, extra field, bad discriminator, invalid Jinja syntax | Config authoring error | Fix fields/types, then run `builder.build()` again. |
| `DataDesigner().validate(builder)` fails before any record generation | Compile/config-resource error | Check model aliases, seed paths/columns, custom generator metadata, validators, and person asset availability. |
| `preview` or `create` starts then fails with model/API/timeout/empty dataset/artifact/profiling messages | Generation/runtime error | Route to `generation-runtime`; do not keep editing config blindly unless the message names a config field. |
| `check_models` fails | Runtime readiness error | Route to `generation-runtime`; model/MCP endpoint credentials and network are outside config authoring. |

Minimal local check:

```python
builder = load_config_builder()
builder.build()  # Pydantic and root config validation only
```

Optional compile check when interface dependencies/resources are available:

```python
from data_designer.interface import DataDesigner
DataDesigner().validate(builder)  # no record generation
```

## Symptom table

| Symptom | Likely cause | Minimal fix |
| --- | --- | --- |
| `Field required` for sampler params | `SamplerColumnConfig` missing `params`. | Add `params=dd.<Sampler>Params(...)` or `params={...}` matching `sampler_type`. |
| `Extra inputs are not permitted` with `sampler_params` | Old/wrong key; config models use `extra="forbid"`. | Rename `sampler_params` to `params`. |
| Discriminator error for column | Missing/wrong `column_type` in dict/YAML. | Use one of `sampler`, `llm-text`, `llm-code`, `llm-structured`, `llm-judge`, `embedding`, `image`, `validation`, `expression`, `custom`, `seed-dataset`. |
| Discriminator error inside `params` | `sampler_type` and params class/dict do not match. | Match `sampler_type="uniform"` with `UniformSamplerParams` fields, `category` with `CategorySamplerParams`, etc. |
| Validation params cannot deserialize | Missing/wrong `validator_type` or `validator_params`. | Set outer `validator_type` to `code`, `local_callable`, or `remote`; use matching params fields. |
| Model inference params deserialize as wrong class | Missing/wrong `generation_type` or fields imply another type. | Use `ChatCompletionInferenceParams`, `EmbeddingInferenceParams`, or `ImageInferenceParams`; include explicit `generation_type` in YAML if ambiguity remains. |
| Processor dict rejected | Missing `processor_type` or non-JSON-serializable schema transform template. | Use `drop_columns` with `column_names` or `schema_transform` with a JSON-serializable `template`. |
| Seed source rejected | Missing/wrong `seed_type`. | Use `local`, `hf`, `df`, `directory`, `file_contents`, or `agent_rollout`; prefer concrete source objects in Python. |
| `skip.when` rejected for no columns | Expression omitted Jinja delimiters or references no variable. | Use `skip=dd.SkipConfig(when="{{ rating > 2 }}")`, not `"rating > 2"`. |
| `skip is not supported on sampler/seed-dataset columns` | `SkipConfig` attached to a sampler or seed column. | Gate downstream LLM/expression/validation columns instead. |
| Expression column empty or invalid syntax | `expr=""` or malformed Jinja. | Provide non-empty valid Jinja, e.g. `expr="{{ person.first_name }}"`. |
| Nested judge score used as whole dict | Jinja references `{{ quality.correctness }}`. | Use `{{ quality.correctness.score }}` for numeric score or `.reasoning` for reasoning. |
| `Subcategory` parent error | Parent exists but is not a category sampler. | Define parent as `SamplerColumnConfig(... sampler_type="category", params=CategorySamplerParams(...))`. |
| `DataFrameSeedSource` cannot be serialized | In-memory dataframe cannot be written into YAML/JSON. | Write dataframe to parquet and use `LocalFileSeedSource.from_dataframe(df, path)` or `LocalFileSeedSource(path=...)`. |
| Person locale rejected | `PersonSamplerParams` only accepts managed dataset locales. | Use a managed locale or switch to `PersonFromFakerSamplerParams`. |
| Managed person field missing at runtime | Locale parquet asset absent or field not present for locale/persona mode. | Run `python ../scripts/inspect_person_schema.py <locale>` and download/configure managed assets through CLI/runtime workflows if needed. |
| Custom column function rejected | Function not callable, not decorated, or signature param names are wrong. | Decorate with `@dd.custom_column_generator(...)`; use params named `row`/`df`, optional `generator_params`, optional `models`. |
| Local callable validator rejected | `validation_function` is not callable. | Pass a real function object in Python. YAML cannot carry local function objects without surrounding Python loader logic. |
| Local callable validator runs but output wrong | Runtime function output lacks `is_valid` bool or mismatches schema. | Return a dataframe with `is_valid: bool` and optional fields matching `output_schema`. |
| Model alias not found during validation/runtime | No `ModelConfig` with the alias referenced by model-backed columns. | Add `ModelConfig(alias="...", model="...", provider="...")` and pass it to `DataDesignerConfigBuilder(model_configs=[...])`. |
| No usable model aliases by default | Agent context has no configured aliases. | For sampler/expression/seed-only work, proceed with config-only validation. For LLM/embedding/image columns, add explicit model configs and route runtime checks to `generation-runtime`. |

## Recovering from `sampler_params` instead of `params`

Bad config:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="segment",
        sampler_type="category",
        sampler_params=dd.CategorySamplerParams(values=["free", "paid"]),
    )
)
```

Why it fails: `ConfigBase` forbids unknown fields, and `SamplerColumnConfig` has a field named `params`, not `sampler_params`.

Minimal fix:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="segment",
        sampler_type="category",
        params=dd.CategorySamplerParams(values=["free", "paid"]),
    )
)
```

YAML/dict shorthand also uses `params`:

```yaml
name: segment
column_type: sampler
sampler_type: category
params:
  values: [free, paid]
```

## Wrong discriminator names checklist

When deserializing YAML/JSON, verify these exact keys:

```text
columns[*].column_type
columns[*].params.sampler_type              # optional in Python dict shorthand if outer sampler_type exists
columns[*].validator_params.validator_type  # optional in Python dict shorthand if outer validator_type exists
model_configs[*].inference_parameters.generation_type
processors[*].processor_type
seed_config.source.seed_type
tool/provider configs: provider_type where applicable
constraints[*].constraint_type              # recommended even when legacy inference works
```

Do not invent aliases like `type`, `kind`, `sampler_params`, `validator`, or `source_type` unless a plugin's own public docs explicitly require them.

## Bad Jinja references

Config object construction catches syntax, not every semantic reference. To debug:

1. List current builder columns: `[c.name for c in builder.get_column_configs()]`.
2. Include side-effect columns if used: `builder.allowed_references`.
3. For seed fields, inspect the seed dataset columns before writing prompts.
4. For person fields, run `inspect_person_schema.py` for managed personas or start with common Faker fields such as `first_name`, `last_name`, `city`, `state`, `age`.
5. Use dot syntax for nested objects and Jinja conditionals for nullable skipped fields.

Examples:

```python
# Correct nested person references
"{{ customer.first_name }} {{ customer.last_name }} from {{ customer.city }}"

# Null-tolerant downstream column when propagation is disabled
"{% if complaint_analysis %}{{ complaint_analysis }}{% else %}No complaint analysis needed.{% endif %}"
```

## Invalid seed paths or seed columns

- `LocalFileSeedSource` validates local files or wildcard dataset partitions at construction time. Supported dataset extensions are `.parquet`, `.csv`, `.json`, and `.jsonl`.
- `DirectorySeedSource` and `FileContentsSeedSource` preserve relative paths and defer existence checks to the active filesystem provider. Their `file_pattern` matches basenames only: use `"*.md"`, not `"docs/*.md"`.
- Seed columns are not known until the seed reader compiles/loads the seed. If a prompt references `{{ product_description }}`, inspect the actual file to confirm that exact column name exists.
- Relative `LocalFileSeedSource` paths are resolved from the current working directory when the config is loaded. If a config file moved, update the seed path or load from the intended working directory.

## Managed persona assets absent

Symptoms include missing parquet files under the managed-assets datasets directory or runtime errors while loading a managed locale.

Actions:

1. Confirm `PersonSamplerParams(locale=...)` uses a managed locale.
2. Run `python ../scripts/inspect_person_schema.py <locale>` to see whether the locale asset is installed and what fields it exposes.
3. If assets are absent, either use `PersonFromFakerSamplerParams` for a config-only fallback or route persona download/runtime setup to CLI/runtime sub-skills.
4. Do not claim a managed persona field exists until the script or an installed package fact confirms it.

## Custom generator signature mistakes

The decorator enforces names, not just arity:

```python
@dd.custom_column_generator(required_columns=["source"], side_effect_columns=["extra"])
def gen(row: dict) -> dict:  # ok: first param named row
    row["target"] = row["source"].strip()
    row["extra"] = len(row["source"])
    return row
```

Rejected patterns:

- `def gen(record): ...` because param 1 must be `row` or `df`.
- `def gen(row, params): ...` because param 2 must be `generator_params`.
- `def gen(row, generator_params, model_clients): ...` because param 3 must be `models`.
- Omitting `@custom_column_generator`, so `CustomColumnConfig` cannot find metadata.

If a custom generator creates additional output columns, declare them as `side_effect_columns`; otherwise downstream Jinja references or allowed-reference checks may miss them.

## Drop versus processor confusion

Use `drop=True` on a helper column when the helper is an implementation detail:

```python
# Helper remains referenceable, but not in final output.
dd.SamplerColumnConfig(name="person", sampler_type="person_from_faker", params=dd.PersonFromFakerSamplerParams(), drop=True)
```

Use `DropColumnsProcessorConfig` when you need a named post-generation processor or glob removal:

```python
dd.DropColumnsProcessorConfig(name="cleanup", column_names=["raw_*", "helper"])
```

If a processor seems not to drop a column, check whether the column existed before `add_processor()` expanded its names. Re-add/update the processor after all matching columns are present.

## Validator misuse

- `ValidationColumnConfig.target_columns` must name existing columns.
- `CodeValidatorParams` supports Python and SQL dialects only; `CodeLang.RUBY` and other non-validator languages are rejected.
- `LocalCallableValidatorParams` can only carry live Python function objects; serialized config files cannot reconstruct arbitrary callables unless the user script creates them.
- `RemoteValidatorParams` only validates field shapes locally; endpoint availability, authentication, and retries are runtime concerns.

## Safe escalation

Escalate out of this sub-skill when:

- The config is well-formed but a model endpoint/API key/MCP server fails (`generation-runtime`).
- The user asks how to run `data-designer validate/preview/create` from shell or inspect agent context (`cli-and-agent-tools`).
- A plugin package must be installed or a new entry-point plugin config class must be registered (`plugins-and-extensions`).
- The user wants an end-to-end recipe choice such as image generation, trace ingestion, workflow chaining, or Hugging Face export (`recipes-and-integrations`).
