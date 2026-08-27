# Extension Workflows

This reference covers ModelScope-specific extension points for custom pipelines,
models, preprocessors, CLI template scaffolding, registration, configuration,
and trust boundaries. It is self-contained: evidence came from the ModelScope
pipeline command documentation, the pipeline CLI implementation, the bundled
pipeline template, registry utilities, import utilities, config trust checks,
plugin helpers, and custom pipeline tests.

## Choose the extension path

Use one of these paths before writing code:

| User intent | Recommended path | Safety notes |
| --- | --- | --- |
| Try an existing task/model | Route to `../pipelines-and-models/SKILL.md` | May download models unless local/offline arguments are used. |
| Wrap local logic as a ModelScope pipeline | Use the CLI scaffold planner, then run `modelscope pipeline --action create` only after reviewing the plan | Scaffold writes a Python file and generated file may write config at top level. |
| Add a reusable component inside a ModelScope checkout | Implement a package module, register it, add focused tests, and update lazy import/indexing if required by the repository workflow | Repository edits should follow contributor guidance. |
| Load third-party or hub-provided extension code | Require explicit trust review before plugins, `allow_remote`, or `trust_remote_code=True` | These paths execute Python from outside the installed SDK. |

## CLI scaffold command

ModelScope exposes a pipeline scaffold command:

```bash
modelscope pipeline --action create \
  --tpl_file_path template.tpl \
  --save_file_path ./ \
  --filename ms_wrapper.py \
  --task_name THE_PIPELINE_TASK \
  --model_name MyCustomModel \
  --preprocessor_name MyCustomPreprocessor \
  --pipeline_name MyCustomPipeline \
  --configuration_path ./
```

Short option aliases are also supported:

```bash
modelscope pipeline -act create -tpl template.tpl -s ./ -f ms_wrapper.py \
  -t THE_PIPELINE_TASK -m MyCustomModel -p MyCustomPreprocessor \
  -pp MyCustomPipeline -config ./
```

Arguments:

| Long option | Alias | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `--action` | `-act` | yes | none | Only `create` is supported. |
| `--tpl_file_path` | `-tpl` | no | `template.tpl` | Template file. If the name matches a bundled template, the CLI uses ModelScope's bundled template; otherwise it treats the value as a filesystem path. |
| `--save_file_path` | `-s` | no | `./` | Directory where the generated wrapper Python file is written. The CLI creates this directory if needed. |
| `--filename` | `-f` | no | `ms_wrapper.py` | Generated Python filename. The CLI rejects names that do not end with `.py`. |
| `--task_name` | `-t` | yes | none | Registry group/task key for the custom components. |
| `--model_name` | `-m` | no | `MyCustomModel` | Generated model class name. |
| `--preprocessor_name` | `-p` | no | `MyCustomPreprocessor` | Generated preprocessor class name. |
| `--pipeline_name` | `-pp` | no | `MyCustomPipeline` | Generated pipeline class name. |
| `--configuration_path` | `-config` | no | `./` | Directory where generated code writes `configuration.json`. The CLI appends a trailing slash internally. |

Use the bundled safe planner before the real command:

```bash
python scripts/pipeline_template_plan.py --task_name my-task --filename ms_wrapper.py
```

The real ModelScope command writes files. The bundled planner only prints the
command.

## Template review checklist

The stock template registers three classes and emits a config object:

- `@MODELS.register_module(task_name, module_name='my-custom-model')`
- `@PREPROCESSORS.register_module(task_name, module_name='my-custom-preprocessor')`
- `@PIPELINES.register_module(task_name, module_name='my-custom-pipeline')`
- `Config({...}).dump(configuration_path + 'configuration.json')`

Before using generated code:

1. Rename the module names from `my-custom-*` to stable names for the package or
   model repo.
2. Remove or guard top-level writes. Prefer placing config generation under an
   explicit function or `if __name__ == "__main__":` block so importing the
   module only registers classes.
3. Replace placeholder model/preprocessor logic with deterministic local logic
   or explicit dependency checks.
4. Implement `Pipeline.preprocess`, `forward`, `postprocess`, and, if useful,
   `_sanitize_parameters`, `_check_input`, `_check_output`, and `_batch`.
5. Add a local smoke test that imports the module, checks registry entries, and
   builds a pipeline from a local directory containing `configuration.json`.
6. Keep hub uploads, remote model downloads, and training out of scaffolding
   verification unless the user explicitly requests them and accepts the cost.

## Registration model

ModelScope registries group modules by task or field. The core registry API is:

```python
@REGISTRY.register_module(group_key, module_name='alias')
class MyComponent:
    ...
```

A component can also be registered imperatively with
`register_module(group_key=..., module_name=..., module_cls=...)`. The registry
stores entries as `registry.modules[group_key][module_name]`. If an alias is
already registered and `force=False`, registration raises a duplicate-key error.

Common registries for this sub-skill:

```python
from modelscope.models.builder import MODELS
from modelscope.preprocessors.builder import PREPROCESSORS
from modelscope.pipelines.builder import PIPELINES
```

Key points:

- The `group_key` is usually the task name for models and pipelines. For
  preprocessors, builders may use a field name, but the template uses the task
  name for a custom pipeline wrapper.
- The `module_name` is the value used in configuration `type` fields and in
  explicit `pipeline_name` arguments.
- Decorators run when the module is imported. If a custom class is in a local
  file, import that file before calling `pipeline(...)` or `build_from_cfg(...)`.
- Built-in ModelScope modules can be lazily imported from an AST index. Custom
  local modules are not visible until imported or packaged as plugins.

## Minimal `configuration.json` shape

For a local custom pipeline directory, the configuration file must identify the
framework, task, and pipeline type. Add a model section when the pipeline builds
a registered model type.

Pipeline-only routing example:

```json
{
  "framework": "pytorch",
  "task": "my-task",
  "pipeline": {
    "type": "my-custom-pipeline"
  }
}
```

Pipeline plus model example:

```json
{
  "framework": "pytorch",
  "task": "my-task",
  "model": {
    "type": "my-custom-model"
  },
  "preprocessor": {
    "type": "my-custom-preprocessor"
  },
  "pipeline": {
    "type": "my-custom-pipeline"
  }
}
```

The exact sections used depend on the pipeline implementation. Tests in the
repository demonstrate that a local directory with `configuration.json` and a
`pipeline.type` can build a registered custom pipeline when the task and
pipeline alias match.

## Local smoke workflow

A safe local verification workflow can avoid model downloads:

1. Create a temporary model directory.
2. Write a minimal `configuration.json` with a dummy framework, custom task, and
   `pipeline.type` matching the registered alias.
3. Import the custom module so registration decorators execute.
4. Assert the alias exists in `PIPELINES.modules[task]`.
5. Build with `pipeline(task=task, pipeline_name=alias, model=temp_model_dir)`.
6. Call the pipeline on synthetic input that requires no network or GPU.

The native custom pipeline tests use this pattern for custom image, batch, and
chat pipelines. When adapting it, avoid LFS image fixtures unless they are
already available; use synthetic strings, dictionaries, or generated arrays.

## Trust and code execution boundaries

ModelScope deliberately gates several extension mechanisms because they execute
Python:

- Python config files: `Config.from_file(..., trust_remote_code=False)` refuses
  untrusted `.py` config files from model repositories. JSON and YAML are
  passive data formats and do not execute Python.
- `pipeline(..., trust_remote_code=False)`: when a model configuration declares
  `plugins` or `allow_remote`, pipeline loading refuses to proceed unless the
  user explicitly opts in with `trust_remote_code=True` or the model is in a
  trusted owner group.
- `allow_remote`: when enabled with trust, ModelScope can import code from a
  downloaded model repository. This is equivalent to running external Python.
- Plugin files: local/global `.modelscope_plugins` plugin lists and explicit
  plugin requirements cause imports, and some helpers can install missing plugin
  packages.
- Local custom modules: importing a generated wrapper file executes all top-level
  statements in that file.

Default policy for agents:

1. Prefer local JSON/YAML config plus explicit imports of code the user owns.
2. Do not set `allow_remote` or `trust_remote_code=True` automatically.
3. If trust is required, name the code source, why it needs execution, what it
   may import/install, and how to isolate it.
4. Never mix a security decision with a download/training command in the same
   step. Ask for trust first, then plan execution.

## Packaging a plugin or repository extension

For a reusable external extension:

1. Put ModelScope registration decorators in a normal importable module.
2. Keep import side effects limited to registration. Do not download models,
   train, mutate caches, or write files at import time.
3. Provide a minimal local smoke test and at least one config-driven build test.
4. Document optional dependencies and backends separately from core imports.
5. If distributed as a plugin package, ensure the plugin module can be imported
   in a fresh Python process and that users understand the trust boundary before
   adding it to plugin files or model configs.

For an in-repository ModelScope contribution, follow `contributor-guidance.md`
for style, tests, LFS data, and focused validation.
