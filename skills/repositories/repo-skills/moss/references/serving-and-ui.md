# MOSS serving and UI summary

## Purpose

Read this when deciding how MOSS should be exposed as an API or browser UI.
For detailed service workflow steps and troubleshooting, route to
[../sub-skills/serving/SKILL.md](../sub-skills/serving/SKILL.md).

## Service surfaces

| Surface | Best for | State behavior | Heavy prerequisites |
| --- | --- | --- | --- |
| FastAPI-style POST service | Programmatic calls from another app or test client. | Conversation state keyed by `uid` in process memory. | Model checkpoint, CUDA/memory, FastAPI/Uvicorn. |
| Gradio chat UI | Local browser chat demo with simple sliders. | UI session state stores chat history. | Model checkpoint, CUDA/memory, Gradio/mdtex2html. |
| Streamlit chat UI | Local app with sidebar controls and session history. | `st.session_state` stores history and prompt prefix. | Model checkpoint, CUDA/memory, Streamlit. |

## FastAPI request schema

The MOSS API shape uses POST `/` with:

```json
{
  "prompt": "Hello MOSS",
  "uid": "optional-existing-conversation-id",
  "max_length": 2048,
  "top_p": 0.8,
  "temperature": 0.7
}
```

The response shape includes:

```json
{
  "response": "decoded model response",
  "history": [["prompt", "response"]],
  "status": 200,
  "time": "server timestamp",
  "uid": "conversation id"
}
```

Use [../sub-skills/serving/scripts/moss_request_template.py](../sub-skills/serving/scripts/moss_request_template.py)
to create a payload and curl snippet without contacting a server.

## Bundled service template

Use the bundled template for a self-contained dry-run or an explicit service
launch:

```bash
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --json
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --serve
```

The first command prints the plan and schema. The second command is heavyweight:
it loads a MOSS checkpoint, uses CUDA, and starts Uvicorn. Confirm network,
cache, GPU memory, port, and exposure policy before using `--serve`.

## UI controls

Common UI controls from the source evidence include:

- `max_length` or maximum response length;
- `top_p`;
- `temperature`;
- `length_penalty` and `repetition_penalty` in the Streamlit-style path;
- clear-history actions;
- Markdown/LaTeX rendering through `mdtex2html` in Gradio-style rendering;
- `<eom>` stop criteria in Streamlit-style generation.

## Deployment cautions

- Avoid multiple service workers unless each worker can load its own model copy.
- Bind to `127.0.0.1` for local testing; bind to `0.0.0.0` only when external
  access is intentional.
- Preserve `uid` only for conversations that should share history.
- Keep model license and data/privacy constraints explicit before public
  exposure.
