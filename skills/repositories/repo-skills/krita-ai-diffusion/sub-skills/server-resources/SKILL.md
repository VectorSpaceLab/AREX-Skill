---
name: server-resources
description: "Guides Krita AI Diffusion ComfyUI, cloud, managed server, backend,
  resource catalog, custom node, model, and URL troubleshooting tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# server-resources

Use this sub-skill when the task is about the plugin's local ComfyUI server,
external ComfyUI connection, cloud service, model/resource catalog, custom nodes,
backend selection, or server errors.

Trigger examples:

- Normalizing or debugging ComfyUI URLs and WebSocket endpoints.
- Explaining `ComfyClient`, `CloudClient`, `ClientModels`, `Server`, or
  `ServerState` behavior.
- Checking required/optional custom nodes and resource catalog version.
- Diagnosing missing checkpoints, LoRAs, control models, inpaint models,
  upscalers, or server install state.
- Planning a managed server install/download/upgrade/uninstall safely.
- Parsing common server startup errors without running the server.

## Safe entry points

```bash
python scripts/list_krita_ai_diffusion_resources.py --summary
python sub-skills/server-resources/scripts/check_server_resources.py --summary
python sub-skills/server-resources/scripts/check_server_resources.py --parse-url localhost:8188
```

These commands inspect catalog/code facts and URL normalization only. They do
not install ComfyUI, download models, start a server, connect to cloud, or run
generation.

## References

- [references/client-server-reference.md](references/client-server-reference.md):
  client/server classes, URL parsing, server lifecycle, and safety policy.
- [references/resources-and-models.md](references/resources-and-models.md):
  resource catalog, custom nodes, architectures, model requirements, and model
  inventory guidance.
- [references/troubleshooting.md](references/troubleshooting.md): server,
  backend, URL, missing model/node, and cloud failure recovery.
- [scripts/check_server_resources.py](scripts/check_server_resources.py): bundled
  read-only catalog and URL helper.

## Boundaries

- For payload shape after server resources are selected, route to
  `inference-workflows`.
- For Graph workspace placeholder nodes and custom workflow metadata, route to
  `custom-graphs`.
- For UI settings that store server mode, backend, URL, or authorization, route
  to `ui-workspaces` as well.
