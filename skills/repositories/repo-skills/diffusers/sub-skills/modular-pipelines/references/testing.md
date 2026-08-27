# Testing Modular Pipelines

## Fast validation levels

1. Pure block tests: instantiate a small custom block, call `init_pipeline()`, run with toy inputs, and assert `output.values` includes expected input and output keys.
2. Workflow graph tests: call `blocks.available_workflows`, `blocks.get_workflow(name)`, and compare the selected `sub_blocks` names with the intended graph.
3. Component loading tests: call `init_pipeline(tiny_repo_or_local_dir)`, `load_components(...)`, and assert required component names are loaded.
4. Inference tests: run tiny models through a full modular pipeline and assert output shape, batching behavior, dtype behavior, or numerical tolerances.

## Native test patterns

Diffusers modular tests commonly use a `ModularPipelineTesterMixin` that checks:

- Pipeline `__call__` signature against expected required and optional parameters.
- Batched inference consistency and single-vs-batch equivalence.
- Float16 or accelerator behavior when the backend supports it.
- Device movement with `pipe.to(device)`.
- Workflow extraction through an `expected_workflow_blocks` mapping.
- Save/load roundtrips with `ModularPipeline.from_pretrained(tmp_path)`.

When adding a new modular family, define:

- `pipeline_class`: the modular pipeline class.
- `pipeline_blocks_class`: the corresponding blocks class.
- `pretrained_model_name_or_path`: a tiny or test model repo.
- `params` and `batch_params`: expected call inputs.
- `expected_workflow_blocks`: mapping of workflow name to block-name list.
- `get_dummy_inputs(...)`: deterministic toy inputs.

## Custom block tests

Minimal assertions for a custom block:

```python
block = MyCustomBlock()
pipe = block.init_pipeline()
out = pipe(prompt="Diffusers is nice")
assert "prompt" in out.values
assert "my_output" in out.values
```

Save/load assertions:

- `block.save_pretrained(tmp_path)` writes `modular_config.json`.
- The Python module referenced by `auto_map` exists next to `modular_config.json`.
- `ModularPipelineBlocks.from_pretrained(tmp_path, trust_remote_code=True)` reloads the block.
- The reloaded block's `inputs`, `intermediate_outputs`, and behavior match the original.

## Workflow tests

For a multi-workflow block class:

```python
blocks = MyAutoBlocks()
assert "text2image" in blocks.available_workflows
workflow = blocks.get_workflow("text2image")
assert list(workflow.sub_blocks) == ["text_encoder", "denoise", "decode"]
selected = blocks.get_execution_blocks(prompt="cat", image=None)
print(selected)
```

Use workflow tests when editing `AutoPipelineBlocks`, `ConditionalPipelineBlocks`, `_workflow_map`, trigger names, or before-denoise insertion points.

## Synthetic cases worth verifying

- Insert a custom before-denoise block into a selected workflow, mutate `latents` while preserving the `latents` key, and assert the downstream denoise block still receives the expected state.
- Build a failing mini-pipeline with one missing `ComponentSpec` and one output/input name mismatch, then require the agent to diagnose both from `doc`, printed pipeline state, and `ComponentsManager` output.

## Native-style candidates

Prefer native-style tests that exercise pure custom block behavior, save/load roundtrips, `from_blocks_dict`, conditional routing, loop blocks, workflow extraction, and family-specific tiny inference. Run targeted custom/conditional tests first, then broader family tests only when required dependencies and tiny model assets are available. Avoid heavyweight model downloads or accelerator-only tests unless the task specifically requires them.
