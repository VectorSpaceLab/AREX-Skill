# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `xturing chat` says the model name/path is not valid | The value is neither a known model key nor a model directory that xTuring can load | Use a registered model key or a saved xTuring model directory containing `xturing.json` |
| `xturing api` says the model path is not valid | The path is not a directory | Point `-m` at a saved model directory |
| `/v1/models` or the OpenAI-compatible routes return 503 | No model is loaded in the API process | Start the server with `xturing api -m <model_dir>` and keep that process running |
| `messages must not be empty` | Chat payload has no messages | Send at least one message object |
| HTTP 400 about `n` | The server only supports one completion per request | Use `n=1` |
| Streaming looks like one big chunk instead of tokens | This implementation emits a streaming skeleton, not token-level deltas | Treat streaming as compatibility shape only |
| The Gradio prompt box stays disabled | The model has not been loaded in the UI | Load a valid model path first |
| The UI says `Enter a valid prompt` | The prompt textbox is empty | Type a prompt and submit again |
| The UI load step fails | The path does not point to a valid saved model | Use a directory with `xturing.json` |
| The server does not start | Port `5000` is already in use | Free the port or launch the app with your own Uvicorn settings |
| The UI needs a different model choice flow | The public UI currently exposes path-based loading only | Use the path textbox or instantiate the playground in Python with `model_path=...` |

## Quick fixes

- Use the API server for non-interactive automation.
- Use `xturing chat` only when a terminal prompt loop is acceptable.
- Use `xturing ui` only when you want the Gradio app and can load the model in the browser session.
- If a response shape is wrong, verify that the model is loaded and that the request uses the expected route family (`/api` versus `/v1/*`).
