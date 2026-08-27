# CLI and Automation Troubleshooting

## Config discovery and loading

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `could not determine config path` | None of the configured locations contains a valid config file | Pass `-c`, set `NML_CONFIG_PATH`, or place `nannyml.yaml` / `nann.yml` in one of the supported locations. |
| `nml -c <cfg> run --help` fails even though help was requested | The root CLI callback loads configuration before subcommand help renders | Use a tiny valid config file for help checks. |
| Config changes do not seem to apply in a long-lived Python session | `Config.load` is cached with `lru_cache` | Restart the process or clear the cache before reloading the same path. |
| Path-templating error | One of the configured paths contains an invalid Jinja expression | Simplify the path template and keep only the supported placeholders. |

## Scheduling problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Scheduling error about missing subsections | `scheduling` exists but neither `cron` nor `interval` is defined | Add exactly one subsection or remove `scheduling` entirely. |
| Scheduling error about multiple subsections | Both `cron` and `interval` were provided | Keep only one scheduling subsection. |
| Interval scheduling error about multiple values | More than one interval unit was set | Set exactly one of `weeks`, `days`, `hours`, or `minutes`. |
| Interval scheduling error about no values | The interval block is empty | Set at least one unit. |

## File reading and writing problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Unsupported file suffix | `FileReader` only supports `.csv`, `.pq`, and `.parquet` | Convert the file or change the suffix to one of the supported formats. |
| Missing writer filename | `RawFilesWriter`, `PickleFileWriter`, or `FilesystemStore` was called without a filename | Pass `filename` explicitly in the write/store call or in the config block. |
| CSV/Parquet writer failure on cloud paths | Missing credentials or unsupported storage options | Add the required `fsspec` credentials for the target cloud filesystem. |
| Pickle writer failure on a non-pickleable object | The object is not serializable | Use `RawFilesWriter` instead if you only need the tabular result data. |
| Empty-result writer failure | The result object was empty | Check earlier filters and ensure the calculator actually produced data. |

## Optional database writer

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `sqlmodel` module is not available | The optional `db` extra is not installed | Install `pip install 'nannyml[db]'`. |
| Database writer import fails immediately | Database dependencies or driver packages are missing | Install the optional extra and verify the connection string. |
| Database initialization error | The connection string is invalid or the backend is unavailable | Verify the SQLAlchemy URL and that the database accepts connections. |
| Result does not write to the expected table | The result type selects a different mapper/table | Confirm the calculator/result type and inspect the writer output table names. |

## Result of a scheduled run looks stale

- Confirm the config path points to the file you edited.
- Confirm the scheduler is using the expected config after rendering path templates.
- If you are reusing a store, make sure `invalidate: true` is not unintentionally forcing refits or that `filename` matches the cached object.
- Confirm the monitored data paths and output paths are not templated into different dates than you expected.

## When to route elsewhere

- Missing columns, incompatible metrics, or threshold logic -> monitoring/data-setup sub-skills.
- `pkg_resources` / `setuptools<81` / package install issues -> the root troubleshooting reference.
- If the problem is not about commands, config files, writers, or stores, route to the nearest monitoring sub-skill.
