---
name: bundle-config
description: "Work with MONAI Bundle configuration syntax, metadata/spec files,
  ConfigParser, ConfigWorkflow, Bundle CLI commands, verification, export, and
  package-style bundle workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI Bundle Config

Use this sub-skill when the task involves `monai.bundle`, `python -m monai.bundle`, Bundle JSON/YAML config syntax, metadata/spec files, `ConfigParser`, `BundleWorkflow`, `ConfigWorkflow`, CLI overrides, verification, export, or reproducible package-style bundle workflows.

Do not use this sub-skill for Auto3DSeg orchestration that generates bundles; route those tasks to `apps-auto3dseg`. For Bundle component internals, route model definitions to the model sub-skill, transforms and datasets to the data/transforms sub-skills, and training loop objects to the training sub-skill.

## Fast Routing

- Read `references/config-syntax.md` when authoring, merging, overriding, or debugging Bundle JSON/YAML with `_target_`, `@`, `%`, `$`, nested ids, and `ConfigParser`.
- Read `references/cli-reference.md` when invoking `python -m monai.bundle`, selecting commands, preparing CLI overrides, validating metadata/network I/O, exporting checkpoints, downloading large files, or pushing bundles.
- Read `references/troubleshooting.md` when Bundle parsing, CLI startup, verification, export, path, optional dependency, or network/download behavior fails.
- Run `scripts/monai_bundle_smoke.py --help` when checking what the bundled smoke script can do without touching external data or repository source files.
- Run `scripts/monai_bundle_smoke.py parse-inline` when confirming the installed MONAI Bundle parser can instantiate a tiny object graph and apply an override.
- Run `scripts/monai_bundle_smoke.py build-tiny-bundle --output <dir>` when a temporary self-contained Bundle directory is useful for experimentation.
- Use `templates/tiny-bundle/` as a copyable minimal Bundle skeleton when a user asks for example bundle files rather than a generated temporary directory.

## Common Workflows

1. For config authoring, start with `references/config-syntax.md`, keep top-level ids meaningful, use `_target_` for instantiable Python objects, and prefer simple `@` references over complex `$` expressions.
2. For Bundle CLI work, ensure Python Fire is installed, run command help as `python -m monai.bundle <command> -- --help`, and quote shell-sensitive ids such as `network_def#spatial_dims`.
3. For verification, use `verify_metadata` for schema-backed metadata and `verify_net_in_out` only when the config network can run safely on the requested device with fake tensor input.
4. For export, require an existing checkpoint, config file, and compatible optional export dependencies before using `ckpt_export`, `onnx_export`, or `trt_export`.
5. For reproducible workflows, prefer `run_workflow`/`create_workflow` with explicit `config_file`, `meta_file`, `workflow_type`, and overrides instead of relying on current working directory defaults.

## Safety Defaults

- Treat download, Hub push, and large-file commands as network/credential operations; ask before running them unless the user explicitly requested network publishing or downloads.
- Do not claim optional IO/export/tracking/HPO dependencies are installed unless the current environment proves it.
- Avoid absolute local paths in reusable instructions; use placeholders such as `<bundle_dir>`, `<config_file>`, and `<checkpoint.pt>`.
- Keep generated Bundle examples small, CPU-safe, and based on installed `monai`, `torch`, and `numpy` APIs.
