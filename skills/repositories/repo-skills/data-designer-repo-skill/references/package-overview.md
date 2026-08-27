# Package Overview

## Purpose

Read this file when you need the DataDesigner package map, verified entry points, or a quick reminder of which sub-skill owns which workflow.

## Verified package layering

DataDesigner is a three-package workspace that merges at runtime through the shared data_designer namespace:

| Package | Source root | Public surface |
| --- | --- | --- |
| data-designer-config | packages/data-designer-config/src/data_designer/config/ | Declarative config objects, builder API, seed sources, processors, validators, plugins |
| data-designer-engine | packages/data-designer-engine/src/data_designer/engine/ | Compilation, generation engine, async scheduler, models, MCP, sampling, storage, validation |
| data-designer | packages/data-designer/src/data_designer/ | Public DataDesigner class, CLI, integrations, workflow chaining, results |

Dependency direction is interface -> engine -> config.

## Public entry points verified from the installed package

- Console script: data-designer -> data_designer.cli.main:main
- Primary Python API: data_designer.interface.DataDesigner
- Config builder: data_designer.config.DataDesignerConfigBuilder
- Agent CLI group: data-designer agent context/types/state

## Runtime facts worth remembering

- The CLI is Typer-based and loads commands lazily.
- The agent context output reports config types, source files, persona dataset state, and model alias usability.
- In a clean environment with no user-provided provider configuration, there may be no usable model aliases yet. That is a model-configuration state, not a package-install failure.
- The live package version used for this generation run is 0.9.1.

## Workflow map

| User task | Primary sub-skill |
| --- | --- |
| Design a dataset schema | config-authoring |
| Run preview/create/validate/check-models | generation-runtime |
| Use CLI/config/persona/plugin commands | cli-and-agent-tools |
| Install or inspect plugins/custom columns/MCP tools | plugins-and-extensions |
| Adapt notebooks or recipes | recipes-and-integrations |

## When to read the other references

- Read api-reference pages inside the relevant sub-skill when you need concrete parameter names or return values.
- Read troubleshooting when commands fail, assets are missing, or provider/API/assistant paths are unavailable.
- Read repo-provenance when you need to decide whether this skill still matches the current checkout.
