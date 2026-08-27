---
name: extensions-and-services
description: "Extend LeRobot with discoverable policies, processors, hardware
  plugins, asynchronous inference, transport services, annotation validation, or
  Hugging Face Jobs without crossing hardware, network, credential, or
  dataset-safety boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Extensions and services

Use this skill when the task mentions a custom policy, processor, plugin, package prefix, `lerobot_robot_`, `lerobot_camera_`, `lerobot_teleoperator_`, async inference, a policy server/client, gRPC, transport, annotation, an annotation schema, HF Jobs, or a service endpoint.

## Safety and routing

- This skill covers extension seams and **local diagnostics**. It does not replace the dataset, policy, hardware, simulation, or training sub-skills.
- Route dataset creation, episode/video decoding, language-column editing, and ordinary dataset inspection to the dataset skill; route model architecture/training/evaluation to the policy skill; route robot motion, camera capture, calibration, teleoperation, and motor access to hardware; route Gym/env execution to simulation.
- Never start a daemon, connect to a robot/camera, open a remote endpoint, submit a job, push to the Hub, or send credentials merely to diagnose a configuration.
- Treat remote bytes as untrusted. The async implementation currently uses pickle for handshake, observations, and actions; use it only between mutually trusted endpoints on a protected network. Do not deserialize arbitrary bytes in a probe.

## Inputs and outputs

Inputs are one or more of: a plugin distribution/package name, a config or config fragment, a processor JSON checkpoint, an async server/client parameter set, a local annotation staging tree, or a proposed HF Jobs command. Establish the requested route, package extras, device/backend, endpoint ownership, credential availability, and whether the user wants a dry-run or an actual launch.

Produce a route decision, a normalized local config, a list of discovered/registered types, or a validation report. A successful diagnostic proves only local parsing/importability/schema invariants; it does not prove hardware, network, model download, VLM availability, Hub authorization, or actuation.

## Decision flow

1. **Classify the extension.** Choose plugin discovery, registry/factory, processor serialization, async service, annotation, or Jobs. Start with the [extension API](references/extension-api.md) or the closest route below.
2. **Check the boundary.** Confirm optional extras and whether the requested operation needs a GPU, vendor SDK, ffmpeg/video backend, HF token, or writable Hub repo. Stop at the first missing gate.
3. **Inspect before importing.** Run the read-only plugin probe for installed distribution prefixes. Use explicit `discover_packages_path` only when a local plugin package is intentionally supplied. Do not guess a registered `type` from a distribution name.
4. **Validate local structure.** Use `async_config_check.py` for server/client scalar settings and `annotation_config_check.py` for annotation config/schema. Use `--help` on the real CLI for scoped draccus fields, but do not launch it.
5. **Resolve collisions and unknowns.** Registry names are global within the process. A duplicate processor-step name raises `ValueError`; an unknown policy/hardware/step type is a registration/import problem, not a network problem. Remove or rename the conflicting registration and start a fresh process.
6. **Only then hand off.** If the user explicitly requests execution, hand the verified config to the relevant focused skill and require its own hardware/network/credential confirmation.

## Extension quick routes

- **Policy:** register a `PreTrainedConfig` subclass with a unique name, make its modeling module expose the corresponding policy class, and provide required feature/delta/optimizer/scheduler validation. Use the policy factory; do not instantiate a model by guessing a module path.
- **Processor:** implement `ProcessorStep.__call__` and `transform_features`; use a unique `ProcessorStepRegistry` name. Keep `get_config()` JSON-serializable and use tensor `state_dict()` only for state. Test both data and feature transforms.
- **Robot/camera/teleoperator:** subclass the corresponding `*Config`, register a unique choice, expose the implementation class using the config class name without the trailing `Config`, and keep vendor imports optional. Factory construction can connect or touch hardware, so diagnostics stop at config/type resolution.
- **Plugin:** an installed distribution whose name starts with an accepted `lerobot_*_` prefix is imported by `register_third_party_plugins()`. Package initialization should register choices; failures are logged and do not abort discovery. For scoped config plugins, `load_plugin()` imports the package and its immediate submodules.

## Async and transport route

The async route is a two-process gRPC protocol: client calls `Ready`, sends a pickled `RemotePolicyConfig` via `SendPolicyInstructions`, streams chunked pickled `TimedObservation` values through `SendObservations`, and requests pickled `list[TimedAction]` values through `GetActions`. The server loads the requested policy and pre/post-processors; the client executes actions locally. Matching host/port, policy type, checkpoint visibility, device, feature keys, FPS, chunk size, and aggregate function are all required. `services.proto` also declares learner transition RPCs; do not confuse those with async inference.

Use [services](references/services.md) for wire details, serialization limits, retries, and a no-daemon mismatch diagnosis. A successful config check must not be reported as a live endpoint check.

## Annotation and Jobs route

Annotation is a local or HF Jobs VLM workflow, not a harmless metadata edit. It stages module JSONL, validates timestamps/column routing/pairs/VQA JSON, then rewrites parquet. Validate a local config and synthetic staging shape before considering a real run. Remote annotation requires a Hub dataset id and HF authentication; a local `root` is not visible in the pod, and output is discarded without `push_to_hub=true`. Training Jobs similarly stage/resolve configs, forward secrets, and submit cloud work; use the training skill for the actual run.

See [annotation and Jobs](references/annotation-and-jobs.md) for the local schema and credential gates. `annotation_config_check.py` never contacts a VLM, Hub, endpoint, or Jobs service.

## Bundled diagnostics

- [`scripts/plugin_discovery_probe.py`](scripts/plugin_discovery_probe.py) — lists installed distributions matching LeRobot plugin prefixes without importing them.
- [`scripts/async_config_check.py`](scripts/async_config_check.py) — validates server or client scalar configuration from local JSON/YAML or flags; never starts gRPC.
- [`scripts/annotation_config_check.py`](scripts/annotation_config_check.py) — validates local annotation config fields and optional synthetic staging rows; never calls the VLM or Hub.

All scripts accept `--help`, are safe from arbitrary working directories, and write no files by default. Keep reports outside this skill tree.

## Verification checklist

Before handing off an extension or service draft:

- confirm the requested package extra and Python/runtime version are compatible;
- run the plugin probe and record candidates without importing actuation code;
- run both valid and invalid async cases, including endpoint syntax and aggregate-name errors;
- run annotation config validation with a synthetic passing case and an off-frame/orphan/VQA failure;
- check that every registry name, processor step, artifact, and state tensor has a stable owner;
- record whether the next step needs model files, GPU, vendor SDK, network, token, Hub write, or physical actuation;
- keep generated reports and temporary configs out of the runtime skill directory.

A synthetic collision case should place two isolated plugin packages on the import path with the same processor registration and show the second import failing with a duplicate-name error; recovery is to rename/remove one and retry in a fresh process. A synthetic service mismatch should pair a valid local server config with a client address using a different port and show the checker stopping before any connection. A synthetic annotation case should pass local VQA/timestamp/pair validation while omitting `api_key` or using an unavailable remote target, then stop with the network/credential requirement rather than attempting a call.

## Configuration and recovery

Use [configuration](references/configuration.md) for draccus, `ChoiceRegistry`, path-vs-type rules, processor JSON/state/artifact boundaries, and Hub-locality behavior. Use [troubleshooting](references/troubleshooting.md) when a type is unknown, a plugin collides, an endpoint is mismatched, a backend is missing, annotation validation fails, or a remote credential is absent.

Validation is complete only when links resolve, scripts pass parser/help checks, local configs pass or fail with actionable errors, and every unresolved hardware/network/credential assumption is recorded. Intentional omissions and known implementation hazards are preserved in the troubleshooting reference.

## Handoff format

Return a concise record with:

- **Route:** plugin, registry/factory, processor, async, annotation, or Jobs;
- **Inputs:** config source kind, selected type/name, local-vs-Hub ownership, and requested side effects;
- **Validated:** exact local checks and their pass/fail results;
- **Gates:** missing extra, vendor/backend, endpoint, model, credential, Hub write, or actuation gate;
- **Recovery:** the smallest safe next action, preferably in a fresh process;
- **Omissions:** behavior not proved because this skill stopped before network, cloud, or hardware.

Do not claim that a plugin is usable because its distribution is listed, that a service is reachable because its address parses, or that an annotation is publishable because its JSON schema passes. Do not duplicate dataset editing, policy training, hardware control, or simulation instructions here; hand those routes to the focused sub-skills.
