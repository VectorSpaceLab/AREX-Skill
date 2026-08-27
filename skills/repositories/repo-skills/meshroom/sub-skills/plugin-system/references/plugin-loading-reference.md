# Plugin Loading Reference

## Environment Variables

| Variable | Loader | Shape |
| --- | --- | --- |
| `MESHROOM_PLUGINS_PATH` | `initPlugins()` | path-separated plugin roots containing `meshroom/` |
| `MESHROOM_USER_PLUGINS_PATH` | `initPlugins()` | user-owned plugin roots with the same shape |
| `MESHROOM_NODES_PATH` | `initNodes()` | path-separated folders containing node packages directly |
| `MESHROOM_PIPELINE_TEMPLATES_PATH` | `initPipelines()` | folders containing `.mg` templates |
| `MESHROOM_SUBMITTERS_PATH` | `initSubmitters()` | folders containing submitter packages |
| `MESHROOM_REZ_PLUGINS` | `initRezPlugins()` | path-separated `package-name=plugin-root` mappings |
| `MESHROOM_USER_REZ_PLUGINS` | `initRezPlugins()` | user-owned Rez mappings |

`meshroom.env.EnvVar.getList()` splits values on the platform path separator and removes empty entries.

## Programmatic APIs

Verified entry points:

```text
loadPluginFolder(folder, userPlugin=False) -> list[Plugin]
loadAllNodes(folder) -> list[Plugin]
loadNodes(folder, packageName, pluginUid) -> list[NodeDescProvider]
loadAllSubmitters(folder) -> list[BaseSubmitter]
loadSubmitters(folder, packageName) -> list[BaseSubmitter]
loadPipelineTemplates(folder)
```

`Plugin(name, path)` stores node providers, `.mg` templates, config env, and a `ProcessEnv`. `PluginManager` tracks loaded plugins by unique name (`uid_name`) and registered node providers by descriptor class name.

## Loading Semantics

- A plugin root without `meshroom/` is ignored.
- A node package should be importable and contain an `__init__.py` for standard package discovery.
- Every `.mg` file directly inside a plugin's `meshroom/` folder is registered as a template by basename.
- Provider validation occurs before registration. Invalid descriptions stay associated with the plugin but are not instantiable.
- Duplicate descriptor class names are rejected to avoid ambiguous graph node types.
- User plugins are marked `isUserPlugin`; their node version type is treated as `USER`.
- A plugin's `configFullEnv` is config defaults merged with `os.environ`; explicit process environment values win.

## Template Visibility Checklist

1. Put the `.mg` file under a loaded plugin `meshroom/` folder or an explicit template folder.
2. Ensure `initPlugins()`/`initPipelines()` are called in the current process.
3. Inspect `meshroom.core.pipelineTemplates` for the basename key.
4. If a template references external node types, load those node providers before opening it.
