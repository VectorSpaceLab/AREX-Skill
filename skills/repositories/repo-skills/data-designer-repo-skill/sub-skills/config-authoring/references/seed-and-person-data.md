# Seed Sources and Person Data

Use this when a DataDesigner config starts from existing records or needs realistic person fields. For sampler field tables see [`columns-and-samplers.md`](columns-and-samplers.md); for generation and artifact behavior route to [`generation-runtime`](../../generation-runtime/SKILL.md).

## Seed source decision table

Seed datasets are attached to a builder with `builder.with_seed_dataset(...)`; users normally do **not** add `SeedDatasetColumnConfig` objects manually.

| Source class | `seed_type` | Fields | Use when | Serialization notes |
| --- | --- | --- | --- | --- |
| `LocalFileSeedSource` | `local` | `path` | Local `.parquet`, `.csv`, `.json`, `.jsonl`, or wildcard partitions. | Serializable. Relative paths are resolved from the current working directory when config is loaded, not from the config file's directory. |
| `HuggingFaceSeedSource` | `hf` | `path`, `token`, `endpoint` | Data lives in Hugging Face datasets/storage. | Serializable, but token handling belongs to runtime/secret policy. |
| `DataFrameSeedSource` | `df` | `df` | In-memory Python API experiments. | Not serializable; `df` is excluded from dumps. Use `LocalFileSeedSource.from_dataframe(df, path)` before writing YAML/JSON. |
| `DirectorySeedSource` | `directory` | `path`, `file_pattern`, `recursive` | A reader should turn files in a directory into seed rows. | Serializable. Existence/read checks happen through runtime seed readers. |
| `FileContentsSeedSource` | `file_contents` | `path`, `file_pattern`, `recursive`, `encoding` | Each matching text file should become a seed row with decoded `content`. | Serializable. `file_pattern` matches file basenames, not relative paths; `encoding` must be a known Python codec. |
| `AgentRolloutSeedSource` | `agent_rollout` | `format`, `path`, `file_pattern`, `recursive` | Ingest built-in agent trace formats such as `atif`, `claude_code`, `codex`, `hermes_agent`, `pi_coding_agent`. | Serializable. Some formats have default paths; ATIF requires `path`. Recipe selection belongs to `recipes-and-integrations`. |

## Seed config controls

```python
builder.with_seed_dataset(
    dd.LocalFileSeedSource(path="seed/products.parquet"),
    sampling_strategy=dd.SamplingStrategy.SHUFFLE,
    selection_strategy=dd.IndexRange(start=0, end=99),
)
```

Fields:

- `SamplingStrategy.ORDERED` reads rows in original order.
- `SamplingStrategy.SHUFFLE` shuffles before sampling; when a selection strategy exists, shuffling applies within the selected range/partition.
- `IndexRange(start, end)` uses inclusive zero-based row indices and requires `start <= end`.
- `PartitionBlock(index, num_partitions)` selects one zero-based partition and requires `index < num_partitions`.

## Seed authoring checklist

1. **Verify the file/source before wiring it.** Confirm path, extension, readability, and exact column names with a local reader (`pandas`, `pyarrow`, or the service-specific tool). Do not guess seed column names.
2. **Attach the seed once.** Use `with_seed_dataset(...)`; seed columns are discovered by runtime readers and become Jinja variables during compilation.
3. **Reference seed fields directly.** If the seed has `diagnosis` and `patient_summary`, prompts can use `{{ diagnosis }}` and `{{ patient_summary }}`.
4. **Do not manually duplicate seed columns.** Adding a manual `SeedDatasetColumnConfig` is normally wrong; the builder/engine handles them from `seed_config`.
5. **Choose a serializable source if writing YAML/JSON.** `DataFrameSeedSource` is useful for tests and notebooks, but `builder.write_config(...)` raises until it is replaced by a file-backed source.

Example:

```python
builder = dd.DataDesignerConfigBuilder(model_configs=[...])
builder.with_seed_dataset(dd.LocalFileSeedSource(path="symptoms.csv"))
builder.add_column(
    dd.SamplerColumnConfig(
        name="patient",
        sampler_type="person_from_faker",
        params=dd.PersonFromFakerSamplerParams(locale="en_US"),
        drop=True,
    )
)
builder.add_column(dd.ExpressionColumnConfig(name="patient_name", expr="{{ patient.first_name }} {{ patient.last_name }}"))
builder.add_column(
    dd.LLMTextColumnConfig(
        name="note",
        model_alias="text",
        prompt="Write a clinical note for {{ patient_name }}. Diagnosis: {{ diagnosis }}. Symptoms: {{ patient_summary }}.",
    )
)
```

## Person sampler choices

| `sampler_type` | Params class | Best use | Key fields |
| --- | --- | --- | --- |
| `person` | `PersonSamplerParams` | Realistic managed persona data with demographic consistency. | `locale`, `sex`, `city`, `age_range`, `select_field_values`, `with_synthetic_personas` |
| `person_from_faker` | `PersonFromFakerSamplerParams` | Fast fallback/prototyping when managed locale assets are absent or demographic grounding is unnecessary. | `locale`, `sex`, `city`, `age_range` |

Current managed persona locales from config constants: `en_US`, `en_IN`, `en_SG`, `fr_FR`, `hi_Deva_IN`, `hi_Latn_IN`, `ja_JP`, `ko_KR`, `pt_BR`.

`PersonSamplerParams` validates that `locale` is one of the managed locales. The managed dataset also has to be downloaded/available at runtime. If the locale is unsupported or absent locally, either route to the CLI/runtime persona download workflow or use `person_from_faker` as a config-only fallback.

## Inspect managed person schema

Managed person fields vary by locale and by `with_synthetic_personas`. Inspect before writing Jinja expressions:

```bash
python ../scripts/inspect_person_schema.py en_US
```

From the sub-skill root:

```bash
python scripts/inspect_person_schema.py en_US --json
```

The helper reads the installed package's managed-assets location or an override from `--managed-assets-path`; it exits with a clear message if pyarrow, the DataDesigner package, or the locale parquet file is missing.

## Keep full person object versus extract selected fields

Keep the full object when downstream consumers need many demographic/persona fields, or when the user explicitly asks for the full nested person record:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="person",
        sampler_type=dd.SamplerType.PERSON,
        params=dd.PersonSamplerParams(locale="en_US"),
    )
)
```

Extract a few fields and drop the helper when the final dataset should have simple flat columns:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="person",
        sampler_type="person",
        params=dd.PersonSamplerParams(locale="en_US"),
        drop=True,
    )
)
builder.add_column(dd.ExpressionColumnConfig(name="full_name", expr="{{ person.first_name }} {{ person.last_name }}"))
builder.add_column(dd.ExpressionColumnConfig(name="city", expr="{{ person.city }}"))
builder.add_column(dd.ExpressionColumnConfig(name="age", expr="{{ person.age }}", dtype="int"))
```

Switching from full object to extracted fields only requires adding `drop=True` on the person helper and adding expression columns. Do not drop the person column before all dependent expressions/prompts have been defined; `drop=True` does not prevent downstream references during generation.

## Synthetic persona fields

Use `with_synthetic_personas=True` only with `sampler_type="person"`:

```python
builder.add_column(
    dd.SamplerColumnConfig(
        name="persona",
        sampler_type="person",
        params=dd.PersonSamplerParams(locale="en_US", with_synthetic_personas=True),
        drop=True,
    )
)
builder.add_column(dd.ExpressionColumnConfig(name="interests", expr="{{ persona.hobbies_and_interests }}"))
```

Guidelines:

- Run `inspect_person_schema.py` for the exact locale before referencing persona-only fields.
- If persona assets are absent, config construction may validate but runtime person loading will fail; classify this as an optional managed-asset/runtime readiness issue and route downloads/checks outside this sub-skill.
- Faker person data does not provide managed synthetic persona fields.

## Field filters

`PersonSamplerParams` supports both convenience filters and flexible managed-dataset filters:

```python
dd.PersonSamplerParams(
    locale="en_US",
    sex="Female",
    city=["New York", "San Francisco"],
    age_range=[25, 45],
    select_field_values={"education_level": ["bachelors", "some_college"]},
)
```

Use `sex`, `city`, and `age_range` when possible. Reserve `select_field_values` for fields confirmed by `inspect_person_schema.py`; rare combinations may not be represented enough for runtime sampling.

## Seed plus person pattern

When a config combines seed rows and sampled people, keep naming explicit so Jinja references are unambiguous:

```python
builder.with_seed_dataset(dd.LocalFileSeedSource(path="products.parquet"))

builder.add_column(
    dd.SamplerColumnConfig(
        name="customer",
        sampler_type="person_from_faker",
        params=dd.PersonFromFakerSamplerParams(locale="en_US"),
        drop=True,
    )
)
builder.add_column(dd.ExpressionColumnConfig(name="customer_name", expr="{{ customer.first_name }} {{ customer.last_name }}"))

builder.add_column(
    dd.LLMTextColumnConfig(
        name="review_prompt",
        model_alias="text",
        prompt=(
            "Customer: {{ customer_name }}\n"
            "Seed product: {{ product_name }}\n"
            "Seed description: {{ product_description }}\n"
            "Write a realistic review."
        ),
    )
)
```

Validate in stages:

1. Build seed source and sampler/expression columns; call `builder.build()`.
2. If seed reader and interface are installed, call `DataDesigner().validate(builder)` to catch missing seed columns/compile issues.
3. Route preview/create or model checks to `generation-runtime`.
