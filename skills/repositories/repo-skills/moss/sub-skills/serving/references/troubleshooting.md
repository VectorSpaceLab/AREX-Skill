# MOSS serving troubleshooting

## API JSON errors

**Symptoms**: request fails before generation, `prompt` is `None`, or server logs
unexpected JSON values.

**Recovery**

- Ensure the request body is JSON with `Content-Type: application/json`.
- Include a non-empty `prompt` field.
- Keep `max_length` positive and `top_p`/`temperature` between 0 and 1.
- Use `scripts/moss_request_template.py --prompt ... --curl` to generate a
  validated payload.

## History and uid confusion

**Symptoms**: API response includes unrelated prior context, or a conversation
loses history.

**Recovery**

- Reuse the returned `uid` to continue the same conversation.
- Omit `uid` or provide a new one to start fresh.
- Remember that source history is in process memory; restarting the server or
  running multiple workers will not preserve or share it.

## Server startup stalls

**Symptoms**: Uvicorn/Gradio/Streamlit command appears hung before serving.

**Likely causes**

- Large Hugging Face checkpoint download.
- CUDA memory allocation during model load.
- Import-time dependency resolution.

**Recovery**

- Validate command flags with the inference helper first.
- Pre-download or point to a local checkpoint.
- Run the model-runtime CUDA/import smoke helper.
- Watch GPU memory and logs before sending test traffic.

## Port and binding problems

**Symptoms**: address already in use, cannot access server remotely, firewall
blocks traffic.

**Recovery**

- The FastAPI source binds `0.0.0.0:19324`. Change port/host only in a deliberate
  service wrapper or source modification.
- For local-only testing, bind to loopback when adapting the service.
- Check firewall, container, and proxy rules before exposing publicly.

## UI dependency failures

**Symptoms**: `ModuleNotFoundError` for `gradio`, `streamlit`, or `mdtex2html`;
Gradio API incompatibility; Markdown/LaTeX rendering errors.

**Recovery**

- Install UI dependencies from the documented requirements.
- If Gradio API methods changed, keep the behavior but adapt UI construction to
  the installed Gradio version.
- Rendering failures should not change the underlying prompt/history format;
  fall back to plain text when necessary.

## CUDA/OOM during service

**Recovery**

- Use INT4 or INT8 only on one GPU.
- Use FP16 SFT with Accelerate when multi-GPU model parallelism is required.
- Reduce request `max_length` and history length.
- Avoid launching multiple service workers that each load a full model.

## Stop criteria and response truncation

The Streamlit demo stops on `<eom>`. If responses include raw stop tokens or do
not stop, verify tokenizer special tokens and decode with `skip_special_tokens`
where appropriate. If the API uses `max_length` rather than `max_new_tokens`,
long prompts reduce available generation room.
