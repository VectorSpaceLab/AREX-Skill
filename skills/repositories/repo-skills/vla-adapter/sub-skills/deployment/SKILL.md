---
name: deployment
description: "Guides VLA-Adapter inference servers, MsgPack or JSON action
  payloads, ALOHA fake-client checks, and real robot deployment boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment (external-checkout adapter)

This sub-skill documents deployment contracts and renders commands for a
separate native checkout. It contains only documentation and safe command or
synthetic-payload helpers; it does not contain `prismatic/`, `vla-scripts/`, or
`experiments/robot/`, and it never starts a server, client, or robot.

Before using any native entrypoint, set and enter the absolute checkout root:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"
```

External prerequisites depend on the selected operation: base package plus
CUDA/checkpoint for a server; FastAPI/uvicorn and the matching JSON or MsgPack
serialization packages for HTTP serving; the native ALOHA fake-client and its
runtime for a fake check; and ROS, cv_bridge, sensor/message packages, camera
inputs, hardware, and a human operator for a real client. Install these in the
native/robot environment, not in this generated skill.

## Read and render

- Read [references/server-client-contracts.md](references/server-client-contracts.md)
  for JSON/MsgPack schemas and native command expectations.
- Read [references/aloha-real-robot.md](references/aloha-real-robot.md) before
  any real Cobot Magic/ALOHA deployment.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  HTTP, serialization, checkpoint, CUDA, and ROS failures.
- Render commands with [scripts/build_aloha_launch.py](scripts/build_aloha_launch.py)
  using `--repo-root "$VLA_ADAPTER_REPO_ROOT"`. `build_aloha_launch` **only
  prints** `cd <absolute-repo-root> && ...` commands; it does not execute or
  validate a server/client.
- Run [scripts/validate_msgpack_payload.py](scripts/validate_msgpack_payload.py)
  only to inspect a deterministic **synthetic** payload. It checks keys, image
  dtype/shape, state shape, and non-empty strings; it is not a server, client,
  HTTP probe, or connectivity test. `--write-msgpack` additionally requires
  external `msgpack` and `msgpack-numpy` packages.

## Native source entrypoints

After review, native commands must be run from `cd <absolute-repo-root>` and
use the external source files below (the adapter does not invoke them):

| Operation | Native source entrypoint |
| --- | --- |
| MsgPack server | `experiments/robot/server_deploy/deploy.py` |
| JSON server | `vla-scripts/deploy.py` |
| Fake ALOHA client | `experiments/robot/aloha/run_fake_cobot_client.py` |
| Real ROS client | `experiments/robot/aloha/run_cobot_client.py` |

## Deployment workflow

1. Validate the checkpoint and server contract against the linked references.
2. Confirm CUDA and operation-specific package/ROS prerequisites.
3. Decide whether the client/server should use MsgPack (ALOHA primary) or JSON.
4. Inspect a synthetic payload with the bundled validator; this does not
   contact a server.
5. Review the rendered native command, then run a native fake-client sanity
   check before any real robot client.
6. For real robots, confirm ROS topics, emergency stop, operator procedure,
   action scaling, and `unnorm_key` before publishing commands.

## Safety boundaries

- Never run a real robot client from an automated agent without explicit human
  operator approval and a safe physical setup.
- Do not expose a VLA action server on an untrusted network without access
  controls; the basic repo server is a research utility, not a hardened service.
- Treat `unnorm_key` mismatch as a safety issue because it changes action scale.
