# Model Acquisition Troubleshooting

Use this reference for acquisition failures, unsafe download-script questions, and missing-artifact checks in a user-supplied model folder.

## Quick triage

1. Confirm the selected folder and requested artifact family.
2. Check per-folder license files before use or redistribution.
3. Run `python scripts/inspect_download_plan.py <selected-model-folder> --json` from this sub-skill directory.
4. If artifacts are expected to exist locally, run the root folder checker: `python ../../scripts/check_model_folder.py <selected-model-folder>`.
5. Decide whether the owner is acquisition, backend runtime setup, inference, conversion/deployment, or user-provided credentials/storage.

## Common failures

| Symptom | Likely cause | What to do | Stop condition |
|---|---|---|---|
| User asks if `download.sh` is safe on CI | Script may reach the network, create cookies, extract archives, or remove downloaded archives | Dry-run with `inspect_download_plan.py`; report explicit outputs, Drive IDs, mutation signals, and host/network requirements; recommend a CI artifact cache only after approval | No network approval, unknown license, unknown storage, or script writes outside selected folder |
| Google Drive downloads an HTML page instead of an archive/model | Drive confirmation token, quota page, virus-scan warning, or login wall | Treat output as failed; inspect file type and size; rerun only with user-approved confirmation/cookie flow or ask user to supply artifact manually | Quota exceeded, credentials unavailable, or the service requires interactive login |
| `cookie` or similar file appears | Script uses a Drive cookie jar for confirmation | Keep cookies local and out of version control; delete when no longer needed if the user approves cleanup | Cookie contains sensitive account/session data or cleanup target is unclear |
| Download is `403`, `404`, or permission denied | Link expired, access restricted, quota exceeded, or blocked by proxy | Verify the dry-run IDs/hosts; ask user to confirm access or provide a mirror/artifact | Protected resource cannot be accessed with available credentials |
| Script succeeds but expected backend file is missing | Wrong variant script, archive extraction failed, artifact name differs, or catalog flag was only a remote availability signal | Compare parser `output_files` with folder checker output; inspect archive contents before extraction when possible; choose another `download_*.sh` variant if names match better | Requested backend/artifact is not produced by any reviewed script |
| Multiple `download_*.sh` scripts exist | Folder has model-size, postprocess, precision, or dataset variants | Parse all scripts, compare output names and Drive IDs, choose only the variant matching the user's target | Variant cannot be identified from outputs and user cannot choose |
| Archive extraction fails | Partial download, wrong file type, no space, missing extractor, corrupt archive | Check file type, size, and checksum if provided; re-download only after approval; install extractor only if user allows | Storage or extractor unavailable; downloaded file is an HTML/error page |
| Disk fills during extraction | Archive expands to many or large files | Estimate archive plus extraction size; use `df -h` or user-provided storage budget; clean only user-approved files | Free space is below requested budget or cleanup would remove unreviewed files |
| Output file overwritten | Script writes fixed `-o` names such as `resources.tar.gz`, `saved_model.tar.gz`, or `checkpoint.tar.gz` | Run in the selected folder; back up or rename existing files if user approves; avoid running two variants in the same folder without a plan | Existing artifacts would be overwritten without approval |
| Requested ONNX/TFLite/OpenVINO/CoreML/TFJS artifact absent | The selected folder does not list or provide that backend locally | Use catalog format flags for selection and root folder checker for local evidence; route conversion requests to conversion/deployment if source artifacts are available | Backend unsupported and conversion is not requested or cannot be prepared |
| OpenVINO checker reports incomplete files | `.xml` and `.bin` pair is missing or basenames differ | Reacquire the matching pair or choose a script whose outputs include both; do not treat `.xml` alone as a complete IR model | Matching pair cannot be found |
| EdgeTPU file requested but only regular TFLite exists | TPU/EdgeTPU artifact is separate from ordinary TFLite, or compiler step was not run | Look for `_edgetpu.tflite` or similar; if absent, route to conversion/deployment and require EdgeTPU compiler/hardware policy | User needs verified EdgeTPU execution but compiler/hardware is unavailable |
| License file is missing or ambiguous | Upstream model/license not included with artifact script | Mark redistribution blocked or unresolved; ask user for source/license evidence | Intended use requires a license grant and none is available |
| Script references non-Drive host | Many folders use object storage or other hosts instead of Drive | Parser still reports explicit `-o` outputs and network warning; ask approval for that host and check storage | Host is not approved or blocked by network policy |
| Shell parser finds no `-o` output | Script may use implicit filenames, variables, `wget -O`, Python helpers, or extraction-only commands | Inspect the script text manually as untrusted shell; do not assume no writes | Cannot explain writes well enough for user approval |

## Google Drive-specific guidance

Google Drive acquisition scripts often use a two-step confirmation pattern: first request a confirmation page with a cookie jar, then send a second request containing a confirmation token. Failures are common and should not be treated as model-format failures.

Check for these signals in the dry-run output or script text:

- `drive.google.com` URLs.
- `fileid=...`, `id=...`, or a long Drive-like ID.
- `confirm=` token parsing.
- `cookie`, `-c`, `-b`, `--cookie`, or `--cookie-jar`.
- A small downloaded file whose contents are HTML instead of the expected archive/model.

Recovery options:

1. Retry only after the user approves network and cookie handling.
2. If quota is exceeded, wait, use a user-approved mirror, or ask the user to manually place the artifact in the folder.
3. If credentials are required, ask how the user wants to provide access; do not print secrets in commands.
4. After manual placement, use the root folder checker rather than rerunning the download script.

## Artifact-family checks

Use these checks when the user asks whether the folder has the model artifacts they need:

- ONNX: at least one `.onnx` file; for large external-data models, also check adjacent weight/data files named by the model.
- TensorFlow Lite: `.tflite` files; distinguish regular, FP16, INT8, dynamic range, weight-quantized, and EdgeTPU-named variants when filenames reveal them.
- TensorFlow SavedModel: `saved_model.pb` plus `variables/`, unless the folder specifically uses a frozen graph.
- OpenVINO: matching `.xml` and `.bin` pair.
- CoreML: `.mlmodel` or `.mlpackage`.
- TFJS: `model.json` and weight shards.
- TF-TRT/TensorRT: folder-specific SavedModel or engine artifacts; backend proof requires the deployment sub-skill and suitable runtime.

A local artifact check proves presence, not numerical correctness or backend execution. Route runtime proof to the inference or conversion/deployment sub-skill.

## When to ask the user

Ask a short clarification instead of guessing when:

- More than one `download_*.sh` variant could satisfy the request.
- The requested backend is not stated.
- Network approval, credentials, or storage budget is unknown.
- The intended use involves redistribution and license status is unclear.
- The user expects hardware-specific proof such as EdgeTPU, GPU, OpenVINO device plugin, TF-TRT, camera, or Raspberry Pi behavior.

## Safe final wording

Prefer conclusions like:

- `Dry-run only: this script would contact Google Drive, write checkpoint.tar.gz, and use a cookie confirmation flow. It is not safe for unattended CI until network, cookie, quota, and storage are approved.`
- `The folder has an ONNX file locally, but no OpenVINO .xml/.bin pair. Acquisition can fetch other artifacts only if network is approved; conversion is a separate task.`
- `License is unresolved for redistribution because no folder-level model license was found. Local inspection can continue, but publication or redistribution should stop until the user supplies license evidence.`
