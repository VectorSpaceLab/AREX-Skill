---
name: setup-and-host
description: "Choose and safely prepare the legacy GIMP-ML plug-in path or the
  newer local Python 3 service path, including host checks, discovery,
  permissions, weights layout, lifecycle, and refresh safety."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Setup and host

Use this sub-skill when a user needs to install, discover, diagnose, or safely refresh GIMP-ML on a host. This is an operating guide, not a promise that the historical plug-ins run on a current machine.

## Non-negotiable facts

- The historical plug-in tree targets **GIMP 2.10, Python 2.7, `gimpfu`, and a `gimpenv` virtualenv**. Its imports and `sys.path` entries are Python-2.7-specific.
- The historical installation expects a sibling `weights/` tree below the installed plug-in directory. Model files are not supplied or downloaded by this skill.
- A newer installed GIMP-ML application may expose a Python 3 FastAPI service with GET `/status` plus model-affecting POST routes. The service port is deployment-selected and must come from the installed application or its operator.
- A Python 3 service-core verification passed package consistency, imported the FastAPI application, and exposed the expected route declarations. This did **not** verify every historical requirements entry: launcher-only/platform packages such as PyQt6, PyQt6-WebEngine, and pywin32 remain unverified.
- The checked host had no GIMP and no Python 2.7. CUDA was visible, but even a tiny allocation was blocked by host CUDA OOM. No model weights, provider credential, provider request, or successful inference is assumed. Do not promise GIMP 3 compatibility.

## Decision tree

1. **Need a menu item or a GIMP PDB call?** Choose the legacy path only when the target host independently provides GIMP 2.10 with its Python-Fu/PDB bridge, Python 2.7-compatible dependencies, and a readable/executable installed plug-in tree. Follow [installation](references/installation.md) and [host compatibility](references/host-compatibility.md).
2. **Have GIMP 2.10 or Python 2.7 been ruled out?** Stop the legacy path. Do not substitute Python 3.11 for embedded Python-Fu. A service-capable client may use an already installed local service, but a GIMP menu/PDB integration remains blocked.
3. **Need the newer text-image workflows?** Use the installed GIMP-ML application's supported launcher when one is present. Then obtain the active loopback port from the installed application or operator and verify only GET `/status` with `scripts/check_service_status.py` before any model operation.
4. **Is no supported installed launcher available?** Report `blocked: deployment-specific service startup`. Do not invent a command that runs or imports files from an original source checkout.
5. **Is a model-backed operation requested?** First inspect the installed legacy asset layout with `scripts/check_layout.py`. Missing weights are a blocked capability, not a reason to run a downloader.
6. **Is a plug-in invisible?** Run `scripts/check_plugin_registrations.py` against an explicitly supplied installed/candidate plug-in tree, then verify the host's configured plug-in directory and permissions. A static `register()` finding is not proof that GIMP loaded it.
7. **Is an update or refresh requested?** Make a backup or disposable copy, review the installation package, and preserve `weights/` and environment data. Never execute an unfamiliar bundled updater or downloader automatically.

## Safe operating sequence

1. Record the user-provided installed plug-in root, intended mode (legacy or service), and desired boundary (menu/PDB or HTTP). For service mode, record the operator-provided active loopback port; do not infer it from a checkout or a historical default.
2. For a legacy candidate, run the two bundled static checks with explicit installed/candidate paths. They do not import plug-ins, contact a network, download weights, start GIMP, or mutate files.
3. For legacy mode, perform presence and permission checks only; configure the installed plug-in folder in GIMP 2.10 Preferences → Folders → Plug-ins, then restart GIMP manually. Do not claim this was tested on the current host.
4. For service mode, ask the operator to use the installed application's supported launcher. Once the operator confirms that the service is running and supplies its active loopback port, run:

   ```bash
   python3 scripts/check_service_status.py --port <active-port>
   ```

   This helper performs one loopback-only GET `/status`; it does not start, stop, import, or configure the service. If the launcher or active port is unavailable, return a deployment-specific startup blocker.
5. Treat a missing menu, missing PDB procedure, unavailable `gimpfu`, missing weights, refused loopback connection, or failed model prerequisite as a diagnostic result. Use [troubleshooting](references/troubleshooting.md) rather than silently switching modes.

## Inputs, outputs, and evidence labels

Inputs are an explicitly supplied installed/candidate plug-in root, optional weights root, target GIMP generation, desired boundary, and—for service liveness only—an operator-confirmed active loopback port. Never infer a deployment path or port from the current checkout.

The output is a mode verdict and a next safe check:

- **legacy eligible** means the host prerequisites and selected files were independently observed; it does not mean inference works;
- **service eligible for liveness** means the installed application's supported launcher was used or the operator independently confirms an already running service, and the bundled helper validated GET `/status` on the supplied loopback port;
- **blocked** names the missing prerequisite, such as GIMP, Python 2.7, `gimpfu`, weights, a supported service launcher, an active port, provider access, or device memory;
- **static-only** means installed/candidate layout or registration evidence was inspected without executing the plug-in or model.

Keep those labels separate. Service liveness cannot upgrade a legacy menu result, and a present checkpoint cannot upgrade a provider or GPU result.

## Service lifecycle boundary

This skill has no portable service-start command. The only supported lifecycle path is the installed GIMP-ML application's launcher or an operator-managed deployment. Do not open, run, import, or adapt an original service module or configuration file to manufacture a startup command.

After supported startup, obtain the active port from the installed application/operator and accept only a loopback endpoint. The bundled status helper rejects non-loopback hosts by design. A successful `/status` response establishes only HTTP process liveness; it does not establish weights, provider credentials, CUDA capacity, or inference correctness. Stop the service only through the same installed launcher/operator procedure that started it.

## Stop rules and ownership

Stop before changing anything when the requested mode, target GIMP generation, asset source, or service ownership is unclear. Ask the operator to choose the boundary rather than silently installing both stacks.

Stop at static-only when the host cannot provide GIMP 2.10/Python-Fu or a required checkpoint. Stop at `blocked: deployment-specific service startup` when no installed launcher/operator procedure or active loopback port is available. Stop before any model/provider operation that lacks explicit authorization.

The operator owns package installation, service deployment, credentials, model provenance, active-port disclosure, and any manual GIMP preference change. Never turn an updater failure into a retry loop: preserve the copy, capture the diagnostic, and use the reviewed refresh procedure in [installation](references/installation.md).

## Bundled checks

- `scripts/check_layout.py` reports a supplied plug-in root, `weights/`, optional `gimpenv/`, model directories, and permission/readability facts without changing anything.
- `scripts/check_plugin_registrations.py` scans supplied text files for likely Python-Fu `register()` calls, procedure names, menu paths, `gimpfu` imports, and `main()` calls without executing Python.
- `scripts/check_service_status.py` performs one proxy-disabled GET `/status` against an explicit loopback port, validates a JSON object with `service: running`, and never starts or configures a process.

Use `--help` first when integrating any script. The layout and registration helpers report missing paths safely; the status helper returns nonzero when liveness is not established.

## Evidence and provenance — not runtime instructions

Historical source evidence used to establish safety boundaries included `gimpml/service.py`, `gimpml/config.json`, `gimpml/GIMPML.py`, `gimpml/gimp2/text_*_g2.py`, `installGimpML.sh`, `update.py`, and `syncWeights.py`. It showed three local routes, launcher-selected ports, Python-Fu registration patterns, and potentially destructive/networked update behavior. These names are provenance and warnings only: do not locate, open, run, import, or adapt them while following this skill.

## Read order

Start with this router, then open the relevant bundled reference only after the mode is selected. Keep the final verdict and unresolved blockers explicit.

## Limits

This sub-skill does not install Python 2, GIMP, virtualenv, model weights, provider credentials, platform GUI packages, or a service deployment. It does not run GIMP, manufacture a service-start command, call model-affecting routes, mutate a GIMP image, or certify GIMP 3. See [installation](references/installation.md), [host compatibility](references/host-compatibility.md), and [troubleshooting](references/troubleshooting.md) for the detailed contracts.
