# Services and Rendering

## When to read

Read this for TorchRL `Service` owners, `get_services`, direct/process/Ray
placement, Python tool execution services, and the `rlrender` / `torchrl-render`
commands. Run [smoke_services.py](../scripts/smoke_services.py) for safe import,
signature, and direct-lifecycle checks.

## Service owner/client lifecycle

TorchRL uses `Service` as the owner-side lifecycle contract for long-lived
resources. A service owner exposes:

- `start() -> self`
- `shutdown(timeout=None)`
- `client()` returning the restricted worker-facing capability
- `is_alive`

The owner constructs and shuts down the heavy resource. Worker code should use
only the client. Direct services are the deliberate exception: `owner.client()`
may be the owner itself because there is no isolation boundary in the same
process.

Keep lifecycle ownership in the driver:

```python
owner = make_service()
owner.start()
try:
    client = owner.client()
    run_workers(client)
finally:
    owner.shutdown()
```

Do not let a worker or collected TensorDict hold the only reference to a service
owner. Shut services down after collectors/evaluators stop, not before.

## Placement vocabulary and practical choices

TorchRL docs use a canonical service-backend vocabulary including `direct`,
`thread`, `process`, `ray`, `monarch`, and `distributed`; collector construction
also accepts related backends such as `rpc` and `submitit`. Individual domains
support only a subset. Unsupported combinations fail at construction instead of
silently emulating another backend.

Common choices:

- **direct**: same-process owner and client. Lowest overhead; no capability
  isolation. Good for debugging, small jobs, and CPU smoke tests.
- **thread/process**: owner is local but isolated from the driver. Useful for
  inference/logging processes; payloads must be pickle-compatible unless a
  specialized transport is configured.
- **Ray**: distributed ownership, placement, and discovery. Requires Ray and
  explicit cleanup. Use when independently created workers need to discover a
  shared service by name or when Ray-owned inference/replay/loggers are desired.

Placement is separate from payload transport. Inference, replay buffers,
loggers, and weight synchronization all keep domain-specific communication
contracts. Avoid writing code that assumes every service supports the same
operations just because it has a common lifecycle.

## Service registry

`get_services(backend="ray", **init_kwargs)` returns a distributed service
registry. Verified signature: `get_services(backend='ray', **init_kwargs) ->
ServiceBase`. The current public registry implementation supports Ray; passing
other backend names raises `ValueError`.

Ray registry basics:

```python
from torchrl.services import get_services

services = get_services(backend="ray", namespace="experiment")
if "tokenizer" not in services:
    services.register("tokenizer", TokenizerService, vocab_size=50000, num_cpus=1)
tokenizer = services["tokenizer"]
# Ray actor methods are called with .remote() and resolved by ray.get(...).
services.reset()
```

Use unique namespaces for independent experiments. `reset()` removes registry
entries and terminates registry-owned actors. Registering an already-started
`Service` owner stores its restricted client for discovery but does not transfer
shutdown ownership; removing the entry does not stop the external owner.

For a portable registry-facing service, keep constructor arguments separate from
backend actor options when possible. `register_with_options(...)` is Ray-specific.

## Python tool services

`PythonExecutorService(pool_size=32, timeout=10.0)` owns a pool of persistent
Python interpreter processes and exposes `execute(code) -> dict` with success,
stdout, stderr, and return-code-like fields. It is intended for many LLM envs
sharing a smaller interpreter pool.

`PythonInterpreter(tokenizer=None, tool_name="tool", persistent=False,
timeout=10.0, services=None, service_name="python_executor", namespace=None)` is
the transform that executes Python code blocks found in LLM responses:

- `services=None`: use local processes; `persistent=True` reuses processes.
- `services="ray"`: retrieve a registered Ray `python_executor` service by name
  and namespace.
- invalid `services` values raise an error.

Treat code execution as unsafe unless the prompt, tools, timeout, and execution
sandbox are controlled. For routine help or imports, prefer the bundled smoke
script rather than invoking `PythonInterpreter` on user text.

## Direct/process service example pattern

The source service examples share one training loop across direct, process, and
Ray placement. The important reusable pattern is not the environment used in the
example; it is the owner/client split:

1. construct logger/replay/inference owners for the selected placement;
2. register owner shutdown callbacks in reverse dependency order;
3. start owners that require explicit startup;
4. pass restricted clients into the TensorDict loop;
5. keep the training loop independent of placement; and
6. flush/shutdown owners deterministically.

This sub-skill bundles only a tiny direct-lifecycle smoke because the full
examples require optional environments, Ray, process spawning, logs, and longer
training. Process and Ray examples are reference-only unless the user asks to
provision those backends.

## Rendering and `rlrender`

`torchrl.render` powers the `rlrender` and `torchrl-render` commands. The CLI
loads a policy factory, environment factory, and local checkpoint, collects one
or more rollouts, captures RGB frames from TensorDict pixels or `env.render()`,
and writes an output.

Required options after config merging:

- `--ckpt`: local policy checkpoint path
- `--policy`: import spec or file path with `module_or_file:callable`
- `--env`: import spec or file path with `module_or_file:callable`

Frequently used options:

- `--config` JSON/YAML/TOML file; YAML requires PyYAML and TOML requires Python
  with `tomllib` support.
- `--format {ipynb,mp4,gif,frames,npz,jsonl}`; defaults from `--out` suffix,
  otherwise MP4.
- `--out`, `--max-steps`, `--num-trajs`, `--fps`, `--seed`, `--device`,
  `--policy-device`, `--env-device`.
- `--render-backend {auto,pixels,env,null}` and env backend selection via
  `--env-backend`.
- `--obs-key`, `--action-key`, `--done-key`, `--reward-key`, `--pixel-key` for
  TensorDict policies/envs.
- `--dry-run`, `--validate-only`, and `--print-config` for validation without
  rendering.
- notebook/MuJoCo WASM options such as `--notebook-render-backend`,
  `--notebook-rollout-mode`, `--mujoco-model-path`, `--mujoco-asset-paths`, and
  `--mujoco-qpos-key`.

Rendering extras are optional. MP4/GIF/PNG/video or YAML-backed configs may
require `rendering` or `video` dependencies, codecs, display libraries, and in
MuJoCo WASM notebook mode Node.js plus a package manager. Use `--dry-run` or
`--validate-only` before running an expensive render.

## Checkpoint and logging surfaces

`torchrl.render` includes helpers for `load_checkpoint`, `save_render_checkpoint`,
`checkpoint_hash`, `infer_state_dict`, `load_render_policy`, and output
writing. These are for local checkpoint/output workflows. Do not mix them with
LLM weight-sync schemes: rendering loads a static checkpoint for evaluation,
whereas vLLM/SGLang sync updates live inference workers and should be tracked
with policy versions.
