# Notebook workflows

This document covers how CubeStudio notebooks are created, opened, reset, renewed, stopped, and routed to JupyterLab or Theia.

## Notebook record fields

The notebook record centers on:

- `project`
- `name`
- `describe`
- `namespace`
- `images`
- `ide_type`
- `working_dir`
- `env`
- `volume_mount`
- `node_selector`
- `image_pull_policy`
- `resource_memory`
- `resource_cpu`
- `resource_gpu`
- `expand`

Important defaults:

- namespace defaults to `jupyter`
- node selector defaults to `cpu=true;notebook=true`
- resource GPU defaults to `0`
- working directory defaults to `/mnt`
- the user workspace mount is always present unless explicitly blocked by policy

## Create and open flow

Notebook creation and opening are handled by the entry endpoint that can both create a record and start the pod.

Behavior to remember:

- names are normalized to lowercase, underscores become hyphens, and the backend truncates long names
- images are selected from `NOTEBOOK_IMAGES`
- image labels determine `ide_type`
- `theia` / `vscode` images open a Theia-style IDE
- `matlab` and `rstudio` images map to their own runtime types
- all other notebook images default to JupyterLab
- `entry_jupyter` can reuse an existing notebook record if the name already exists
- `file_path` is normalized so text files open in the JupyterLab tree, while non-text paths are reduced to directories

## URL patterns

Notebook URLs are generated from the runtime type and edge-network settings.

| Runtime | Typical route |
| --- | --- |
| JupyterLab | `/notebook/jupyter/<name>/lab?#/mnt/<user>` or a tree URL for a saved root path |
| Theia | `/notebook/<namespace>/<name>/#...` |
| Matlab | `/notebook/<namespace>/<name>/index.html` |
| RStudio | `/` |

Other notebook actions:

- `reset` → destroy and recreate the notebook pod / service / virtual service
- `renew` → bump `changed_on` so the expiry timer moves forward
- `stop` → stop and clean up notebook resources
- `save` → UI-only commercial marker; not a standard self-service backup flow

## Mount and startup behavior

Notebook pods rely on a fixed per-user workspace.

Key points:

- user work is expected to live under `/mnt/<username>`
- `Project.volume_mount` is merged into notebook mounts
- user-specific mounts can be filtered by the user-volume policy
- image startup runs `/init.sh` and `/mnt/<username>/init.sh` when present
- `init.sh` is where notebook images set SSH, examples, or other startup customization

## Edge and proxy behavior

The notebook route may be served through an external edge IP.

Fallback order for the external IP:

1. `Project.expand.SERVICE_EXTERNAL_IP`
2. cluster host
3. global `SERVICE_EXTERNAL_IP`
4. the current request host

If edge mode is enabled:

- the notebook uses `NOTEBOOK_PORT` to compute user-facing ports
- the helper selects a non-blacklisted port before building the redirect
- the generated notebook view may point at the external proxy IP instead of the internal cluster host

## Lifecycle reminders

- Notebook pods are treated as disposable compute sessions.
- Persistent work belongs in `/mnt/<user>` or in version-controlled files.
- If a notebook image or environment changes, a reset is often required before the new settings take effect.
- The UI list shows status, resource summary, renew, reset, and save links so users can manage lifecycle from the table view.

## Safe routing reminders

Use this document for notebook UX questions, not for cluster installation or notebook image build mechanics.
For image family and registry questions, continue to `image-catalog.md`.
For selector math, continue to `resource-and-kubernetes-api.md`.
