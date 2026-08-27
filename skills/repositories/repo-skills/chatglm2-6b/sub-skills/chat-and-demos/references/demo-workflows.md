# CLI, Gradio, and Streamlit Workflows

## When to read

Use this reference when choosing a local user interface or converting an
interactive demo into a controlled deployment plan. The original demo files
are evidence; the commands below are intentionally explicit about model,
backend, and dependency prerequisites.

## Preflight

1. Install the root runtime dependencies and verify `torch.cuda.is_available()`
   when using the official CUDA demos.
2. Ensure the model is cached or provide a local model directory. Do not start
   a demo just to test installation: each demo loads a multi-billion-parameter
   model before opening its UI.
3. Run the bundled check helper and, for multiple GPUs, the device-map helper.
4. Select a free local port and avoid binding an unauthenticated service to a
   public interface; use the API route for deliberate service deployment.

## Command recipes

### CLI streaming chat

From a checkout containing the repository scripts, run the repo's CLI entry
point after the preflight checks. The loop accepts normal prompts, `clear`, and
`stop`. It keeps a conversation `history` and reuses `past_key_values` when
streaming is enabled. Use a small prompt first, then increase the context
budget. The CLI is interactive and should not be used in automation without a
wrapper that handles stdin and termination.

### Gradio demo

The legacy UI exposes a textbox, chat history, clear button, and sliders for
`max_length`, `top_p`, and `temperature`. The source uses Gradio's deprecated
`Textbox.style()` method. The construction environment verified the following
compatibility choice:

```text
gradio==3.50.2
gradio-client==0.6.1
```

Recent Gradio 6 releases removed `.style()` and fail at import-time. If a
future Gradio release is desired, adapt the UI constructor to use the current
layout API rather than silently upgrading the dependency.

### Streamlit demo

Launch with the Streamlit CLI rather than `python`:

```text
streamlit run <path-to-web-demo2.py>
```

The demo caches tokenizer/model initialization, stores `history` and
`past_key_values` in `st.session_state`, and exposes sliders for generation
settings. `streamlit==1.24.0` was used for the legacy dependency combination;
check the current Gradio/Streamlit resolver before mixing newer versions.

## Turning a demo into automation

Prefer `model.chat` or `model.stream_chat` in a controlled application instead
of driving the UI. Keep model initialization outside the request loop, validate
prompt length, cap generation parameters, and make history ownership explicit.
For an HTTP contract, use the `api-serving` route. For a P-Tuning checkpoint,
load the prefix state first using the `ptuning` route, then reuse the same chat
or stream-chat contract.
