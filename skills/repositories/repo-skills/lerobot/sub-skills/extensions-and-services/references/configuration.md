# Configuration and serialization boundaries

## draccus and ChoiceRegistry

LeRobot command configuration is dataclass-based and parsed by draccus. Polymorphic fields use a registered `type` choice. Import the module that defines a built-in or plugin subclass before parsing, or load the plugin using the explicit discovery argument described in `extension-api.md`.

The parser's `wrap()` adds LeRobot-specific handling:

- `--config_path` selects a YAML/JSON config;
- `--field.type=name` selects a registered choice;
- `--field.path=value` is reserved for path/pretrained loading and is removed before draccus sees the choice fields;
- `--field.discover_packages_path=package` imports a package and its immediate submodules before parsing;
- `--help` prints scoped help for choices already selected on the CLI.

A path and type for the same field are mutually exclusive. YAML/JSON nested values are flattened into CLI-style overrides where needed. Keep config files portable: use relative local paths only when the target process has the same filesystem, and use Hub ids/revisions only when a network/credential gate has been consciously accepted.

Unknown fields, misspelled nested paths, invalid enum/choice values, missing required fields, and malformed types should be fixed in the config—not hidden by passing a different type. Capture the parser's error and the exact flag before changing values.

## Async config boundary

`PolicyServerConfig.from_dict(mapping)` and `RobotClientConfig.from_dict(mapping)` are thin dataclass constructors. Server serialization includes `host`, `port`, `fps`, `environment_dt`, and `inference_latency`; it does not include every internal field (notably queue timeout in `to_dict`). Because `environment_dt` is a derived property rather than a dataclass field, do not feed `PolicyServerConfig.to_dict()` back to `from_dict()` unchanged; remove the derived key and preserve `obs_queue_timeout` separately. Client serialization includes endpoint, policy/checkpoint, devices, threshold, FPS, chunk size, task, visualization, and aggregate name. The live client config also requires a concrete `robot`, which is intentionally not constructed by the safe checker.

Use string devices that the **process doing inference or execution** can actually resolve (`cpu`, `cuda`, `cuda:0`, `mps`, or another supported torch device). The client may run policy inference remotely and action execution locally, so `policy_device` and `client_device` have distinct ownership. A server cannot load a checkpoint that exists only on the client filesystem.

The current server constructor validates port, inference latency, and observation timeout. It computes `environment_dt=1/fps`; keep `fps > 0` even where an invalid zero can surface as a division error before a friendly message. The client validates non-empty server/policy/checkpoint/device values, a threshold in `[0,1]`, positive FPS and action count, and a known aggregate function.

## Processor pipeline JSON

A saved pipeline has a JSON object with `name` and a `steps` list. Each step has either:

```json
{"registry_name": "unique_step", "config": {}}
```

or:

```json
{"class": "package.module.StepClass", "config": {}}
```

Registered names are preferred for portability. A stateful step may add `state_file`; the pipeline stores tensor state in safetensors grouped by a deterministic step key. A step may also declare `artifacts`; each artifact path must be relative to the checkpoint and cannot contain `..` or be absolute. Artifact files must exist before the pipeline is saved.

`DataProcessorPipeline.from_config()` is the safe constructor for an in-memory config plus optional state tensors. `from_pretrained()` additionally resolves local files or downloads a named config/state/artifact from a Hub model. It requires an explicit `config_filename`, validates the processor shape, resolves registry/import classes, merges per-step overrides, loads state, and rejects unused override keys. Use `local_files_only=True` for a deliberate offline check.

Treat `class` strings and registry names as executable import/constructor instructions. Do not load a pipeline from an untrusted checkpoint. Preserve a version/revision with any published pipeline and test that a clean process can import every registered step.

## Annotation config boundary

`AnnotationPipelineConfig` is a regular dataclass tree, not a `ChoiceRegistry`. Its `root` and `staging_dir` are local paths; `repo_id` and `new_repo_id` are Hub ids. `VlmConfig.api_base` is a URL-like string, `serve_port` is a local server port, and `api_key` is a secret boundary even when it is the literal `EMPTY`. `only_episodes` should contain non-negative integer indices; module booleans are independent.

`AnnotationJobConfig` extends `JobConfig` with an annotation image, a shorter default timeout, and `lerobot_ref`. `job.target` values omitted or `local` are local; all other values are remote flavors. Do not put a local config-file path inside a remote job config: the remote submitter explicitly rejects host-only config files.

## Hub and serialization checklist

Before publishing any custom config or pipeline, check:

- all `get_config()` values are JSON serializable;
- state tensors load with the intended dtype/shape and the state key matches the step index/name;
- artifact paths are checkpoint-relative and present;
- registry/module identifiers are stable across a clean environment;
- optional dependencies are declared in the appropriate extra and guarded at use time;
- Hub ids, revisions, visibility, and push flags are explicit;
- no token, endpoint secret, device-local path, robot port, or calibration data is logged.

A config parse proves only syntax and constructor validation. It does not prove model weights, camera frames, robot connectivity, cloud authorization, VLM readiness, or service reachability.
