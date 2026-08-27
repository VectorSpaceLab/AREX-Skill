# Config API Reference

This reference is self-contained for the DataDesigner 0.9.1 config surface. It was distilled from the public `data_designer.config` package, config architecture notes, config tests, and installed-package inspection facts. If the installed package changes, refresh live facts with:

```bash
python ../scripts/dump_config_type_catalog.py
```

From this `references/` directory use `python ../scripts/dump_config_type_catalog.py`; from the sub-skill root use `python scripts/dump_config_type_catalog.py`.

## Imports and package split

Use public lazy exports through:

```python
import data_designer.config as dd
```

The config package owns declarative objects only. Config objects validate and serialize declarations; they do not execute generation. Runtime execution (`DataDesigner.preview`, `create`, `check_models`, artifacts, resume) belongs to [`generation-runtime`](../../generation-runtime/SKILL.md). Cross-package architecture lives in the root [package overview](../../../references/package-overview.md).

## Public config exports by family

Installed inspection reported `data_designer.config.__all__` has 90 public exports. High-use groups:

| Family | Public exports to prefer |
| --- | --- |
| Builder/root | `DataDesignerConfigBuilder`, `DataDesignerConfig`, `DataDesignerScriptParams`, `get_library_version` |
| Columns | `SamplerColumnConfig`, `LLMTextColumnConfig`, `LLMCodeColumnConfig`, `LLMStructuredColumnConfig`, `LLMJudgeColumnConfig`, `EmbeddingColumnConfig`, `ImageColumnConfig`, `ExpressionColumnConfig`, `ValidationColumnConfig`, `SeedDatasetColumnConfig`, `CustomColumnConfig`, `Score`, `GenerationStrategy`, `DataDesignerColumnType`, `SkipConfig` |
| Samplers | `SamplerType`, `CategorySamplerParams`, `SubcategorySamplerParams`, `UniformSamplerParams`, `GaussianSamplerParams`, `BernoulliSamplerParams`, `BernoulliMixtureSamplerParams`, `BinomialSamplerParams`, `PoissonSamplerParams`, `ScipySamplerParams`, `UUIDSamplerParams`, `DatetimeSamplerParams`, `TimeDeltaSamplerParams`, `PersonSamplerParams`, `PersonFromFakerSamplerParams` |
| Seed | `LocalFileSeedSource`, `HuggingFaceSeedSource`, `DataFrameSeedSource`, `DirectorySeedSource`, `FileContentsSeedSource`, `AgentRolloutSeedSource`, `AgentRolloutFormat`, `SeedConfig`, `SamplingStrategy`, `IndexRange`, `PartitionBlock` |
| Models/tools | `ModelConfig`, `ModelProvider`, `ChatCompletionInferenceParams`, `EmbeddingInferenceParams`, `ImageInferenceParams`, `ManualDistribution`, `ManualDistributionParams`, `UniformDistribution`, `UniformDistributionParams`, `MCPProvider`, `LocalStdioMCPProvider`, `ToolConfig` |
| Validators/processors | `CodeValidatorParams`, `LocalCallableValidatorParams`, `RemoteValidatorParams`, `ValidatorType`, `DropColumnsProcessorConfig`, `SchemaTransformProcessorConfig`, `ProcessorType` |
| Multimodal/util enums | `ImageContext`, `AudioContext`, `VideoContext`, `Modality`, `ModalityDataType`, `ImageFormat`, `AudioFormat`, `VideoFormat`, `TraceType`, `CodeLang`, `ResumeMode`, `RunConfig` |

## Builder API shapes

Installed-package signatures verified these public builder methods:

```text
DataDesignerConfigBuilder(
    model_configs: list[ModelConfig] | str | Path | None = None,
    tool_configs: list[ToolConfig] | None = None,
)

add_column(column_config: ColumnConfigT | None = None, *, name: str | None = None, column_type: DataDesignerColumnType | None = None, **kwargs) -> Self
add_constraint(constraint: ColumnConstraintT | None = None, *, constraint_type: ConstraintType | None = None, **kwargs) -> Self
add_processor(processor_config: ProcessorConfigT | None = None, *, processor_type: ProcessorType | None = None, **kwargs) -> Self
add_profiler(profiler_config: ColumnProfilerConfigT) -> Self
with_seed_dataset(seed_source: SeedSourceT, *, sampling_strategy: SamplingStrategy = SamplingStrategy.ORDERED, selection_strategy: IndexRange | PartitionBlock | None = None) -> Self
build() -> DataDesignerConfig
from_config(config: dict | str | Path | BuilderConfig) -> Self
get_column_config(name: str) -> ColumnConfigT
get_column_configs() -> list[ColumnConfigT]
get_profilers() -> list[ColumnProfilerConfigT]
delete_column(column_name: str) -> Self
delete_constraints(target_column: str) -> Self
delete_model_config(alias: str) -> Self
delete_tool_config(alias: str) -> Self
```

Builder behavior to rely on:

- `add_column(config_obj)` accepts a concrete Pydantic config object.
- `add_column(name=..., column_type=..., **kwargs)` resolves the concrete class by `column_type`; for sampler columns it also resolves the `sampler_type` to the expected params class.
- Adding a column with an existing name replaces the prior config.
- `add_processor()` upserts processors by name; a `DropColumnsProcessorConfig` also marks matching existing columns `drop=True`.
- `from_config(...)` accepts a full `BuilderConfig` shape (`data_designer: ...`) and a shorthand `DataDesignerConfig` shape with top-level `columns`; shorthand is auto-wrapped.
- `write_config(path)` supports `.yaml`, `.yml`, and `.json`. It raises for `DataFrameSeedSource` because in-memory dataframes are not serializable.

## Runtime interface signatures that affect config work

Use these only to decide boundaries and validation handoff; execution details are in [`generation-runtime`](../../generation-runtime/SKILL.md).

```text
DataDesigner(
    artifact_path: Path | str | None = None,
    *,
    model_providers: list[ModelProvider] | None = None,
    secret_resolver: SecretResolver | None = None,
    seed_readers: list[SeedReader] | None = None,
    managed_assets_path: Path | str | None = None,
    person_reader: PersonReader | None = None,
    mcp_providers: list[MCPProviderT] | None = None,
    auto_configure_logging: bool = True,
)

validate(config_builder: DataDesignerConfigBuilder) -> None
preview(config_builder: DataDesignerConfigBuilder, *, num_records: int = 10) -> PreviewResults
create(config_builder: DataDesignerConfigBuilder, *, num_records: int = 10, dataset_name: str = "dataset", resume: ResumeMode = ResumeMode.NEVER, artifact_path: Path | str | None = None, on_batch_complete: Callable[[Path], None] | None = None) -> DatasetCreationResults
check_models(config_builder: DataDesignerConfigBuilder, *, max_attempts: int = 1, retry_backoff_seconds: float = 0) -> None
```

Config-only guidance:

- `builder.build()` is the cheap Pydantic/config object validation step.
- `DataDesigner().validate(builder)` compiles with configured engine resources and seed/person readers but does not generate records.
- `preview`, `create`, and `check_models` can call model endpoints or runtime resources; route those decisions to `generation-runtime`.
- Installed agent-context evidence says no usable model aliases exist by default. For sampler/expression/seed-only configs this is fine; for model-backed columns create explicit `ModelConfig(alias=...)` entries and use the same alias in columns.

## Root config and discriminators

`DataDesignerConfig` fields:

```text
columns, model_configs, tool_configs, seed_config, constraints, profilers, processors
```

Every deserializable family uses a discriminator field. Wrong discriminator names are a common source of confusing validation errors.

| Object location | Discriminator | Values/classes |
| --- | --- | --- |
| `DataDesignerConfig.columns` | `column_type` | Built-in column types: `seed-dataset`, `sampler`, `llm-text`, `llm-code`, `llm-structured`, `llm-judge`, `embedding`, `image`, `validation`, `expression`, `custom` |
| `SamplerColumnConfig.params` and `conditional_params` | `sampler_type` | `uuid`, `category`, `subcategory`, `uniform`, `gaussian`, `bernoulli`, `bernoulli_mixture`, `binomial`, `poisson`, `scipy`, `person`, `person_from_faker`, `datetime`, `timedelta` |
| `ValidationColumnConfig.validator_params` | `validator_type` | `code`, `local_callable`, `remote` |
| `ModelConfig.inference_parameters` | `generation_type` | `chat-completion`, `embedding`, `image` |
| `DataDesignerConfig.processors` | `processor_type` | `drop_columns`, `schema_transform` |
| `SeedConfig.source` | `seed_type` | `local`, `hf`, `df`, `directory`, `file_contents`, `agent_rollout` |
| MCP provider config | `provider_type` | `sse`, `streamable_http`, `stdio` |
| Constraints | `constraint_type` | `scalar_inequality`, `column_inequality`; legacy shapes may be inferred from `rhs` |

## Model, provider, tool, validator, and processor fields

Use these verified field sets when hand-authoring configs or debugging serialized YAML/JSON.

### Model and inference configs

| Class | Fields | Notes |
| --- | --- | --- |
| `ModelConfig` | `alias`, `model`, `inference_parameters`, `provider`, `skip_health_check` | Alias is what columns reference via `model_alias`. `provider` must match a configured provider name. |
| `ModelProvider` | `name`, `endpoint`, `provider_type`, `api_key`, `extra_body`, `extra_headers` | `provider_type` normalizes to lowercase; default is OpenAI-compatible. |
| `ChatCompletionInferenceParams` | `generation_type`, `max_parallel_requests`, `timeout`, `extra_body`, `temperature`, `top_p`, `max_tokens` | `temperature` and `top_p` may be fixed floats or `UniformDistribution`/`ManualDistribution`. |
| `EmbeddingInferenceParams` | `generation_type`, `max_parallel_requests`, `timeout`, `extra_body`, `encoding_format`, `dimensions` | `generation_type="embedding"`; `encoding_format` is `float` or `base64`. |
| `ImageInferenceParams` | `generation_type`, `max_parallel_requests`, `timeout`, `extra_body` | Model-specific image parameters belong in `extra_body`. |
| `ManualDistributionParams` | `values`, `weights` | Weights normalize and must match values length. |
| `UniformDistributionParams` | `low`, `high` | `low < high`. |
| `ManualDistribution` / `UniformDistribution` | `distribution_type`, `params` | Used for sampling inference params such as temperature/top-p. |

### MCP/tool configs

| Class | Fields | Notes |
| --- | --- | --- |
| `ToolConfig` | `tool_alias`, `providers`, `allow_tools`, `max_tool_call_turns`, `timeout_sec` | LLM columns reference `tool_alias`; duplicate tool names in `allow_tools` are rejected by `builder.build()`. |
| `MCPProvider` | `provider_type`, `name`, `endpoint`, `api_key` | Remote SSE or Streamable HTTP provider. |
| `LocalStdioMCPProvider` | `provider_type`, `name`, `command`, `args`, `env` | Local subprocess provider. Package install/discovery belongs to `plugins-and-extensions`; runtime checks belong to `generation-runtime`. |

### Validator params

| Class | Fields | Notes |
| --- | --- | --- |
| `CodeValidatorParams` | `validator_type`, `code_lang` | Supports Python and SQL dialects in `CodeLang`; other languages are rejected. |
| `LocalCallableValidatorParams` | `validator_type`, `validation_function`, `output_schema` | Function must be callable; output should contain an `is_valid: bool` column when executed locally. |
| `RemoteValidatorParams` | `validator_type`, `endpoint_url`, `output_schema`, `timeout`, `max_retries`, `retry_backoff`, `max_parallel_requests` | Network runtime behavior belongs to `generation-runtime`; config validation checks field bounds. |

### Processor configs

| Class | Fields | Notes |
| --- | --- | --- |
| `DropColumnsProcessorConfig` | `name`, `processor_type`, `column_names` | Can use glob patterns matched against known columns; builder marks matches `drop=True`. Prefer column-level `drop=True` for one helper column. |
| `SchemaTransformProcessorConfig` | `name`, `processor_type`, `template` | Template values must be JSON-serializable and may contain Jinja strings. |

## Seed fields at a glance

Detailed seed/person workflows are in [`seed-and-person-data.md`](seed-and-person-data.md).

| Class | Fields |
| --- | --- |
| `SeedConfig` | `source`, `sampling_strategy`, `selection_strategy` |
| `IndexRange` | `start`, `end` |
| `PartitionBlock` | `index`, `num_partitions` |
| `LocalFileSeedSource` | `seed_type`, `path` |
| `HuggingFaceSeedSource` | `seed_type`, `path`, `token`, `endpoint` |
| `DataFrameSeedSource` | `seed_type`, `df` |
| `DirectorySeedSource` | `seed_type`, `path`, `file_pattern`, `recursive` |
| `FileContentsSeedSource` | `seed_type`, `path`, `file_pattern`, `recursive`, `encoding` |
| `AgentRolloutSeedSource` | `seed_type`, `path`, `file_pattern`, `recursive`, `format` |

## Minimal config skeleton

```python
from __future__ import annotations

import data_designer.config as dd


def load_config_builder() -> dd.DataDesignerConfigBuilder:
    builder = dd.DataDesignerConfigBuilder(
        model_configs=[
            # Add only when model-backed columns need this alias.
            # dd.ModelConfig(alias="text", model="...", provider="..."),
        ]
    )
    builder.add_column(
        dd.SamplerColumnConfig(
            name="record_id",
            sampler_type=dd.SamplerType.UUID,
            params=dd.UUIDSamplerParams(prefix="REC-", short_form=True),
        )
    )
    builder.add_column(
        dd.ExpressionColumnConfig(name="record_label", expr="{{ record_id }}", dtype="str")
    )
    builder.build()  # cheap local config validation
    return builder
```
