# vLLM Serving Troubleshooting

This table focuses on the failure surfaces specific to the HunyuanImage-3.0
vLLM path. It assumes the core package install already succeeded and only the
serving stack is under review.

| Symptom | Likely cause | Safe recovery | Verification signal |
| --- | --- | --- | --- |
| `vllm serve` starts but task support is missing or image-task handling looks wrong | The custom vLLM branch is not installed | Reinstall the branch `feature/hunyuan_image_3.0` from the repo notes and use the branch-specific editable install before retrying | The rendered server command still matches the repo wrapper, but the branch is now the custom one |
| The server does not recognize the HunyuanImage-3.0 task path | `VLLM_ENABLE_HUNYUAN_IMAGE3_TASK` was not exported | Include `export VLLM_ENABLE_HUNYUAN_IMAGE3_TASK=1` in the launch environment or use the bundled command renderer, which prints it by default | The command text contains the env var before `vllm serve` |
| The client gets `Connection refused`, timeout, or a blank response | The server is not running, is on a different host/port, or the URL is wrong | Check that the service is listening at the expected host and port, then point the client at the correct `/v1/chat/completions` URL | A direct request to the endpoint succeeds once the service is up |
| The client says the model is unknown or the request is routed to the wrong model | The request `model` field does not match `--served-model-name` | Keep the client model equal to the server alias. The repo default is `vllm_hunyuan_image3` | Server and client aliases match exactly |
| Docker works but host manual setup fails, or the reverse | Container/manual drift between the custom vLLM branch and the host environment | Treat the Dockerfile and the manual install notes as separate deployment recipes. Rebuild or reinstall from the same branch before comparing behavior | Both paths use the same branch and dependency set |
| Running the payload builder does not create an image | The payload builder only renders JSON | Start the server separately, then POST the printed JSON to the service endpoint | The JSON payload is visible on stdout or in the optional output file |
| `sequence_template=instruct` fails | The inspected `build_payload` path only implements `pretrain` | Use `pretrain` for the safe bundled contract, or extend the branch intentionally if you need a different sequence template | The payload builder completes with a pretrain template |
| `think` or `recaption` does not build a payload | The safe bundled payload contract only verifies `image` and `auto` request shapes | Use `image` or `auto` for the bundled helper. If you need those additional labels, treat them as an upstream branch extension rather than a guaranteed runtime path | The payload builder reports the unsupported label clearly |
| `image_size` looks flipped | The source client stores image size as `height x width` | Pass `--height` first and `--width` second when you want a specific payload size | The rendered payload shows `"image_size": "<height>x<width>"` |
| The server launches but the request never returns an image | The client and server are out of contract on alias, URL, or task type | Re-check the endpoint, alias, `task_type`, and `task_extra_kwargs` before touching unrelated model code | The payload fields match the reference table exactly |

## Quick recovery checklist

1. Confirm the server command includes the custom vLLM branch assumption and
   the required env vars.
2. Confirm the client `model` value equals the server alias.
3. Confirm the URL points to the active service at `/v1/chat/completions`.
4. Re-render the payload with the bundled script and compare the `task_extra_kwargs`.
5. Only after those checks should you inspect checkpoints, hardware topology,
   or unrelated package imports.

## What not to do

- Do not assume the standard repo install is a complete serving stack.
- Do not use the payload builder as a server launcher.
- Do not point the client at an arbitrary alias and expect the server to infer
  the right model.
- Do not treat Docker and manual installs as interchangeable until the branch,
  env vars, and dependency set are the same.
