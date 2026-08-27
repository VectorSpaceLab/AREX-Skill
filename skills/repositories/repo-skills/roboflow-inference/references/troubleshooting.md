# Cross-cutting troubleshooting

Use this page to triage a failing Roboflow Inference request before diving into a
specific sub-skill.

## First decision

| Symptom family | Start here |
| --- | --- |
| Server lifecycle, cloud, rf-cloud, enterprise, or CLI help failure | `sub-skills/cli-operations/references/troubleshooting.md` |
| Workflow image or video processing | `sub-skills/workflow-processing/references/troubleshooting.md` |
| Python SDK, WebRTC, or workflow/pipeline HTTP calls | `sub-skills/sdk-webrtc/references/troubleshooting.md` |
| Backend choice, package negotiation, local packages, or cache/offline issues | `sub-skills/model-runtime/references/troubleshooting.md` |

## Common cross-cutting failures

| Symptom | Likely owner | First move | Probe script |
| --- | --- | --- | --- |
| CLI help fails before showing help | `cli-operations` | Repair the CLI environment or Docker dependency tree. | `sub-skills/cli-operations/scripts/inspect_cli_help.py` |
| Workflow command says the local `inference` package is missing | `workflow-processing` | Install the local `inference` package in the command's environment. | `sub-skills/workflow-processing/scripts/inspect_workflow_outputs.py` |
| WebRTC or SDK import fails because `aiortc` / `av` is missing | `sdk-webrtc` | Install the WebRTC extra for `inference-sdk`. | `sub-skills/sdk-webrtc/scripts/check_webrtc_surface.py` |
| Model loading fails because a backend package or environment is missing | `model-runtime` | Inspect the environment and install the matching backend extra. | `sub-skills/model-runtime/scripts/describe_compute_environment.py` |

## Shared recovery rules

- If the issue is really backend selection or package negotiation, switch to
  `model-runtime` instead of guessing a fix in the caller surface.
- If the issue is really workflow image/video processing, switch to
  `workflow-processing` instead of trying to debug it as a generic CLI problem.
- If the issue is really an SDK/WebRTC session or HTTP call, switch to
  `sdk-webrtc` instead of using CLI guidance.
- If the issue is really Docker or server lifecycle, switch to `cli-operations`.

## What to collect before escalating

Capture the smallest reproducible surface for the matching sub-skill:

- the exact command or Python call
- the package family involved
- the active package version, if known
- the first error line
- whether the environment includes Docker, WebRTC extras, or model backend extras

Then move to the owner sub-skill's troubleshooting page and keep the diagnosis
narrow.
