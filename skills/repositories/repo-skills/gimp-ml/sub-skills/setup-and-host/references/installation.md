# Installation and deployment boundary

This document separates the historical deployment recipe from the currently inspectable Python 3 service. It is intentionally procedural but non-destructive: package installation, application launch, service deployment, and model acquisition belong to an administrator on a compatible host.

## 1. Select a path before installing anything

| Requirement | Legacy plug-in path | Newer installed service path |
|---|---|---|
| GIMP menu/PDB integration | Required; targets GIMP 2.10 Python-Fu | Not supplied by the HTTP service alone |
| Interpreter assumption | GIMP's Python 2.7 bridge plus `gimpfu`; historical environments are Python 2.7-specific | Python 3 service-core environment managed by the installed application/operator |
| Service boundary | Not applicable | Local HTTP service with GET `/status`; model routes require separate authorization and assets |
| Model location | External sibling `weights/` under the installed plug-in root | Model/provider-specific; do not assume weights or credentials |
| Current verification status | Blocked on the inspected host: GIMP and Python 2.7 are unavailable | FastAPI application import and route declaration inspection passed in the isolated Python 3.11 environment; live bind, launcher behavior, and inference are unverified |
| Platform GUI packages | Not needed for static legacy checks, but GIMP/Python-Fu remain required for execution | PyQt6, PyQt6-WebEngine, and pywin32 were not installed or verified; do not claim launcher support from the service-core check |
| GIMP 3 status | Not established | Do not infer compatibility from the service |

Choose exactly one path for a test. Do not mix a Python 2 legacy plug-in tree with a Python 3 service environment and call that a supported installation.

## 2. Historical legacy layout

The historical installation evidence describes this shape:

```text
<installed-plugin-root>/
  *.py and plugin subdirectories
  gimpenv/                 # historical Python 2.7 environment
  weights/                 # externally supplied model files
```

The historical manual recipe describes Python 2.7, old package versions, a GIMP plug-in search path, executable entry files, and a separately supplied `weights/` tree. Those details establish the legacy contract; they are not a recommendation to install end-of-life Python 2 on a modern machine. The current checked host cannot validate that recipe. A Python 3.11 environment is not a drop-in replacement for embedded `gimpfu`.

### Safe preflight checks

Run only on an explicitly supplied installed/candidate deployment; these are presence/version checks, not proof of plug-in execution:

```bash
python2 --version 2>/dev/null || true
python3 --version
command -v gimp || true
test -d <plugin-root> && echo "plugin root exists" || echo "plugin root missing"
test -d <plugin-root>/gimpenv && echo "legacy env present" || echo "legacy env missing"
test -d <plugin-root>/weights && echo "weights directory present" || echo "weights directory missing"
```

Do not use a shell alias to make `python` mean Python 2 for all future work. If an administrator continues with the legacy path, use an isolated, disposable deployment and follow the host's package and GIMP policy.

## 3. Discovery and import in GIMP 2.10

The historical documentation directs an administrator to:

1. Open GIMP 2.10 manually.
2. Open Preferences → Folders → Plug-ins.
3. Add the explicitly supplied directory containing the legacy entry files and its external `weights/` tree.
4. Close and restart GIMP.
5. Look for the procedures reported by the static registration scan.

This is a manual host action. No automated agent should launch GIMP or claim that a menu appeared. If a procedure is missing, run the bundled registration scan against the supplied deployment, then check GIMP's plug-in search path and executable/read permissions. A correct static `register()` call can still fail before registration because the host bridge, package, external module, or weight file is unavailable.

## 4. Service lifecycle and liveness

The service path is deployment-specific. If the installed GIMP-ML application provides a supported launcher, the operator should use that launcher and keep its service local-only. Do not start the service by locating or invoking a module from an original source checkout, and do not substitute a guessed command-line application-server invocation.

After the installed application/operator confirms that a service is already running, obtain its active loopback port from that operator or the installed application's own status UI. From the root of this generated skill, validate only the safe liveness endpoint:

```bash
python3 scripts/check_service_status.py --port <active-port>
```

The helper performs one GET `/status` to `127.0.0.1:<active-port>`, disables environment proxies, validates the JSON response, and does not start, stop, import, or configure the service. A successful response proves only process/route availability. Do not call model-affecting POST routes without an explicit model, data, provider, credential, and resource plan. No provider request, weight download, GPU success, or image result is implied.

If no supported launcher/operator procedure is available, or the active port cannot be obtained, classify service startup/liveness as `blocked: deployment-specific service startup` rather than inventing a source-checkout command.

## 5. Permissions and refresh safety

Check before changing permissions:

```bash
find <plugin-root> -maxdepth 1 -type f -name '*.py' -printf '%M %p\n'
find <plugin-root>/weights -maxdepth 2 -type f -printf '%M %p\n' 2>/dev/null || true
```

If an administrator needs executable entry files for a compatible GIMP 2.10 installation, apply the narrowest reviewed change to a copied deployment after checking ownership and policy. Do not run a broad recursive chmod and do not alter model file contents.

For a safe refresh, copy the deployment, record a file manifest and configuration separately, compare the reviewed installation package, preserve `weights/` and environment directories, and replace only approved files. Re-run the bundled static checks after comparison. Do not allow an unreviewed network updater to overwrite a working deployment, credentials, local settings, or model assets.

## Evidence and provenance — not runtime instructions

Historical source artifacts consulted for this boundary included `service.py`, `config.json`, `GIMPML.py`, `installGimpML.sh`, `update.py`, and `syncWeights.py`. They support the claims about route shape, launcher-selected ports, platform-only dependencies, and destructive refresh risk. Their names are evidence/warnings only; agents must not locate, open, run, import, or adapt them as part of setup.
