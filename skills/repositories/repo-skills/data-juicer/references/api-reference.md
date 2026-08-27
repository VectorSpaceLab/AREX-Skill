# API reference

## Core package surface
`data_juicer.core.__all__` exports:
- `Adapter`
- `Analyzer`
- `NestedDataset`
- `ExecutorBase`
- `ExecutorFactory`
- `DefaultExecutor`
- `Exporter`
- `RayAnalyzer`
- `RayExporter`
- `Monitor`
- `Tracer`

## Core helpers
- `data_juicer.config.config.get_default_cfg`
- `data_juicer.config.config.get_init_configs`
- `data_juicer.config.config.load_custom_operators`
- `data_juicer.config.config.resolve_job_directories`
- `data_juicer.config.config.resolve_job_id`
- `data_juicer.core.data.dataset_builder.DatasetBuilder(cfg, executor_type='default')`

## Service / MCP helpers
- `data_juicer.tools.DJ_mcp_recipe_flow.search_ops`
- `data_juicer.tools.DJ_mcp_recipe_flow.get_global_config_schema`
- `data_juicer.tools.DJ_mcp_recipe_flow.get_dataset_load_strategies`
- `data_juicer.tools.DJ_mcp_recipe_flow.run_data_recipe`
- `data_juicer.tools.DJ_mcp_recipe_flow.analyze_dataset`
- `data_juicer.tools.mcp_server.main`

## How to use this reference
- Use the core helpers when reasoning about configs, dataset loading, and execution objects.
- Use the service helpers when reasoning about route shapes or MCP tool behavior.
- Use the sub-skills for concrete workflow instructions and troubleshooting.
