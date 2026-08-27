---
name: modular-pipelines
description: "Create, customize, debug, and test Diffusers Modular Pipeline
  blocks, states, component managers, sequential/loop blocks, and custom-block
  CLI packaging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Modular Pipelines

Use this sub-skill for Diffusers Modular Pipeline work: `ModularPipeline`, `ModularPipelineBlocks`, `SequentialPipelineBlocks`, `LoopSequentialPipelineBlocks`, `AutoPipelineBlocks`, `ConditionalPipelineBlocks`, `PipelineState`, `BlockState`, `ComponentsManager`, custom block packaging, and modular pipeline tests.

## Route by task

- Design or edit blocks, state keys, component specs, and workflow maps: read [references/block-workflows.md](references/block-workflows.md).
- Build, package, load, or insert custom blocks: read [references/custom-blocks.md](references/custom-blocks.md) and use `scripts/modular_block_skeleton.py`.
- Diagnose missing components, state mismatches, optional dependency failures, local/offline loading, dtype/device issues, and workflow selection bugs: read [references/troubleshooting.md](references/troubleshooting.md).
- Add or adapt tests for modular families: read [references/testing.md](references/testing.md).
- Check installed modular imports or `diffusers-cli custom_blocks` parser shape: run `python sub-skills/modular-pipelines/scripts/modular_import_check.py`.

## Boundaries

- Stay here for modular definitions, block composition, custom blocks, component sharing/offload, and modular test patterns.
- Route classic `DiffusionPipeline` inference, non-modular pipeline call behavior, and end-user generation examples to `pipelines-and-inference`.
- Route scheduler choice, scheduler configs, and sampling algorithm comparison to `schedulers` unless the scheduler is only being wired as a modular component.

## Quick checklist

- Every block declares all read values as `InputParam` and all written values as `OutputParam` in `intermediate_outputs` or final `outputs`.
- Leaf blocks use `block_state = self.get_block_state(state)`, write declared fields, call `self.set_block_state(state, block_state)`, and return `(components, state)`.
- Loop sub-blocks receive a shared `BlockState`, not a `PipelineState`, and return `(components, block_state)` from each loop iteration.
- Sequential and auto blocks have clear `description` text, ordered `block_classes`/`block_names`, and `_workflow_map` entries for supported public workflows.
- Component work uses `ComponentSpec`, `ConfigSpec`, `load_components`, `update_components`, `get_component_spec`, and `ComponentsManager` rather than ad hoc attributes.
- Custom blocks ship their Python module plus `modular_config.json`; remote custom code loads only with explicit `trust_remote_code=True`.

## Useful scripts

- `scripts/modular_block_skeleton.py` prints or writes a minimal custom block module with valid naming and state-update structure.
- `scripts/modular_import_check.py` verifies core modular imports and confirms `custom_blocks` CLI arguments are registered.
