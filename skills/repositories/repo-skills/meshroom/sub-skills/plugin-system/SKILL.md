---
name: plugin-system
description: "Guides Meshroom plugin, node-folder, template, submitter,
  config.json, user-plugin, Rez-plugin, and process-environment discovery
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom Plugin System

Use this route when Meshroom cannot see a custom node/template/plugin, when plugin configuration or process environments are involved, or when a user asks how to package a Meshroom plugin.

## Read First

- [Plugin loading reference](references/plugin-loading-reference.md)
- [Process environments](references/process-environments.md)
- [Troubleshooting](references/troubleshooting.md)
- Run [scripts/check_plugin_folder.py](scripts/check_plugin_folder.py) before debugging a loaded provider.

## Minimum Plugin Shape

```text
plugin-root/
  meshroom/
    customNodes/
      __init__.py
      MyNode.py
    customTemplate.mg
    config.json                 # optional
  venv/                         # optional plugin runtime
```

Set `MESHROOM_PLUGINS_PATH` to `plugin-root`, not to the nested `meshroom/` folder. Meshroom scans packages below that folder, loads node descriptor providers, registers `.mg` templates, and constructs a process environment.

## Initialization Order

For programmatic inspection, initialize in this order when needed:

```python
import meshroom
meshroom.setupEnvironment()
import meshroom.core
meshroom.core.initPlugins()
meshroom.core.initNodes()
meshroom.core.initPipelines()
meshroom.core.initSubmitters()
```

- `initPlugins()` loads classic/user/Rez plugin roots.
- `initNodes()` loads built-in nodes plus `MESHROOM_NODES_PATH` folders.
- `initPipelines()` registers templates from explicit template paths and loaded plugins.
- `initSubmitters()` loads submitter packages from `MESHROOM_SUBMITTERS_PATH`.

The CLI may choose a different order for its workflow; do not assume a template is visible before its plugin has been loaded.

## Configuration Rules

`config.json` is an array of entries with `key`, `type`, and `value`. `type: "path"` resolves relative paths against the plugin root when the path exists. User environment variables take precedence over config defaults in the merged process environment.

## Route Elsewhere

- Author the node descriptor itself with [node-descriptors](../node-descriptors/SKILL.md).
- Use a discovered template or run it from the CLI with [cli-pipeline-execution](../cli-pipeline-execution/SKILL.md).
- Debug LocalFarm daemon/task behavior with [local-farm-submission](../local-farm-submission/SKILL.md).
