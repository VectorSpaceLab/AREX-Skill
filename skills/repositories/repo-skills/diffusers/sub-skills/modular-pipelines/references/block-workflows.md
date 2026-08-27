# Block Workflows

## Core model

- `ModularPipelineBlocks` is a blueprint. Convert it to an executable `ModularPipeline` with `blocks.init_pipeline(...)` or load a saved modular repository with `ModularPipeline.from_pretrained(...)`.
- `ModularPipeline.from_pretrained(...)` is lazy: it reads `modular_model_index.json` or compatible config but does not load model weights until `pipeline.load_components(...)`.
- A block reads user inputs and upstream intermediates through a local `BlockState` and writes back to global `PipelineState.values` with `set_block_state`.
- `pipe.blocks.doc` and `sub_block.doc` are the fastest interface inspection tools because they summarize `description`, components, inputs, configs, and outputs.

## Leaf block pattern

```python
from diffusers.modular_pipelines import InputParam, ModularPipelineBlocks, OutputParam

class BeforeDenoiseHook(ModularPipelineBlocks):
    @property
    def description(self):
        return "Prepare extra conditioning before the denoising loop."

    @property
    def inputs(self):
        return [InputParam("latents", type_hint="torch.Tensor", required=True)]

    @property
    def intermediate_outputs(self):
        return [OutputParam("latents", type_hint="torch.Tensor")]

    def __call__(self, components, state):
        block_state = self.get_block_state(state)
        block_state.latents = block_state.latents
        self.set_block_state(state, block_state)
        return components, state
```

Rules:

- Import modular classes from `diffusers.modular_pipelines` unless a repo file already uses public `diffusers` re-exports.
- Add `ComponentSpec(name="vae", type_hint=AutoencoderKL, ...)` for components the block accesses through `components.vae`.
- Add `ConfigSpec("name", default)` for pipeline-level configuration values that should be serialized and visible in docs.
- A block can mutate an input such as `image`; the mutation is global only after `set_block_state`.
- Do not write undeclared state fields. Undeclared fields are hard to discover and are frequent sources of downstream block failures.

## Sequential blocks

Use `SequentialPipelineBlocks` for linear execution where each sub-block's outputs become available to later sub-blocks.

```python
from diffusers.modular_pipelines import SequentialPipelineBlocks

class MyPipelineBlocks(SequentialPipelineBlocks):
    model_name = "my-model"
    block_classes = [TextEncodeBlock(), BeforeDenoiseHook(), DenoiseBlock(), DecodeBlock()]
    block_names = ["text_encoder", "before_denoise", "denoise", "decode"]

    @property
    def description(self):
        return "Text-to-image workflow with a custom before-denoise hook."
```

Review points:

- `block_classes`, `block_names`, and execution order must match exactly.
- `inputs`, `intermediate_outputs`, `expected_components`, and configs aggregate from sub-blocks; override `outputs` only when final docs should hide internal intermediates.
- `sub_blocks` is an insertable ordered mapping. To insert a block before denoise: `blocks.sub_blocks.insert("my_hook", hook_block, index)`.
- Use `print(blocks)` for the tree and `print(blocks.doc)` for the public input/output contract.

## Auto and conditional workflows

Use `AutoPipelineBlocks` for trigger-input based workflow routing. Use `ConditionalPipelineBlocks` when selection logic needs custom priority or optional skipping.

```python
from diffusers.modular_pipelines import AutoPipelineBlocks

class AutoImageBlocks(AutoPipelineBlocks):
    block_classes = [InpaintBlocks, ImageToImageBlocks, TextToImageBlocks]
    block_names = ["inpainting", "image2image", "text2image"]
    block_trigger_inputs = ["mask_image", "image", None]

    @property
    def description(self):
        return "Runs inpainting when mask_image is present, image2image when image is present, otherwise text2image."
```

Rules:

- `AutoPipelineBlocks` requires equal-length `block_classes`, `block_names`, and `block_trigger_inputs`.
- Put `None` in `block_trigger_inputs` for the default block; do not also set `default_block_name` on `AutoPipelineBlocks`.
- `ConditionalPipelineBlocks.select_block(...)` receives only names listed in `block_trigger_inputs`; return `None` to use `default_block_name`, or to skip when no default exists.
- Define `_workflow_map` on a containing sequential block so agents and tests can use `available_workflows` and `get_workflow("name")`.
- Debug nested conditionals with `get_execution_blocks(**inputs)` to see the actual execution graph selected by a set of trigger inputs.

## Loop blocks

Use `LoopSequentialPipelineBlocks` for iterative denoising or repeated transforms.

```python
from diffusers.modular_pipelines import InputParam, LoopSequentialPipelineBlocks, ModularPipelineBlocks, OutputParam

class DenoiseLoop(LoopSequentialPipelineBlocks):
    model_name = "my-model"

    @property
    def loop_inputs(self):
        return [InputParam("num_inference_steps", type_hint=int)]

    def __call__(self, components, state):
        block_state = self.get_block_state(state)
        for step_index in range(block_state.num_inference_steps):
            components, block_state = self.loop_step(components, block_state, i=step_index)
        self.set_block_state(state, block_state)
        return components, state

class OneDenoiseStep(ModularPipelineBlocks):
    @property
    def inputs(self):
        return [InputParam("latents")]

    @property
    def intermediate_outputs(self):
        return [OutputParam("latents")]

    def __call__(self, components, block_state, i: int):
        block_state.latents = block_state.latents
        return components, block_state
```

Loop rules:

- The wrapper handles `PipelineState` conversion and calls `loop_step`.
- Inner loop blocks operate directly on the shared `BlockState`; do not call `get_block_state` or `set_block_state` inside loop sub-blocks.
- Build a loop with `LoopWrapper.from_blocks_dict({"predict_noise": PredictNoiseBlock(), "scheduler_step": SchedulerStepBlock()})`.
- Keep iteration arguments explicit, usually `i` or timestep-like values, so test failures are easy to trace.

## Components and loading

- `ComponentsManager` registers loaded components, prints dtype/device/load IDs, and can share components across multiple modular pipelines.
- Use `manager.enable_auto_cpu_offload(device="cuda")` before loading if memory pressure is expected and `accelerate` is installed.
- Use `pipeline.load_components(torch_dtype=...)` to load all components with valid specs, or `pipeline.load_components(names=["text_encoder"], torch_dtype=...)` for a subset.
- `torch_dtype` and other load kwargs can be per-component dicts: `torch_dtype={"transformer": torch.bfloat16, "default": torch.float32}`.
- `pipeline.update_components(name=component)` replaces an already-loaded component and updates the serialized loading spec.
- `pipeline.get_component_spec("name")` returns a copy of the component spec; use `spec.load(...)` for pretrained-weight components and `spec.create(...)` for config-created components such as guiders or schedulers.

## Inserting a before-denoise block safely

1. Get the workflow that owns denoising, for example `blocks = pipe.blocks.get_workflow("text2image")` or `pipe.blocks.get_workflow("controlnet_text2image")`.
2. Print `blocks` and `blocks.doc`; locate the denoise block index and the state keys it expects.
3. Define the inserted block with `inputs` matching existing upstream keys and `intermediate_outputs` matching any keys it writes.
4. If preserving a key such as `latents`, declare it as both an input and output when mutating it.
5. Insert with `blocks.sub_blocks.insert("before_denoise_hook", hook, denoise_index)`.
6. Run `blocks.get_execution_blocks(**minimal_trigger_inputs)` and `blocks.init_pipeline(...).load_components(...)` only after the state contract is consistent.
