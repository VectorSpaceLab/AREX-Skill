# Cross-Cutting Troubleshooting

## Purpose

Read this when the failure spans install, imports, optional dependencies, plugins, cloud services, MCP serving, or system tools. For workflow-specific failures, follow the nearest sub-skill troubleshooting reference.

## Install Or Import Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'markitdown'` | Core package is not installed in the active Python environment. | Install `markitdown` or run `python scripts/check_markitdown_environment.py --check-cli` from this skill directory to confirm the active interpreter. |
| `MissingDependencyException` mentions a converter/feature | The core package is installed without the needed optional extra. | Install the specific extra from `references/package-overview.md`, such as `markitdown[pdf]`, `markitdown[docx]`, or `markitdown[az-content-understanding]`. |
| `pip check` reports dependency conflicts | Mixed optional extras or plugin packages pulled incompatible versions. | Create a fresh environment, install the smallest needed extras, then add plugins one at a time. |
| Audio conversion warns that `ffmpeg` or `avconv` is missing | Python package import works, but a system audio binary is absent. | Install a system `ffmpeg` package or avoid audio workflows. Do not treat Python import success as proof of audio transcription readiness. |

## CLI Or API Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Stdin conversion produces poor output or unsupported format | Bytes lack filename, extension, MIME type, or charset hints. | Use CLI `--extension`, `--mime-type`, `--charset`, or Python `StreamInfo`. |
| Markdown output contains huge embedded data | `--keep-data-uris` or `keep_data_uris=True` preserved base64 payloads. | Disable data URI preservation unless the downstream consumer explicitly requires it. |
| `UnsupportedFormatException` | No converter accepted the stream info/content. | Check whether a format extra or plugin is missing; otherwise use a different extraction tool. |
| `FileConversionException` | A converter accepted the input but failed during conversion. | Inspect the converter-specific cause; if optional dependencies or system tools are involved, install only that workflow’s requirements. |

## Plugin Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `markitdown --list-plugins` does not show a plugin | Plugin is not installed in the active environment or entry point group is wrong. | Read `sub-skills/plugin-development/SKILL.md` and run its `scripts/check_plugin_package.py`. |
| Plugin appears but conversion ignores it | Plugins are disabled, converter priority is too low, or `accepts` rejects/consumes the stream. | Use CLI `--use-plugins` or `MarkItDown(enable_plugins=True)` and inspect priority/stream handling. |
| OCR plugin loads but OCR blocks are missing | `llm_client` or `llm_model` is missing, unsupported embedded image path, or per-image API failure. | Read `sub-skills/ocr-plugin/references/troubleshooting.md` and run `sub-skills/ocr-plugin/scripts/check_ocr_plugin.py`. |

## Cloud And Credential Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--use-docintel` or `--use-cu` exits before conversion | Required endpoint or filename is missing, or cloud modes are combined. | Run `sub-skills/cloud-integrations/scripts/check_cloud_configuration.py` and fix parser-level flags before checking credentials. |
| Azure SDK import fails | Cloud optional extra is not installed. | Install `markitdown[az-doc-intel]`, `markitdown[az-content-understanding]`, or `markitdown[all]` as appropriate. |
| Authentication or authorization fails | Endpoint, API key, identity, tenant, or role is wrong. | Do not embed credentials in code; pass explicit credential objects or configure environment/managed identity according to the user’s deployment policy. |
| Unexpected files are sent to cloud conversion | Cloud route was too broad. | Restrict Content Understanding with `--cu-file-types` or `cu_file_types`, or use local conversion for sensitive formats. |

## MCP Server Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `markitdown-mcp --host ...` errors | Host/port flags require HTTP/SSE mode. | Use `markitdown-mcp --http --host 127.0.0.1 --port 3001` or omit host/port for STDIO. |
| Security warning on non-localhost bind | Server has no authentication and can read files/network as its process user. | Prefer STDIO or loopback; if exposure is deliberate, sandbox the process and limit file permissions. |
| MCP cannot read a local file in Docker | URI points to host path not mounted in the container. | Mount the directory and use the container-visible `file:` URI. Prefer read-only mounts. |
| MCP plugins do not run | Plugin package is not installed in the server environment or `MARKITDOWN_ENABLE_PLUGINS` is false. | Install plugin packages in the server image/environment and set `MARKITDOWN_ENABLE_PLUGINS=true` deliberately. |

## Safe Diagnosis Order

1. Run the shared checker: `python scripts/check_markitdown_environment.py --check-cli --list-plugins`.
2. Route to the nearest sub-skill based on the failing workflow.
3. Run that sub-skill’s bundled checker before making network, cloud, OCR, Docker, or server calls.
4. Install only the missing extra/package or system tool indicated by the error.
5. Ask the user before running commands that fetch remote URIs, call Azure/LLM services, start a persistent server, or expose local files.
