---
name: model-acquisition
description: "Plan safe artifact acquisition and inspect selected
  PINTO_model_zoo model folders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Acquisition

Use this sub-skill when a user asks how to obtain, inspect, or validate artifacts for a selected PINTO_model_zoo model folder.

## Route here for

- Planning or dry-running `download*.sh` in a selected model folder.
- Answering whether a download script is safe to run, what it is likely to fetch, and which explicit output files it writes.
- Diagnosing Google Drive confirmation, quota, cookie, credential, proxy, or partial-download failures.
- Checking whether a selected folder has the expected artifacts for ONNX, TensorFlow Lite, OpenVINO, CoreML, TFJS, TensorFlow, EdgeTPU, or other listed formats.
- Reviewing per-folder license constraints before use, copying, publishing, or redistribution.

Do not use this sub-skill to run demos, convert models, quantize models, or prove a backend runtime. Route those follow-up tasks to the inference or conversion/deployment sub-skills after acquisition is understood.

## Required safety gate

Before running any user checkout script or command that reaches the network:

1. Confirm the exact selected model folder and requested backend/artifact family.
2. Review any per-folder `LICENSE`, `NOTICE`, or model-specific license text in the selected folder. Treat license absence as unresolved for redistribution.
3. Dry-run every candidate `download*.sh` with the bundled helper:
   - `python scripts/inspect_download_plan.py <selected-model-folder> --json`
   - or, for one script: `python scripts/inspect_download_plan.py <selected-model-folder>/download.sh --json`
4. Explain network hosts, likely Google Drive IDs, explicit `-o` outputs, cookie/confirmation behavior, archive extraction or cleanup risk, and expected storage impact.
5. Ask for explicit user approval before any network execution. Keep credentials, cookies, and downloaded artifacts out of commits unless the user explicitly instructs otherwise.

Stop instead of executing if approval is missing, credentials are required but unavailable, free storage is insufficient, the requested backend is unsupported by the selected folder, or the license does not allow the intended use.

## Bundled resources

- `scripts/inspect_download_plan.py` parses a selected `download*.sh` file or a directory containing such scripts without executing shell or network commands.
- `references/download-workflows.md` gives the safe acquisition workflow, dry-run interpretation, and folder inspection handoff.
- `references/troubleshooting.md` covers common acquisition and artifact-validation failures.
- The root skill's `references/model-catalog.json` is the self-contained catalog for choosing candidate folders and listed format flags.
- The root skill's `scripts/check_model_folder.py` is the folder/artifact inspection helper. From this sub-skill directory it is addressed as `../../scripts/check_model_folder.py` when present.

## Operating pattern

1. Use the bundled catalog to narrow the model directory and format flag when the user has not already selected a folder.
2. Treat the selected folder as user-supplied checkout content. Inspect only the folder and bundled skill resources needed for the request.
3. Run the dry-run parser before considering execution of any download script.
4. Use the root folder checker after downloads or when the user asks whether required artifacts already exist.
5. Return a plan or diagnosis with clear stop conditions and the next owner: acquisition, inference, conversion/deployment, or user action.

## Handoff fields to include

- Selected model folder and requested artifact/backend family.
- License status: acceptable, unacceptable, or unresolved, with the relative license file names checked.
- Dry-run parser summary: scripts inspected, Google Drive IDs, explicit output filenames, cookie/confirmation signals, archive/cleanup signals, and network warning.
- Folder inspection summary: expected artifact extensions/pairs and files present or missing.
- Approval status for network, credentials, storage, and backend/hardware requirements.
- Safe next command only when all stop conditions are cleared.
