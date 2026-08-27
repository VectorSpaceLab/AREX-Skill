# MONAI Bundle Troubleshooting

Use this matrix when `monai.bundle`, `ConfigParser`, `ConfigWorkflow`, or `python -m monai.bundle` behavior fails.

## Failure Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `python -m monai.bundle --help` fails with Fire import errors | Python Fire is optional and not installed. | Install `fire` or the MONAI extra that provides it in the active environment, then rerun help. |
| CLI help works but command-specific help does not show | Fire command help syntax is wrong. | Use `python -m monai.bundle <command> -- --help`, with `-- --help` after the command. |
| `_target_` object cannot be located | Dotted path is wrong, class/function is not importable, or required optional package is absent. | Import the target in Python first, use a fully qualified path, add `$import ...` only for installed packages, and document optional deps. |
| `TypeError` during target instantiation | Config keys do not match the target callable signature. | Compare target signature, remove unknown keys, and check whether positional-style data should be expressed through supported keyword arguments. |
| `KeyError` for a config id | Wrong nested id, missing merged file, shell ate `#`, or `@` reference points to the wrong scope. | Inspect `parser.get()` after loading, use `#`/`::` consistently, quote CLI keys, and prefer args files for complex overrides. |
| Macro `%...` copies unexpected content | `%` performs raw textual subtree replacement before parsing, not runtime object resolution. | Use `%` only for templates/default subtrees; use `@` to reference parsed values or objects. |
| `$` expression is not evaluated or is mangled | Expression not passed as a string starting with `$`, required imports missing, or shell expanded `$`. | Quote/escape `$` in CLI, put imports in config, or move values to an args file. |
| Override has no effect | Override happened after parser content was resolved and cached. | Apply `parser.update()` or assignment before `parse()`/`get_parsed_content()`, or call `parse(reset=True)` / request non-lazy parsing. |
| Multiple config files override lists instead of extending | Later file uses the same key without `+`. | Use `+key` only when both old and new values are lists or both are dicts. |
| `ConfigWorkflow` cannot find metadata or logging config | Defaults are relative to config root: `configs/metadata.json` and `configs/logging.conf`. | Pass explicit `--meta_file`; pass `--logging_file False` if logging config should be skipped. |
| `run ID '<id>' doesn't exist` | The selected `run_id` is missing from config. | Add a `run` expression/list or pass `--run_id <existing_id>`. |
| Metadata validation says `schema` is missing | `metadata.json` lacks a schema URL. | Add a valid `schema` field or skip schema validation until metadata is complete. |
| Metadata validation fails with a long schema error | Required fields or value types do not match the Bundle metadata schema. | Check version fields, package versions, `network_data_format`, input/output keys, dtype strings, and channel definitions. |
| Metadata verification cannot download schema | Network disabled, URL unavailable, or proxy/certificate issue. | Cache schema with `--filepath` when possible, retry with network approval, or record validation as skipped due to network. |
| `verify_net_in_out` creates huge tensors | Metadata uses production 3D shapes or `*`/`n`/`p` defaults produce large shapes. | Use `--device cpu` and override metadata dimensions or `--any`, `--n`, `--p` for tiny fake input. |
| `verify_net_in_out` output channel/dtype mismatch | Metadata `network_data_format.outputs.pred` disagrees with actual network output. | Fix metadata or model config; verify `num_channels`, dtype, and any postprocessing assumptions. |
| `verify_net_in_out` fails before forward pass | Network id missing, target import fails, checkpoint-dependent module not initialized, or optional package missing. | Confirm `net_id`, instantiate with `ConfigParser` directly, and avoid checkpoint/export verification until dependencies are installed. |
| `ckpt_export` cannot find checkpoint | `ckpt_file` default points under `models/model.pt` or provided path is wrong. | Pass explicit `--ckpt_file <checkpoint.pt>` and confirm the file exists. |
| `ckpt_export` cannot find network definition | `net_id` is absent or not instantiable as a `torch.nn.Module`. | Use `network_def` or pass the correct id; test `parser.get_parsed_content(net_id)` first. |
| TorchScript export fails | Model is not scriptable/traceable, input shape missing for trace, or dynamic Python behavior is unsupported. | Try `--use_trace True --input_shape [...]`, simplify forward logic, or document export as unsupported. |
| ONNX export fails | Optional ONNX dependencies missing or model uses unsupported operations/control flow. | Install ONNX stack, provide concrete input shape, and isolate unsupported layers. |
| TensorRT export fails | Missing TensorRT/Torch-TensorRT, unsupported GPU/driver, precision issue, or unsupported input structure. | Verify hardware/software compatibility, try `fp32`, provide explicit input/dynamic batch settings, or skip TRT export. |
| `download_large_files` cannot find manifest | No `large_files.yml`, `large_files.yaml`, or `large_files.json` in bundle path. | Pass `--large_file_name` or create a manifest with a top-level `large_files` list. |
| Downloads fail or hang | Network, proxy, credential, URL, rate-limit, or storage issue. | Ask before retrying, check URL and free space, use hashes, and record skipped network verification when appropriate. |
| `push_to_hf_hub` fails | Missing `huggingface_hub`, invalid token, repo permission issue, or wrong bundle parent/name. | Confirm optional dependency, token, namespace, `--private`, and `--bundle_dir`/`--name` before retrying. |

## Debugging Parser State

Use direct Python inspection before running heavyweight CLI commands:

```python
from monai.bundle import ConfigParser

parser = ConfigParser()
parser.read_config("configs/inference.json")
parser.read_meta("configs/metadata.json")
parser.update({"network_def#in_channels": 1})
print(parser.get())
print(parser.get_parsed_content("network_def", instantiate=False))
```

Escalate from raw content to parsed content:

1. `ConfigParser.load_config_files(...)` to catch JSON/YAML and merge problems.
2. `parser.get("id")` to confirm nested ids and overrides.
3. `parser.get_parsed_content("id", instantiate=False)` to check expression/reference resolution without constructing objects.
4. `parser.get_parsed_content("id")` to instantiate only the target component.
5. `run`, `run_workflow`, or export commands only after the component-level check passes.

## Safe Metadata Debugging

For metadata-only work, avoid network and model execution until needed.

- Check that required keys exist: `version`, `monai_version`, `pytorch_version`, `numpy_version`, `required_packages_version`, `task`, `description`, `authors`, `copyright`, and `network_data_format`.
- Keep `required_packages_version` limited to packages the bundle truly requires beyond base MONAI requirements.
- Ensure `network_data_format.inputs.image` and `network_data_format.outputs.pred` match the actual network used by `verify_net_in_out`.
- Use small synthetic spatial shapes for smoke bundles; production bundles can document larger supported shapes separately.

## CLI Quoting Problems

When CLI overrides behave strangely, assume the shell changed the command.

Safer:

```bash
python -m monai.bundle run --args_file run_args.yaml
```

Riskier:

```bash
python -m monai.bundle run --network_def#in_channels 1 --device $torch.device('cpu')
```

If using direct CLI overrides, quote keys/values that contain `#`, `$`, brackets, braces, commas, spaces, or colons.

## Optional Dependency Boundaries

Base MONAI with PyTorch and NumPy is enough for many parser and CPU model checks. The following capabilities often require extras:

- CLI entry parsing: `fire`.
- Metadata schema validation: `jsonschema` and network access to the schema URL unless cached.
- Medical image IO: packages such as Nibabel, ITK, PIL/Pillow, or related readers depending on transforms.
- Tracking: packages such as MLflow when `tracking="mlflow"` or custom handlers are used.
- ONNX export: ONNX-related packages.
- TensorRT export: TensorRT/Torch-TensorRT stack and compatible NVIDIA hardware.
- Hub publishing: `huggingface_hub` and credentials.

Document optional dependencies in Bundle metadata or README, but do not claim they are installed merely because MONAI imports.

## Recovery Patterns

- If a config is too complex, split it into `defaults.json`, `network.json`, `inference.json`, and a small override file; merge them explicitly.
- If a Bundle run fails inside transforms/data/model code, route to the corresponding MONAI sub-skill after confirming the Bundle parser passed the right object/value.
- If Auto3DSeg generated the Bundle, route generation and algorithm-template questions to `apps-auto3dseg`; use this sub-skill for the generated Bundle files and CLI validation.
- If verification requires network access or credentials, record the exact skipped command and reason instead of silently replacing it with a weaker check.
