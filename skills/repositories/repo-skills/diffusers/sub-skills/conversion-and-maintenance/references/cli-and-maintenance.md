# CLI And Maintenance

Use this reference for `diffusers-cli` behavior and repository maintainer checks. Keep conversion execution separate from command discovery: `--help`, environment reports, and skeleton generation are safe; conversion scripts can import heavy optional dependencies, load weights, download configs, or write large outputs.

## Diffusers CLI Surface

The package registers a console entry point:

```text
diffusers-cli = diffusers.commands.diffusers_cli:main
```

The top-level CLI has subcommands for `env`, `fp16_safetensors`, and `custom_blocks`.

### `diffusers-cli env`

Use `diffusers-cli env` to collect issue-friendly environment information. It reports Diffusers, Python, platform, PyTorch/GPU, Flax/JAX, Hugging Face Hub, Transformers, Accelerate, PEFT, quantization backends, safetensors, xFormers, accelerator information, and placeholders for script GPU/distributed usage.

Safe probe:

```bash
python scripts/diffusers_cli_probe.py env
```

Do not paste machine-specific paths into public runtime docs or generated skills. For issue reports, ask the user to fill in whether the script uses GPU and distributed/parallel setup.

### `diffusers-cli fp16_safetensors`

This command targets a Hub model repository and can create a Hub PR with converted fp16 and/or safetensors weights. It downloads `model_index.json`, imports the pipeline class, loads from Hub, saves to a temporary local directory, then calls Hugging Face Hub commit APIs with `create_pr=True`.

Usage shape:

```bash
diffusers-cli fp16_safetensors --ckpt_id openai/shap-e --fp16 --use_safetensors
```

Rules:

- Use only when Hub access and PR creation are intended.
- `--ckpt_id` is the model repository id.
- `--fp16` saves a `variant="fp16"` pipeline.
- `--use_safetensors` saves safe serialization.
- `--use_auth_token` is deprecated; authentication is handled by logged-in Hub credentials.
- If neither `--fp16` nor `--use_safetensors` is set, the command raises because it has nothing to do.

### `diffusers-cli custom_blocks`

This command packages a modular pipeline custom block from a Python module. It parses class definitions, looks for classes inheriting from `ModularPipelineBlocks`, imports the module dynamically, instantiates the selected class, and calls `save_pretrained` in the current working directory.

Usage shape:

```bash
diffusers-cli custom_blocks --block_module_name block.py --block_class_name MyBlocks
```

Rules:

- Run in a scratch/output directory because it writes `save_pretrained` output to the current directory.
- Do not execute untrusted block modules; the command dynamically imports and runs Python code.
- If `--block_class_name` is omitted, the first discovered `ModularPipelineBlocks` subclass is used.
- Route modular pipeline design questions to the root skill or a modular-pipeline-specific sub-skill if present; this branch only covers CLI packaging behavior.

## Maintainer Edit Rules

Follow repository-local rules for minimal, explicit code changes.

- Prefer small explicit edits over adding defensive fallback paths, legacy stubs, or unused configuration.
- Do not silently correct ambiguous user intent; document expected inputs and raise concise errors for unsupported cases.
- Do not edit a `# Copied from ...` block directly unless intentionally breaking the copy link. Normally edit the source block and run `make fix-copies`.
- Run `make style` before PR handoff when broad formatting is needed.
- Do not add unrelated compatibility aliases or deprecation shims for code that never shipped.

## Copied Code Checks

Many copied sections are tracked by `# Copied from ...` comments. The maintainer workflow is:

1. Identify whether the target block has a `# Copied from ...` header.
2. Edit the source of truth, not each generated copy.
3. Run `make fix-copies` to propagate and regenerate copied blocks and dummy files.
4. Run focused checks around the touched area.

Useful focused checks:

```bash
python -m pytest tests/others/test_check_copies.py
python -m pytest tests/others/test_check_dummies.py
```

`test_check_copies.py` exercises copy consistency and overwrite behavior. `test_check_dummies.py` verifies generated dummy objects and marks generated files as created by `make fix-copies`.

## Optional Dependency And Dummy Object Checks

Diffusers uses lazy imports and dummy objects for optional backends. When adding a new public class, pipeline, backend, or optional dependency:

- Register the backend in the dependency table using the canonical package name expected by the tests.
- Guard optional imports so importing Diffusers works when the dependency is absent.
- Ensure dummy objects call `requires_backends` with the correct backend names.
- Avoid unguarded optional-dependency imports in pipeline modules.

Focused check:

```bash
python -m pytest tests/others/test_dependencies.py
```

This verifies base import, backend registration, pipeline imports, and unguarded optional-dependency import failures.

## Entry-Point Or CLI Changes

When changing CLI commands:

1. Keep subcommand registration explicit in the command class.
2. Add or update parser arguments in the relevant command module.
3. Keep `diffusers-cli` entry point wired to `diffusers.commands.diffusers_cli:main`.
4. Add parser/help checks or focused CLI tests when changing command arguments.
5. Document whether the command is safe to run offline or can download/push.

## Maintainer Verification Planning

When the user is actively working inside a Diffusers checkout, select focused native checks that match the changed surface: copied-code consistency checks for copied blocks, dummy dependency checks for optional imports, dependency table checks for setup changes, and help-only checks for conversion or CLI entrypoints. Keep those as repo-local verification commands, not as requirements for using this standalone skill.

Run conversion entrypoints with help/parser checks before any full conversion. Full conversion requires real weights and may download or consume significant memory.
