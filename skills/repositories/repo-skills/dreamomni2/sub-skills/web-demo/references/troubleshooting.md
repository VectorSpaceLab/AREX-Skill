# Web demo troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The browser cannot reach the page | The server is bound to the wrong host or the chosen port is blocked | Re-run with a different `--server_name` or `--server_port` value |
| The page opens but the result never appears | The underlying model stack failed to load before the Gradio callback ran | Check the console log and confirm the model paths with `scripts/check_models.py` |
| Editing behaves like the wrong task | The wrong launcher was used or the image order is reversed | Use the editing launcher for edits and keep the source image first |
| The demo starts very slowly | The first launch needs to load the VLM, base model, and LoRA weights | Wait for the initial load; if the startup fails, fix the model paths instead of refreshing the page repeatedly |
| The result is blank or missing | The workflow failed before saving a temporary output file | Inspect the terminal log and rerun the launcher after fixing the underlying error |
| The page works locally but not from another machine | `server_name` is too restrictive or the host firewall is blocking the port | Bind to `0.0.0.0` and open the chosen port on the host if needed |
| The UI has no built-in examples | The bundled launchers intentionally avoid source-checkout-specific sample images | Upload your own two images, or add your own local examples if you want a richer UI |
| The demo OOMs during inference | The same large CUDA stack is being used underneath the UI | Lower the requested image size or switch to a larger GPU |

## Recovery checklist

1. Run `scripts/check_env.py`.
2. Run `scripts/check_models.py`.
3. Confirm the chosen port is free.
4. Relaunch the appropriate web script and watch the console until the model stack finishes loading.
