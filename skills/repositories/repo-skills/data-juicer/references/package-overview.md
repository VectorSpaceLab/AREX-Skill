# Package overview

## Top-level package map
- `data_juicer.config`: configuration parsing, default configs, custom operator loading, and job directory helpers.
- `data_juicer.core`: `Analyzer`, `Exporter`, `NestedDataset`, executors, `RayAnalyzer`, `RayExporter`, `Monitor`, `Tracer`, and related execution plumbing.
- `data_juicer.ops`: operator registry and built-in operator families.
- `data_juicer.format`: format loading and formatting utilities.
- `data_juicer.tools`: console-script entrypoints and MCP helpers.
- `data_juicer.utils`: shared helpers for config, cache, JSONL loading, resources, Ray, checkpoints, jobs, and logging.

## Root-facing APIs worth knowing
- `get_default_cfg`
- `get_init_configs`
- `DatasetBuilder`
- `Analyzer`
- `Exporter`
- `DefaultExecutor`
- `ExecutorFactory`
- `RayAnalyzer`
- `RayExporter`
- `Monitor`
- `Tracer`
- `search_ops`
- `get_global_config_schema`
- `get_dataset_load_strategies`
- `run_data_recipe`
- `analyze_dataset`

## Routing hint
- Use `recipes-and-ops` for config, dataset, export, and utility questions.
- Use `ray-and-recovery` for executor and recovery questions.
- Use `service-mcp` for API, MCP, and operator-search questions.
