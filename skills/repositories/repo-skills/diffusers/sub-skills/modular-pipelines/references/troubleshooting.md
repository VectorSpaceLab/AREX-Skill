# Modular Pipeline Troubleshooting

## Import and optional dependency failures

Symptoms:

- `OptionalDependencyNotAvailable`, dummy-object errors, or missing `torch`/`transformers` symbols.
- Warnings when loading custom blocks with package requirements.
- `trust_remote_code` errors when loading a custom modular repository.

Checks and fixes:

- Run `python sub-skills/modular-pipelines/scripts/modular_import_check.py` to verify core imports and CLI parser registration.
- Install the backend packages required by the selected model family and custom block. Modular inspection needs PyTorch for core classes.
- For remote or local custom block code, pass `trust_remote_code=True` only after reviewing the code.
- If a custom block declares requirements, satisfy the warning before debugging generation logic.
- Remember that `trust_remote_code=True` on a modular pipeline does not make external component repositories trusted automatically; custom external components may still fail until reviewed and explicitly handled.

## Missing component manager entry or component attribute

Symptoms:

- `AttributeError` for `components.<name>` inside a block.
- `load_components()` skips a component.
- `ComponentsManager` printout lacks the expected model.

Root causes:

- The block did not declare `ComponentSpec(name="...")` matching the attribute used in `__call__`.
- The selected model repository has no loading spec for that component, so the component remains `null`.
- A component was loaded separately but not added with `pipeline.update_components(...)`.
- The wrong workflow was extracted, so the block needing that component is not in the active graph.

Fix sequence:

1. Print `pipe.blocks.doc` or `workflow.doc`; confirm the component appears under Components.
2. Check `pipeline.component_names` and the printed pipeline state to see loaded vs `null` components.
3. If a spec exists, use `pipeline.load_components(names=["component_name"], torch_dtype=...)`.
4. If a spec is missing but a component is intentional, load it from the appropriate model class or `get_component_spec(...)`, then call `pipeline.update_components(component_name=component)`.
5. If the component is optional, split selection with `ConditionalPipelineBlocks` or add a workflow that does not execute the block when the component is absent.

## Block input/output mismatch

Symptoms:

- `AttributeError` on `block_state.some_key`.
- A downstream block receives `None` or a stale value.
- `pipe(...).values` lacks an expected output.
- `doc` does not mention a key the code reads or writes.

Fix sequence:

1. For the failing block, list every `block_state.<name>` read and every assignment.
2. Ensure each read key is in `inputs` and each written key is in `intermediate_outputs` or `outputs`.
3. If mutating an input in place, declare the same key as an output so `set_block_state` writes it back.
4. In sequential workflows, confirm an earlier block writes the key before a later block reads it.
5. For inserted blocks, preserve existing key names unless all downstream blocks are updated.
6. Reprint `blocks.doc` and use a tiny `init_pipeline()` run for pure-Python blocks before trying heavyweight model inference.

## Loop-specific errors

Symptoms:

- Inner denoise block expects `PipelineState` methods or calls `get_block_state`.
- Loop outputs do not persist after the loop finishes.
- Iteration variables are missing from loop sub-blocks.

Fixes:

- The loop wrapper receives `(components, state)`, calls `self.get_block_state(state)`, repeatedly calls `self.loop_step(...)`, then calls `self.set_block_state(state, block_state)` once after the loop.
- Inner loop blocks receive `(components, block_state, i=...)` or other explicit loop arguments and return `(components, block_state)`.
- Declare loop-level user inputs in `loop_inputs` and loop-produced fields in `loop_intermediate_outputs` when they belong to the wrapper.
- Declare per-step read/write keys in each loop sub-block's `inputs` and `intermediate_outputs`.

## Workflow selection surprises

Symptoms:

- The text-to-image path runs when image-to-image was expected.
- A nested conditional block is skipped.
- `get_workflow("name")` fails or returns a graph missing a block.

Fixes:

- For `AutoPipelineBlocks`, make `block_trigger_inputs` the same length and order as `block_names` and `block_classes`.
- Put high-priority triggers first when more than one trigger may be present, such as `mask_image` before `image`.
- Use `None` for the default trigger in `AutoPipelineBlocks`; use `default_block_name` only with `ConditionalPipelineBlocks`.
- For custom selection logic, ensure `select_block` parameters exactly match names in `block_trigger_inputs`.
- Add or update `_workflow_map` on the containing sequential class, then verify `available_workflows` and `get_workflow("...")`.
- Use `get_execution_blocks(**trigger_inputs)` to inspect the actual selected graph.

## Device, dtype, and backend mistakes

Symptoms:

- CPU/GPU tensor mismatch, dtype mismatch, unsupported `bfloat16`, or OOM.
- `ComponentsManager` shows models on unexpected devices.
- Generation works without offload but fails with auto offload.

Fixes:

- Call `load_components(torch_dtype=...)` before `to(...)` when loading pretrained components.
- Use a per-component dtype dict when only selected models support `bfloat16` or `float16`.
- Use `ComponentsManager.enable_auto_cpu_offload(device="cuda")` only when `accelerate` and the target backend are available.
- If not using manager offload, move the pipeline with `pipeline.to("cuda")` or the intended device after loading.
- Keep newly created tensors on the device and dtype of existing state tensors, for example derive from `block_state.latents.device` and `block_state.latents.dtype`.

## Local/offline file problems

Symptoms:

- `modular_config.json` or `modular_model_index.json` not found.
- Custom block loads locally but fails after copying or upload.
- `local_files_only=True` fails even though the config exists.

Fixes:

- For custom blocks, keep the Python file named in `auto_map` next to `modular_config.json`.
- For modular pipelines, include `modular_model_index.json` and any custom code files needed by `_blocks_class_name`.
- Offline loading needs all referenced component weights already local or cached; lazy `from_pretrained` success does not prove `load_components` will succeed.
- Avoid local absolute paths in serialized specs when preparing reusable blocks or skills.

## API misuse quick map

- Need to run a block alone: `block.init_pipeline()`.
- Need to run a block with repository component specs: `block.init_pipeline(repo_id_or_path)`.
- Need to load a saved modular pipeline: `ModularPipeline.from_pretrained(repo_id_or_path, trust_remote_code=...)`.
- Need only one workflow from a multi-workflow pipeline: `pipe.blocks.get_workflow("workflow_name")`.
- Need actual conditional execution graph for inputs: `blocks.get_execution_blocks(**inputs)`.
- Need to replace a component: `pipeline.update_components(name=component)`.
- Need to load missing weights: `pipeline.load_components(names=["name"], torch_dtype=...)`.
