# Troubleshooting

## Purpose

Read this first when Opyrator imports fail, the CLI entry point is missing, the API or UI stack uses the wrong package versions, or a workflow fails before you reach the narrower sub-skill.

## Verified compatibility stack for this snapshot

The verified working environment for this repository snapshot used:

- Python 3.8
- `pydantic<2`
- `fastapi==0.63.0`
- `starlette==0.13.6`
- `streamlit==0.72.0`
- `protobuf==3.20.3`
- `altair<5`
- `pandas<2`
- `numpy<2`
- `plotly`
- `loguru`
- `uvicorn<0.24`

If those versions drift too far, import-time failures are common.

Run the safe smoke helper first when you are unsure whether the install is healthy:

```bash
python scripts/check_install.py --json
```

## Cross-cutting failure map

| Signal | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'opyrator'` | The package is not installed in the active environment. | Install the legacy-compatible stack, then rerun `python scripts/check_install.py --json`. |
| `ImportError: cannot import name 'graphql' from starlette` or `ModuleNotFoundError: starlette.graphql` | The API stack is newer than the snapshot expects. | Pin `fastapi==0.63.0` and `starlette==0.13.6`, then recheck the API smoke. |
| protobuf descriptor errors while importing `opyrator.ui.streamlit_ui` | `streamlit` is paired with a protobuf release that is too new for the generated protos in this snapshot. | Pin `protobuf==3.20.3` and `streamlit==0.72.0`, then rerun the UI smoke. |
| `opyrator` command is missing | The console script was not installed or the environment was not activated correctly. | Reinstall the package, then rerun `opyrator --help` or `scripts/check_install.py`. |
| A wrapped callable is rejected before service creation | The callable contract is invalid. | Route to [`sub-skills/wrapping-and-cli/SKILL.md`](../sub-skills/wrapping-and-cli/SKILL.md). |
| `launch-api` / OpenAPI / docs routes fail | The FastAPI service stack or `patch_fastapi` behavior is the issue. | Route to [`sub-skills/api-services/SKILL.md`](../sub-skills/api-services/SKILL.md). |
| Streamlit widgets, `FileContent`, or custom renderers fail | The schema/UI layer or optional UI dependencies are the issue. | Route to [`sub-skills/ui-and-components/SKILL.md`](../sub-skills/ui-and-components/SKILL.md). |

## What to do before changing code

1. Re-run `python scripts/check_install.py --json`.
2. Confirm the installed stack matches the compatibility block above.
3. Check the command you actually need with `opyrator --help`.
4. Only then move into the narrower sub-skill.

## When to stop and ask for more context

Stop and ask if:

- the user wants a newer package version than this snapshot verifies,
- the environment cannot install the legacy UI stack,
- or a required example dependency is missing and the user wants that example verified.

## Optional example dependencies

These are not required for the core package smoke, but they are needed for some repo examples:

- `spacy` and `st-annotated-text` for the named-entity example
- `ISR` for image super-resolution
- `spleeter` and `ffmpeg` for audio separation
- `fasttext` for language detection and word-vector demos
- `nltk` for text preprocessing

Keep them out of the base install unless the task specifically asks for those examples.
