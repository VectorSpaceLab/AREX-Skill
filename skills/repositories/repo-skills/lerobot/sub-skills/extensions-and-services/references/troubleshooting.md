# Troubleshooting, omissions, and recovery

## Unknown type after installing a plugin

1. Run the read-only discovery probe and confirm the installed distribution `Name` starts exactly with an accepted prefix.
2. Remember that the distribution suffix is not necessarily the registered `type`.
3. Check whether import failed; discovery logs failures and continues.
4. In a fresh local process, explicitly import the intended package and inspect the relevant ChoiceRegistry/processor registry. Do not import a package that may connect hardware just to test a type.
5. For a scoped env/plugin package, use `--<field>.discover_packages_path=<package>` and ensure registration occurs during package import.
6. If the type is still unknown, verify that the config class decorator ran and that the selected CLI field uses the right registry base. A type is not available merely because a class exists in a file.

## Conflicting registration

A duplicate `ProcessorStepRegistry` name raises `ValueError` while importing the second class. ChoiceRegistry collisions can similarly make parsing/import fail. This is not recoverable by selecting whichever import happened first: restart the process, remove one plugin, or rename the extension's public registration. Do not mutate a live registry in a long-running service as a collision workaround. For a synthetic test, use two isolated subprocesses or clear a test-only registry after the assertion; never clear production registries.

## Processor cannot deserialize

- `registry_name` missing: import the defining package before `from_config()` or use a fully qualified `class` path.
- Registry name unknown: the plugin did not load, was renamed, or is absent from the environment.
- `class` import fails: the module path or class name is stale; prefer a stable registry name for published pipelines.
- Constructor fails: compare saved `config` keys and overrides with the current signature.
- Missing/unexpected state: keep step order, registered names, state filenames, and tensor keys aligned.
- Artifact error: use a checkpoint-relative path that exists; absolute paths and `..` traversal are rejected.

If loading from a Hub id, distinguish missing files/credentials/network from a malformed local JSON. Re-run with a pinned revision and `local_files_only=True` only after the files are already cached.

## Async endpoint or protocol mismatch

- **Connection refused/unavailable:** compare the client `server_address` with the server's bind host/port and confirm the async extra is installed. Do not port-scan or start a daemon as a diagnostic.
- **Ready succeeds, setup fails:** compare policy registration, checkpoint visibility on the server, policy optional extra, device, and feature metadata. A client-local checkpoint is not visible to a remote server.
- **Unsupported policy:** import/register the policy before server startup and use the registered policy name; the server checks its supported policy registry.
- **Empty actions/timeouts:** inspect `fps`, `obs_queue_timeout`, action queue pressure, tensor/image shapes, and server inference errors. An empty `GetActions` response can mean no observation arrived before the timeout.
- **Malformed or oversized payload:** ensure both peers use the same generated protobuf contract and chunking states. Pickle is version/trust sensitive; never accept arbitrary peer payloads.
- **Overlapping actions look unstable:** check `actions_per_chunk`, threshold, and aggregate function. The four built-ins are exact names from the local registry.
- **Service appears unsafe:** the reference uses insecure gRPC and has no auth/TLS. Keep it private or add an explicitly reviewed secure transport layer before exposure.

The bundled async checker deliberately stops before network, model download, robot construction, or daemon startup.

## Annotation config/schema failure

- **Local schema error:** fix nested field names/types, non-positive rates/ports, invalid module choices, or episode indices; rerun the checker.
- **VLM URL/key absent:** stop before network. For local `openai`, explicitly arrange a running compatible server and credential policy; for remote Jobs, ensure the pod can access the model/runtime. Do not substitute a remote endpoint silently.
- **Timestamp error:** copy exact source frame timestamps; do not round/recompute them.
- **Orphan interjection:** add its paired speech atom and same-time plan refresh, or remove the event.
- **Invalid VQA:** assistant content must be JSON with one of the documented key shapes, and a user/assistant pair must share timestamp/camera.
- **Wrong language column:** use only the documented styles; module/column routing is validated before parquet rewriting.
- **Remote root/config:** a pod cannot see a host-only root or nested config file. Use Hub `repo_id` and CLI overrides, then decide where output is pushed.

`skip_validation` is for debugging only. Preserve the staging tree and report errors before considering a writer run.

## Hardware/backend/credential gates

- Camera/robot/teleoperator plugins may import vendor SDKs, serial/CAN/ZMQ libraries, or platform-specific binaries. A successful class import does not prove the device is connected or safe.
- Video annotation needs a usable decoder; `torchcodec` may be installed but unloadable, with PyAV as the documented fallback. Remote annotation images must include a compatible decoder and ffmpeg support.
- Async requires gRPC/protobuf; policy-specific transformers, diffusers, PEFT, or other extras are policy-dependent. Install the smallest selected extra and record its version.
- HF Jobs requires an authenticated Hub account, a Hub-visible dataset/model/config, a selected flavor, and an output push policy. W&B-enabled remote training additionally requires its key. Never print or guess secrets.

## Intentional omissions and uncertainty

This sub-skill intentionally does not prescribe vendor-specific robot/camera/teleoperator APIs, policy architecture/training hyperparameters, camera calibration, simulation setup, TLS deployment, service authentication, cloud pricing, VLM prompt quality, or data-model migration steps. Those require the focused workflow and/or current vendor/platform documentation.

The async transport currently serializes Python objects with pickle and exposes an insecure gRPC server; no claim of production security is made. The plugin discovery helper filters distribution metadata by exact prefix and logs import failures rather than returning a structured public result. The annotation validator's memory-at-boundary condition is a warning in the current implementation, while other invariants are errors. `PolicyServerConfig` computes `1/fps` during validation, so zero FPS can surface as a division error rather than the friendliest custom message. Treat these as known limits, not behaviors to build safety around.

## Safe completion criteria

A diagnostic is complete when it states the exact local facts checked, lists unresolved gates, does not contact a service or Hub, does not import an actuation plugin by default, and leaves no credentials or generated files in the runtime skill tree. Only a user-approved launch may cross from this reference into hardware, network, cloud, or write operations.
