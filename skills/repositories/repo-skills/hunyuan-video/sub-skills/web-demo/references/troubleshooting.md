# Gradio Troubleshooting

## Model root missing

Symptom:

```text
`models_root` not exists: <path>
```

Fix the `--model-base` path and validate it before launching:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base <path>
```

## UI exposed unexpectedly

The source workflow defaults to `SERVER_NAME=0.0.0.0` when the environment variable is absent. The bundled command builder defaults to `127.0.0.1` for safety. Use `0.0.0.0` only when network exposure is intentional.

## Port conflict

If Gradio cannot bind the port, choose another integer port:

```bash
python sub-skills/web-demo/scripts/build_gradio_command.py --server-name 127.0.0.1 --server-port 7861
```

## Negative prompt confusion

The Gradio helper does not expose a negative-prompt UI field and passes an empty string for `negative_prompt`. If the user needs negative-prompt control, use the CLI/API inference route instead.

## Output directory confusion

Gradio-generated MP4 files are saved to `gradio_outputs/` under the server process current working directory, not necessarily to the shared `--save-path` value.

## Generation still requires GPU/checkpoints

A successful Gradio import or server command does not prove generation. Actual button clicks load/use the HunyuanVideo model stack and need CUDA memory plus complete checkpoints.
