# Plugin API reference

## Verified public surfaces

- `nerfstudio.plugins.types.MethodSpecification`
- `nerfstudio.plugins.registry_dataparser.DataParserSpecification`
- `nerfstudio.plugins.registry.discover_methods()`
- `nerfstudio.plugins.registry_dataparser.discover_dataparsers()`

## How the registries behave

- Methods are keyed by `method_name` and appear in `ns-train --help` when registered.
- Dataparsers are keyed by their registration name and appear in the training CLI path when referenced.
- The registries accept class, function, or object style values when they resolve to the expected specification objects.
- Environment variable registration is meant for temporary development and testing; package entry points are the durable distribution mechanism.

## Related built-in config objects

- `nerfstudio.engine.trainer.TrainerConfig`
- Pipeline configs such as `VanillaPipelineConfig` and `DynamicBatchPipelineConfig`
- Dataparser configs such as `NerfstudioDataParserConfig`, `BlenderDataParserConfig`, and other built-in dataset parsers

## Quick sanity check

The plugin registry tests verify that custom method/dataparser objects can be discovered both from entry points and from the environment variables. Use those tests as the behavioral reference for a new extension package.
