# MOSS serving and UI workflows

## Purpose

Read this when planning a MOSS FastAPI service, browser UI, or safe request
payload. Full services load a MOSS checkpoint; this reference separates request
and UI mechanics from heavyweight model execution.

## FastAPI demo behavior

The API demo exposes `POST /` and maintains a process-local `history_mp` map by
`uid`. Request fields:

| Field | Required | Default in source | Meaning |
| --- | --- | --- | --- |
| `prompt` | yes | none | User message appended as `<|Human|>: ...<eoh>`. |
| `uid` | no | generated UUID | Conversation id used to recover history. |
| `max_length` | no | 2048 | Passed to `model.generate(max_length=...)`. |
| `top_p` | no | 0.8 | Nucleus sampling. |
| `temperature` | no | 0.7 | Sampling temperature. |

Response fields:

| Field | Meaning |
| --- | --- |
| `response` | New decoded MOSS response. |
| `history` | List of `(query, response)` pairs stored for the uid. |
| `status` | Source returns `200` on success. |
| `time` | Server-side timestamp string. |
| `uid` | Existing or generated conversation id. |

The bundled dry-run-first service template mirrors that request behavior:

```bash
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --json
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --serve
```

The first command is safe and prints the plan. The second command starts Uvicorn,
loads the model at startup, and can download checkpoints and allocate GPU
memory before the endpoint is useful. The default bundled host is `127.0.0.1`;
choose `0.0.0.0` only when external network exposure is intentional.

## Safe request payload generation

Use the bundled helper before contacting a server:

```bash
python sub-skills/serving/scripts/moss_request_template.py \
  --prompt "Hello MOSS" --max-length 512 --top-p 0.8 --temperature 0.7 --curl
```

It validates field ranges, prints JSON, and optionally prints a curl snippet.
It does not send the request.

## Gradio demo behavior

The Gradio demo:

- exposes a `gr.Chatbot` plus a large text input;
- uses `max_length`, `top_p`, and `temperature` sliders;
- keeps `(message, response)` history in `gr.State`;
- overrides chatbot postprocessing to render Markdown/LaTeX through
  `mdtex2html`;
- calls `demo.queue().launch(share=False, inbrowser=True)`.

Use this when the user wants a local browser chat surface. It still loads the
selected checkpoint before the app is responsive.

## Streamlit demo behavior

The Streamlit demo:

- sets page title/icon/layout;
- has sidebar controls for `temperature`, `max_length`, `length_penalty`,
  `repetition_penalty`, and `max_time`;
- caches the loaded model with `@st.cache_resource`;
- stores chat history and prompt prefix in `st.session_state`;
- uses `StopWordsCriteria(tokenizer.encode("<eom>", add_special_tokens=False))`
  to stop generation.

Use this when the task asks for a simple local app with sidebar parameters or
Streamlit-specific deployment.

## Service planning checklist

Before launching any service:

1. Choose checkpoint precision and GPUs using the inference/model-runtime
   sub-skills.
2. Confirm dependency imports: `fastapi`, `uvicorn`, `gradio`, `streamlit`,
   `mdtex2html`, `torch`, `transformers`, `accelerate`, and Hugging Face hub as
   relevant.
3. Confirm checkpoint cache/network and model licenses.
4. Reserve a port and decide whether binding `0.0.0.0` is acceptable.
5. Prepare a small request payload and expected response shape.
6. Keep `uid` for continued API conversations; drop it for a fresh conversation.
