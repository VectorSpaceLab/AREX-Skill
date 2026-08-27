# Setup and host troubleshooting

Run the bundled commands below from the `setup-and-host/` sub-skill directory (or replace `scripts/...` with the absolute path to that bundled script). They inspect only operator-supplied files or a loopback endpoint; they do not import the source checkout.

Classify the failure first. Do not “fix” a legacy mismatch by running a downloader, silently changing interpreters, or inventing a service command from source artifacts.

## Triage table

| Symptom | Safe checks | Interpretation and next action |
|---|---|---|
| GIMP menu is absent | `python3 scripts/check_plugin_registrations.py <plugin-root>`; inspect the host's configured GIMP plug-in directory and file mode | Static registrations do not prove loading. Confirm GIMP 2.10/Python-Fu, exact search path, executable/read permission, and restart manually. If GIMP is absent, mark blocked. |
| `No module named gimpfu` or PDB is unavailable | Run the bundled registration scan; use `python2 --version` and `gimp --version` only as presence checks | A standalone Python 3 invocation cannot supply embedded legacy `gimpfu`. Stop; do not add random Python 3 packages. |
| Legacy entry uses a Python-2-specific environment | Treat the static scan and layout checker as the boundary | This is a runtime mismatch. Use a compatible GIMP 2.10 host or report the legacy path blocked; GIMP 3 compatibility is unverified. |
| Menu appears but model operation fails | `python3 scripts/check_layout.py <plugin-root>`; compare expected files in [host compatibility](host-compatibility.md) | Missing/unreadable `weights/<model>/...` or incompatible packages are capability blockers. Do not download automatically. |
| `weights/` is missing | Run the bundled layout checker | The historical contract expects external assets. Ask the operator to supply reviewed weights through the normal supply chain. |
| Weight directory exists but file is missing | Use the layout checker's expected-file report | Directory existence is not model installation. Do not infer provenance or integrity. |
| Permission denied on plug-in or checkpoint | Inspect ownership, directory traversal, and file modes on the supplied deployment | Apply only a narrowly reviewed permission change to a copy. Never recursively chmod an unknown tree. |
| No supported installed launcher exists | Ask the application owner for its supported launcher/service procedure | Report `blocked: deployment-specific service startup`. Do not locate or run a source service module and do not construct an application-server command. |
| Active service port is unknown | Ask the installed application/operator for its current loopback port | Do not inspect an original configuration artifact or assume a historical default. Without the port, liveness is blocked. |
| `/status` connection refused | `python3 scripts/check_service_status.py --port <operator-provided-port>` | Confirm that the operator used the installed application's supported launcher and supplied the current port. If still refused, return the helper diagnostic and keep startup deployment-specific; do not manufacture a fallback command. |
| Status helper rejects the host | Use the default host or explicitly pass `--host 127.0.0.1`/`localhost` | Non-loopback hosts are outside this skill's security boundary. Do not bypass the rejection. |
| Service reports running but inference is unavailable | Keep the successful GET `/status` result separate from model prerequisites | Status is liveness, not inference. Missing weights, provider credentials/access, or device memory remain unresolved. |
| Service package/import issue is reported by the operator | Use the installed application's own diagnostics and package policy | The Creator inspection proved only selected service-core imports. PyQt6, PyQt6-WebEngine, pywin32, live launcher behavior, and every historical requirement were not verified. |
| CUDA is “visible” but model fails with OOM | Check current free memory using the host's normal monitoring tools; do not allocate a model just to probe it | The verified host could not allocate a tiny CUDA buffer. Prefer a CPU feasibility decision or report GPU blocked; do not promise a GPU result. |
| Updater threatens files | Stop; do not invoke it | Back up the deployment and perform a reviewed replacement rather than a network/destructive update. |
| Refresh changes configuration or weights unexpectedly | Compare the recorded manifest and backup against the deployment | Restore only from a reviewed backup. Never let an unreviewed refresh overwrite credentials, local settings, or model assets. |
| GIMP 3 is the only available GIMP | Report legacy menu/PDB path as blocked | No GIMP 3 support is established. Use only a separately validated integration. |

## Port and configuration contract

The active service port is an operator/deployment input. Obtain it from the installed application's own status UI or from the operator managing the deployment. Validate it with:

```bash
python3 scripts/check_service_status.py --port <active-port>
```

Do not derive the port by opening an original configuration file, do not assume a historical example value, and do not edit a deployment's configuration as an unreviewed “fix.” The helper accepts only loopback hosts and performs one GET `/status`.

## Registration diagnosis without execution

The registration checker reports likely procedure names and menus by looking around `register(...)` without importing files. Use it to answer “what should this supplied candidate file register?” It cannot detect runtime exceptions before registration, a GIMP plug-in search path mismatch, a bad PDB signature, or a missing model. A helper definition found by a whole-tree scan is evidence, not a menu entry.

## Missing service route versus missing GIMP PDB

These are different failures:

- A failed `/status` check means the expected local FastAPI process/route was not reached at the operator-supplied loopback port or returned an invalid response.
- A missing GIMP PDB procedure means the legacy plug-in was not loaded or registered in GIMP 2.10.
- A visible GIMP-ML menu does not prove that the service is alive; check the service boundary separately.

Check one boundary at a time: supplied static files → host runtime → already-running service liveness → model/provider prerequisites.

## Safe escalation questions

Before any install, update, service check, or model request, obtain explicit answers to: Which GIMP generation and OS are targeted? Is legacy Python 2.7/Python-Fu genuinely available? Is the intended result a GIMP menu or only local HTTP liveness? Does the installed application have a supported launcher? What active loopback port does the operator report? Who supplies and verifies weights? Is a provider authorized? If any answer is unknown, keep the verdict static-only or blocked and document the gap.

## Evidence and provenance — not runtime instructions

Historical artifact names including `config.json`, `service.py`, `GIMPML.py`, `update.py`, and `syncWeights.py` explain port mutability, platform dependency, and update risks. They are evidence/warnings only; do not locate, inspect, open, run, import, or adapt them while troubleshooting.
