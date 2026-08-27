# Custom Blocks

## Expected project shape

A reusable custom modular block repository or folder should include:

```text
.
├── block.py
└── modular_config.json
```

`block.py` contains a `ModularPipelineBlocks` subclass. `modular_config.json` is produced by `save_pretrained(...)` and contains the `auto_map` metadata that lets Diffusers reload the class.

## Fast local skeleton

Use the bundled helper to create a minimal block module:

```bash
python sub-skills/modular-pipelines/scripts/modular_block_skeleton.py --class-name CannyBeforeDenoiseBlock --output block.py
```

Then edit `inputs`, `intermediate_outputs`, and `__call__` before packaging.

## Minimal implementation contract

```python
from diffusers.modular_pipelines import InputParam, ModularPipelineBlocks, OutputParam

class PromptPrefixBlock(ModularPipelineBlocks):
    @property
    def description(self):
        return "Add a fixed prefix to the prompt."

    @property
    def inputs(self):
        return [InputParam("prompt", type_hint=str, required=True)]

    @property
    def intermediate_outputs(self):
        return [OutputParam("prompt", type_hint=str)]

    def __call__(self, components, state):
        block_state = self.get_block_state(state)
        block_state.prompt = "cinematic " + block_state.prompt
        self.set_block_state(state, block_state)
        return components, state
```

Package and reload locally:

```python
block = PromptPrefixBlock()
block.save_pretrained("prompt-prefix-block")
# Ensure the Python file named in modular_config.json is also present in that folder.
from diffusers.modular_pipelines import ModularPipelineBlocks
loaded = ModularPipelineBlocks.from_pretrained("prompt-prefix-block", trust_remote_code=True)
pipe = loaded.init_pipeline()
output = pipe(prompt="cat")
```

Important details from Diffusers tests:

- `save_pretrained(...)` writes `modular_config.json` with `auto_map`, but the Python module implementing the class must also be present in the saved directory or Hub repo.
- Loading custom Python code requires `trust_remote_code=True` for remote or local custom-code directories.
- The `diffusers-cli custom_blocks` command can infer the first `ModularPipelineBlocks` subclass from a module, instantiate it, and call `save_pretrained(os.getcwd())`.
- If multiple block classes exist in one module, pass `--block_class_name` to avoid packaging the wrong one.

## CLI packaging

Run from the directory where `modular_config.json` should be created:

```bash
diffusers-cli custom_blocks --block_module_name block.py --block_class_name PromptPrefixBlock
```

Parser facts:

- `--block_module_name` defaults to `block.py`.
- `--block_class_name` defaults to inference from the first top-level class that directly subclasses `ModularPipelineBlocks`.
- The command parses class bases with Python AST, imports the module dynamically, instantiates the selected class with no arguments, and calls `save_pretrained(...)` in the current directory.

Avoid:

- Required constructor arguments in a block intended for CLI packaging.
- Multiple candidate block classes without `--block_class_name`.
- Relative imports that only work from the source checkout.
- Hidden runtime dependencies that are not declared in the block requirements metadata.

## Declaring requirements

Custom blocks may need packages outside Diffusers. Declare them so loading can warn early when dependencies are missing or incompatible. Use standard package specifier strings such as `opencv-python>=4.8` or `transformers>=4.45` in the block's requirements metadata when the project pattern supports it. Treat warnings from Diffusers requirement validation as actionable; do not defer them to runtime model execution.

## Composing with built-in workflows

Typical edit flow for inserting a custom block into an existing modular workflow:

```python
from diffusers import ModularPipeline
from diffusers.modular_pipelines import ModularPipelineBlocks

pipe = ModularPipeline.from_pretrained("model-or-local-modular-repo", trust_remote_code=True)
blocks = pipe.blocks.get_workflow("controlnet_text2image")
custom = ModularPipelineBlocks.from_pretrained("custom-block-folder", trust_remote_code=True)
blocks.sub_blocks.insert("custom_preprocess", custom, 0)
new_pipe = blocks.init_pipeline("model-or-local-modular-repo")
new_pipe.load_components()
```

When adding a before-denoise block:

- Preserve existing state keys unless intentionally changing the downstream contract.
- If the block modifies `latents`, `image_latents`, `prompt_embeds`, or conditioning tensors, declare the same key as an output.
- If the block creates a new conditioning key, update the downstream denoise block inputs or insert a bridge block that maps the new key to the expected key.
- Confirm with `print(blocks.doc)` and `blocks.get_execution_blocks(**trigger_inputs)` before running expensive inference.

## Local and offline loading

- Use local directories with `ModularPipelineBlocks.from_pretrained(local_dir, trust_remote_code=True)` for custom code already downloaded.
- Use `local_files_only=True` when a task must not hit the network, but expect failures if `modular_config.json`, the Python module, or referenced component weights are absent from cache.
- For modular repositories without weights, `init_pipeline(repo_id)` or `ModularPipeline.from_pretrained(repo_id)` only reads loading specs; `load_components(...)` is the step that needs actual component files.

## Security posture

`trust_remote_code=True` executes Python from the target repository or folder. Use it only for a reviewed local folder or a trusted Hub repo. For untrusted blocks, inspect the module first and prefer running in an isolated environment before loading.
