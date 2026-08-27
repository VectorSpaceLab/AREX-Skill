# Download Workflows

This reference is for safe artifact acquisition from a user-supplied PINTO_model_zoo checkout folder. It is self-contained: use the bundled catalog and bundled helpers, not external source documentation, when planning an acquisition step.

## Inputs to establish

Record these before inspecting or running anything:

- Selected model folder, such as `320_your_model_name`, supplied by the user or chosen from the bundled catalog.
- Requested artifact family or backend: ONNX, TFLite, TensorFlow SavedModel, OpenVINO, CoreML, TFJS, TF-TRT, EdgeTPU, FP32, FP16, INT8, DQ, TPU, WQ, or another folder-specific target.
- Intended use: local experiment, benchmark, redistribution, publication, product integration, or conversion input.
- Network policy: offline only, dry-run only, or approved download.
- Storage budget and whether archive extraction is allowed.
- Credential state if a script points to a protected or quota-limited service.

If any of these affect safety and remain unknown, stop at a plan instead of running commands.

## License gate

Model licenses may differ folder by folder. Do this before use or redistribution:

1. Inspect license-like files in the selected folder: `LICENSE`, `LICENSE.txt`, `NOTICE`, `COPYING`, `README`, or similarly named local files.
2. Separate script/conversion code permissions from upstream model weights, datasets, checkpoints, pretrained weights, and exported artifacts.
3. For redistribution or product use, require a positive license grant for the exact artifact, not just a permissive repository-level code license.
4. If there is no clear license file or the license conflicts with the user's intended use, mark license status as `unresolved` or `blocked` and do not download for redistribution.

## Dry-run every download script

The bundled helper parses shell text only. It does not run shell, network, archive, or cleanup commands.

From the sub-skill directory:

```bash
python scripts/inspect_download_plan.py <selected-model-folder> --json
```

For one script:

```bash
python scripts/inspect_download_plan.py <selected-model-folder>/download.sh --json
```

For nested acquisition scripts when the user explicitly asks to inspect them too:

```bash
python scripts/inspect_download_plan.py <selected-model-folder> --recursive --json
```

Interpret the output as a plan, not proof that the resource is reachable:

- `google_drive_file_ids`: likely Drive IDs or file-id variables found in the script.
- `output_files`: explicit filenames supplied to `curl -o` or equivalent output flags.
- `contains_network_command`: the script appears to call a network-capable tool or URL.
- `cookie_or_confirmation_flow`: the script may depend on cookies, confirmation tokens, or quota-sensitive Drive behavior.
- `archive_or_cleanup_signals`: the script appears to extract, remove, move, copy, or otherwise mutate files after download.
- `warnings`: reviewer prompts that must be resolved before execution.

The parser cannot guarantee all files written by archive extraction. If an archive is downloaded, assume extraction may create many files and may overwrite existing names unless separately inspected.

## Decide whether to run a download

Only propose a network command when all are true:

- The user approved network access for this exact folder/script.
- The user approved the named host or service and any cookies/credentials involved.
- Free storage is enough for the archive plus extracted artifacts.
- The selected script matches the requested artifact family.
- The license gate is acceptable for the user's intended use.
- The script has no unreviewed destructive command that could affect files outside the selected folder.

Prefer running from inside the selected model folder so relative paths match the script's assumptions. Avoid broad shell execution from a repository root unless the script explicitly requires it.

## Safe execution template

Use this only after approval and review. Replace placeholders with user-supplied paths; do not invent a folder.

```bash
cd <selected-model-folder>
bash ./download.sh
```

For folders with multiple scripts, choose the specific script whose dry-run outputs match the requested target:

```bash
cd <selected-model-folder>
bash ./download_<variant>.sh
```

Do not pipe remote content into a shell. Do not add credentials to a command shown in chat. If a credentialed URL or cookie is required, ask the user how they want to provide it and keep it out of persistent logs where possible.

## Folder inspection after or instead of download

Use the root skill's folder checker when the user asks whether artifacts are already present or whether a download succeeded. From this sub-skill directory, the root checker is addressed as:

```bash
python ../../scripts/check_model_folder.py <selected-model-folder>
```

If the root checker exposes backend filters, use the requested backend or format. Otherwise, inspect expected file families manually:

| Requested family | Typical required evidence |
|---|---|
| ONNX | one or more `.onnx` files; optional external data files if the model uses split weights |
| TensorFlow Lite | one or more `.tflite` files; `_edgetpu.tflite` indicates EdgeTPU-oriented output |
| TensorFlow SavedModel | `saved_model.pb` plus a `variables/` directory when variables are not frozen |
| OpenVINO | paired `.xml` and `.bin` files with matching basenames |
| CoreML | `.mlmodel` or `.mlpackage` artifacts |
| TFJS | `model.json` plus shard files such as `.bin` weights |
| TF-TRT | SavedModel-like export or TensorRT engine artifacts depending on the folder |
| Archives | downloaded `.tar.gz`, `.tgz`, `.zip`, `.7z`, or similar files before extraction |

A listed catalog format is a selection signal, not proof that the local checkout currently contains the artifact. Downloads may still be required.

## Reporting template

When answering an acquisition request, include:

```text
Selected folder: <relative folder>
Requested artifacts: <format/backend>
License status: <acceptable|unresolved|blocked> after checking <files>
Dry-run scripts: <script names>
Likely remote IDs/hosts: <Drive IDs or non-Drive hosts>
Explicit output files: <filenames from -o>
Mutation signals: <archive extraction, cleanup, overwrites, cookies>
Network approval: <approved|not approved|required>
Storage/credentials: <ok|missing|unknown>
Folder check: <present/missing files or not run>
Safe next step: <run exact script | stop and ask | route to another sub-skill>
```

## Stop conditions

Stop and ask or return a blocked diagnosis when any of these hold:

- Network access is not approved.
- A Google Drive or protected-resource download needs confirmation, cookies, credentials, or quota that the user cannot provide.
- The script's expected output does not match the requested backend/artifact.
- The requested backend is not listed for the selected catalog entry and no folder artifact proves it exists.
- Per-folder license is missing, unclear, or incompatible with the intended use.
- Storage is insufficient for archives and extracted outputs.
- The script contains unreviewed destructive commands, path traversal, or writes outside the selected folder.
