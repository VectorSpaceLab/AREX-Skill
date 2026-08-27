# Plugin System Troubleshooting

- **Plugin ignored:** verify the configured value points to the plugin root and that `plugin-root/meshroom/` exists. The loader logs an informational message when this folder is missing.
- **Nodes not registered:** ensure node package imports, `__init__.py` exists, descriptor class inherits `desc.BaseNode`, and defaults pass validation. Run `scripts/check_plugin_folder.py` and then the descriptor validator for the failing module.
- **Duplicate node warning:** two providers expose the same class name. Rename the descriptor or reduce overlapping `MESHROOM_*_PATH` entries.
- **Template missing:** call plugin/template initialization in the correct process, confirm the `.mg` is directly under a loaded template folder/plugin root, and inspect `meshroom.core.pipelineTemplates`.
- **Config path remains relative/unresolved:** `type: "path"` resolves only when the referenced path exists. Fix the path or create the required file; do not assume a missing path is silently valid.
- **OS env value is ignored:** config values are defaults; an existing environment variable intentionally wins. Remove/adjust the parent environment if the plugin default should take effect.
- **Rez command fails:** verify `rez`/`REZ_BIN`, package URI mappings, `REZ_REQUEST`/`REZ_USED_REQUEST`, and plugin subrequires. If Rez is optional, switch the plugin to a directory-tree process environment instead of hiding a missing dependency.
- **Plugin reload leaves stale nodes:** unregister providers or reload the graph's node descriptors after editing. Existing graph instances do not automatically adopt every descriptor change.
