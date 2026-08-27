# Cross-cutting troubleshooting

Read this before changing dependencies, downloading assets, exposing a local
service, or deciding that a plugin failure is a model failure.

| Symptom | Likely boundary | Safe next step | Stop condition |
|---|---|---|---|
| `No module named gimpfu`, no PDB, or no menu | GIMP 2/Python-Fu host | Use `sub-skills/setup-and-host/scripts/check_plugin_registrations.py` for static evidence and verify a compatible GIMP 2.10 host independently | Do not install random Python 3 packages or claim GIMP 3 compatibility |
| Plugin appears but model operation fails | External weights or model dependency | Run `vision-filters/scripts/check_model_assets.py` or setup layout checker against an operator-supplied asset root | Missing/unreadable checkpoints block inference; do not auto-download |
| Layer-size/channel error | Input contract | Use the classical array validator or guided mask validator, then apply the nearest workflow's alignment rules | Do not silently resize or invert a mask |
| CUDA is visible but inference fails/OOMs | Backend capacity, not importability | Run the no-allocation Torch probe; use explicit Force CPU only where the model and weights support it | Do not present a CPU import or CUDA visibility as native model success |
| FastAPI service will not answer `/status` | Launcher, port, bind, or dependency problem | Inspect an operator-provided local config with the service helper and probe only a loopback URL | No launcher/running process or non-loopback endpoint means blocked; do not start source code or expose the service |
| `/run_inference` rejects payload | Route or raw-byte protocol | Validate base64, shape, and byte count with the bundled payload checker; confirm a load request used the same pipeline | Do not send credentials or retry provider calls blindly |
| Provider returns auth/quota/network/image URL error | External OpenAI boundary | Redact secrets, classify the exact response, and ask the operator to verify their own credentials/quota/network | No credentials or authorization: keep live generation unverified |
| Update wants to delete/replace files | Destructive source updater | Stop; make a reviewed backup and perform an offline, selective refresh | Never run a downloader/updater as a diagnostic or recovery loop |
| Skill seems stale | Source provenance mismatch | Compare the current repo commit, branch, dirty state, entry points, and evidence paths with `references/repo-provenance.md` | Use a refresh workflow before relying on changed behavior |

## Evidence labels

Use `static-only` for source scans and documentation checks, `preflight-pass`
for deterministic input/asset validation, `service-liveness` for a local status
response, `model-unverified` when no checkpoint inference was run, and
`blocked` when a host, device, asset, credential, or launcher is absent. These
labels must not be collapsed into a generic “success.”

## Privacy and side effects

Do not print provider keys, full credential-bearing config, private model URLs,
local environment names, or private checkout paths into a report. Prefer the
bundled read-only helpers. Do not add `--reload`, bind a service to all
interfaces, download weights, launch GIMP, or mutate a live layer unless the
operator separately authorizes that exact action and has a compatible host.
