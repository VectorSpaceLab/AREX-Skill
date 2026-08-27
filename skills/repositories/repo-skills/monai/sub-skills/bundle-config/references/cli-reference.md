# MONAI Bundle CLI Reference

The Bundle CLI is exposed through Python Fire:

```bash
python -m monai.bundle --help
python -m monai.bundle <command> -- --help
```

If the CLI cannot start, install the optional Fire dependency in the active environment. Do not assume export, tracking, IO, Hugging Face, TensorRT, or ONNX dependencies are installed unless the environment proves it.

## Command Catalog

| Command | Primary use | Important inputs | Safety / optional dependency notes |
| --- | --- | --- | --- |
| `run` | Run a config-based Bundle workflow with initialize/run/finalize stages. | `--config_file`, `--meta_file`, `--workflow_type`, `--init_id`, `--run_id`, `--final_id`, overrides. | Can train/infer and write outputs depending on config expressions. Inspect config first. |
| `run_workflow` | Create a `BundleWorkflow` subclass, run it, then finalize it. | `--workflow_name`, `--config_file`, `--meta_file`, `--args_file`, workflow kwargs. | Default workflow is `ConfigWorkflow`; custom dotted workflow classes must be importable. |
| `verify_metadata` | Validate metadata against the schema URL declared in `metadata.json`. | `--meta_file`, optional schema `--filepath`, hash args. | Downloads schema from `metadata.schema`; network may fail or require approval. |
| `verify_net_in_out` | Instantiate a configured network and test fake input/output shape and dtype against metadata. | `net_id`, `--meta_file`, `--config_file`, `--device`, `--p`, `--n`, `--any`, `--extra_forward_args`, overrides. | Runs model forward pass. Prefer `--device cpu` for safe smoke checks; metadata shape expressions can create large tensors. |
| `ckpt_export` | Export checkpoint/config/metadata to TorchScript with bundled extra JSON. | `net_id`, `--filepath`, `--ckpt_file`, `--config_file`, `--meta_file`, `--key_in_ckpt`, `--use_trace`, `--input_shape`. | Requires a real checkpoint and a scriptable/traceable network. Tracing needs representative input shape. |
| `onnx_export` | Export checkpoint/config network to ONNX. | Same core inputs as `ckpt_export`; `--converter_kwargs` for ONNX options. | Requires optional ONNX stack. Some Python structures and dynamic behavior may not export. |
| `trt_export` | Export to TensorRT engine-based TorchScript. | `--precision`, `--input_shape`, `--dynamic_batchsize`, `--device`, `--use_onnx`, ONNX names. | Requires GPU-compatible TensorRT/Torch-TensorRT stack. Check hardware and versions first. |
| `init_bundle` | Create a new Bundle directory skeleton. | `bundle_dir`, optional `ckpt_file`, `network`, `dataset_license`, `metadata_str`, `inference_str`. | Target directory must not already exist; parent must exist. Review generated placeholder metadata before publishing. |
| `download` | Download a model-zoo/hosting/Hugging Face bundle for loading or local use. | Bundle name/version/source/repo/device/model file args. | Network operation; may hit rate limits, credentials, or storage limits. |
| `download_large_files` | Download large files declared by `large_files.yml`, `large_files.yaml`, or `large_files.json` in a bundle. | `--bundle_path`, `--large_file_name`. | Network operation. Verifies hashes only if provided. |
| `push_to_hf_hub` | Upload a Bundle to Hugging Face Hub. | `--repo`, `--name`, `--bundle_dir`, `--token`, `--private`, `--version`. | Credentialed publishing operation; confirm repo, privacy, and token handling before running. |

The help catalog may also expose utility commands such as bundle info/version listing depending on the installed MONAI version. Treat commands that query remote registries as network operations.

## `run` And `run_workflow`

Use these when a Bundle config has executable `initialize`, `run`, and optional `finalize` ids.

```bash
python -m monai.bundle run \
  --config_file <bundle_dir>/configs/inference.json \
  --meta_file <bundle_dir>/configs/metadata.json \
  --workflow_type infer \
  --run_id run
```

```bash
python -m monai.bundle run_workflow \
  --config_file <bundle_dir>/configs/train.json \
  --meta_file <bundle_dir>/configs/metadata.json \
  --workflow_name ConfigWorkflow \
  --workflow_type train
```

Workflow notes:

- `create_workflow()` defaults to `ConfigWorkflow`, calls `initialize()`, and returns the workflow object.
- `run_workflow()` creates the workflow, calls `run()`, then calls `finalize()`.
- `ConfigWorkflow.run()` temporarily adds the bundle root to `sys.path`, so local bundle modules can be importable when packaged correctly.
- If `run_id` is missing, `ConfigWorkflow.run()` raises an error; `initialize` and `finalize` ids may be absent.
- Set `logging_file=False` when a missing or undesired logging config should not alter logging.

## Metadata Verification

`verify_metadata` loads one or more metadata files, reads the `schema` URL, downloads the schema, and validates with `jsonschema`.

```bash
python -m monai.bundle verify_metadata \
  --meta_file <bundle_dir>/configs/metadata.json \
  --filepath <schema-cache.json>
```

Use this when checking bundle publication readiness. It does not prove that the configured network runs; combine it with `verify_net_in_out` for I/O checks.

## Network I/O Verification

`verify_net_in_out` loads config and metadata, applies overrides, instantiates `net_id`, creates fake input from `_meta_#network_data_format`, runs a forward pass, and compares output channels and dtype.

```bash
python -m monai.bundle verify_net_in_out network_def \
  --config_file <bundle_dir>/configs/inference.json \
  --meta_file <bundle_dir>/configs/metadata.json \
  --device cpu \
  --any 8
```

Shape expression controls:

- `--p` supplies the exponent factor for expressions such as `2**p`.
- `--n` supplies the multiplier for expressions such as `16*n`.
- `--any` supplies the concrete size for `"*"` dimensions.

Avoid using this command blindly on large 3D metadata shapes or GPU-only networks. Override metadata dimensions to tiny CPU-safe values when the goal is smoke testing syntax rather than validating production throughput.

## Export Commands

### `ckpt_export`

```bash
python -m monai.bundle ckpt_export network_def \
  --filepath <bundle_dir>/models/model.ts \
  --ckpt_file <bundle_dir>/models/model.pt \
  --config_file <bundle_dir>/configs/inference.json \
  --meta_file <bundle_dir>/configs/metadata.json \
  --input_shape '[1,1,16,16]'
```

- Defaults `net_id` to `network_def` when omitted.
- Defaults `filepath`, `ckpt_file`, and `meta_file` under a `bundle_root` when not specified.
- Raises if checkpoint file is missing or network id cannot be parsed.
- Stores config content as JSON extra files in the TorchScript artifact.

### `onnx_export`

Use for ONNX deliverables when optional ONNX dependencies and model compatibility are confirmed.

```bash
python -m monai.bundle onnx_export network_def \
  --filepath <bundle_dir>/models/model.onnx \
  --ckpt_file <bundle_dir>/models/model.pt \
  --config_file <bundle_dir>/configs/inference.json \
  --meta_file <bundle_dir>/configs/metadata.json \
  --input_shape '[1,1,16,16]'
```

### `trt_export`

Use only in a TensorRT-capable environment.

```bash
python -m monai.bundle trt_export \
  --net_id network_def \
  --filepath <bundle_dir>/models/model_trt.ts \
  --ckpt_file <bundle_dir>/models/model.pt \
  --config_file <bundle_dir>/configs/inference.json \
  --input_shape '[1,1,16,16]' \
  --precision fp32
```

TensorRT export can use Torch-TensorRT or an ONNX-to-TensorRT path. Confirm supported GPU architecture, TensorRT version, precision, dynamic batch settings, and model input structure before running.

## `init_bundle`

`init_bundle` creates a directory skeleton with `configs/metadata.json`, `configs/inference.json`, `models/`, `docs/README.md`, and `LICENSE`.

```bash
python -m monai.bundle init_bundle <new_bundle_dir>
```

Cautions:

- The target directory must not exist.
- The parent directory must exist.
- Generated metadata and README are placeholders; edit them before validation or publication.
- Passing `--dataset_license True` adds `docs/data_license.txt`.

## Downloads And Hub Publishing

Use explicit user approval for these in agent workflows.

```bash
python -m monai.bundle download_large_files --bundle_path <bundle_dir>
python -m monai.bundle push_to_hf_hub --repo <namespace/name> --name <bundle_name> --bundle_dir <parent_dir> --private True
```

Download guidance:

- `download_large_files` searches for supported `large_files*` config files if `--large_file_name` is absent.
- Each large-file entry should include a URL, destination path, and ideally hash information.
- Registry downloads may require `requests`, Hub packages, credentials, or network access.

Publishing guidance:

- `push_to_hf_hub` uses Hugging Face APIs and token discovery if `--token` is not supplied.
- It may create a repo, upload the bundle folder, and create version/latest tags.
- Confirm privacy, namespace, bundle name, model card content, and license before invoking.

## Args Files

Most commands accept `--args_file <json-or-yaml>`. Use args files to avoid fragile shell quoting and to preserve reproducible runs.

```yaml
config_file: <bundle_dir>/configs/inference.json
meta_file: <bundle_dir>/configs/metadata.json
workflow_type: infer
network_def#in_channels: 1
```

Then run:

```bash
python -m monai.bundle run --args_file run_args.yaml
```

## Quoting Rules

- Put `-- --help` after the command name for Fire command help.
- Quote override keys with `#` if the shell treats `#` as a comment marker in your context.
- Escape or single-quote values beginning with `$`, such as `'\$torch.device("cpu")'`.
- Prefer JSON/YAML args files for lists and dicts, such as `input_shape`, `dynamic_batchsize`, or `extra_forward_args`.

## Safe Command Selection

- Need to inspect syntax only: use `../scripts/monai_bundle_smoke.py parse-inline` or `ConfigParser.load_config_file`.
- Need to validate metadata fields: use `verify_metadata`, but expect schema download.
- Need to validate fake network I/O: use `verify_net_in_out` with CPU and small shape controls.
- Need to package TorchScript: use `ckpt_export` after confirming checkpoint and model exportability.
- Need remote files or publishing: pause for user approval and credential/network checks.
