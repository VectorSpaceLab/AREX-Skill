# HunyuanImage-3.0 vLLM Serving Reference

This reference distills the repo's vLLM deployment path into a self-contained
operating contract. It separates server startup from client payload building so
future agents can reason safely without depending on the original checkout.

## Deployment contract

The vLLM path is not satisfied by a plain `hunyuan-image-3` package install.
A serving environment must also include the HunyuanImage-3.0-specific vLLM
branch and the server launch environment.

Required serving facts:

- Python target from the package metadata: Python 3.12 or newer.
- Verified package distribution name: `hunyuan-image-3`.
- The repo vLLM notes require the custom branch
  `feature/hunyuan_image_3.0` from `https://github.com/kippergong/vllm.git`.
- The tested vLLM environment in the repo notes uses PyTorch 2.7.1 or 2.8.0
  with CUDA 12.8.
- The inspected live environment used torch 2.8.0+cu128, torchvision 0.23.0,
  transformers 4.57.1, diffusers 0.35.2, and CUDA-capable NVIDIA A100 GPUs.
- Server startup must export `VLLM_ENABLE_HUNYUAN_IMAGE3_TASK=1`.
- The repo shell launcher also exports
  `MULTI_MODA_SAVE_PATH=/tmp/hunyuan_image3/png/`.
- The default server alias is `vllm_hunyuan_image3`; clients must send this
  same value in the request `model` field unless the server alias is changed.
- The repo notes place the service at `http://localhost:8000` and the client
  posts to `/v1/chat/completions`.

## Server command shape

Use `scripts/render_vllm_server_command.py` to render the command safely before
starting anything. The rendered command mirrors the repo shell wrapper and is
parameterized for model path, alias, and tensor-parallel size.

Important flags and env vars:

| Item | Source value | Why it matters |
| --- | --- | --- |
| `VLLM_ENABLE_HUNYUAN_IMAGE3_TASK` | `1` | Enables the HunyuanImage-3.0 task path in the custom vLLM branch. |
| `MULTI_MODA_SAVE_PATH` | `/tmp/hunyuan_image3/png/` | Path used by the server path for generated image artifacts. |
| `vllm serve <model>` | required model path | The shell wrapper exits if no model path is supplied. |
| `--trust-remote-code` | enabled | Required for the HunyuanImage model code path. |
| `--served-model-name` | `vllm_hunyuan_image3` | Defines the alias clients put in the payload `model` field. |
| `--max-model-len` | `10000` | Mirrors the repo server wrapper. |
| `--gpu-memory-utilization` | `0.6` | Mirrors the repo server wrapper's memory cap. |
| `--no-enable-prefix-caching` | enabled | Mirrors the repo server wrapper. |
| `--no-enable-chunked-prefill` | enabled | Mirrors the repo server wrapper. |
| `--max-num-batched-tokens` | `10000` | Mirrors the repo server wrapper. |
| `--max-num-seqs` | `1` | Keeps the deployment single-sequence as in the repo wrapper. |
| `--enforce-eager` | enabled | Mirrors the repo server wrapper. |
| `--trust-request-chat-template` | enabled | Lets requests provide the chat template used by the client payload. |
| `-tp` | `8` | Tensor-parallel default from the repo wrapper; change only when you intentionally retune the deployment topology. |

The source wrapper does not add an explicit `--port`; the repo docs state that
service startup is expected at `http://localhost:8000`. If a deployment uses a
different host or port, update the client URL accordingly.

## Docker versus manual setup

The Dockerfile path is reference-only for this skill because building it is
networked, heavyweight, and environment-mutating. Its dependency story is still
important:

- Base image: `vllm/vllm-openai:v0.11.0`.
- Installs current Transformers from GitHub in the container.
- Installs `apache-tvm-ffi==0.1.0b15` plus `diffusers`, `transformers`, and
  `accelerate`.
- Installs HunyuanImage-3.0 into the container.
- Clones the custom vLLM branch `feature/hunyuan_image_3.0` and installs it
  editable with `VLLM_USE_PRECOMPILED=1`.

The manual path in the repo notes performs the same logical steps outside the
container: install HunyuanImage-3.0, install `apache-tvm-ffi==0.1.0b15`, install
`diffusers transformers accelerate`, then install the custom vLLM branch before
starting the server.

Do not mix a container built from the custom branch with a host environment
using ordinary upstream vLLM and assume they are equivalent. Treat Docker and
manual installs as separate deployments that can drift.

## Client request shape

The inspected vLLM client builds a JSON payload and posts it with
`Content-Type: application/json` to `http://0.0.0.0:8000/v1/chat/completions`
by default. The bundled `scripts/build_vllm_payload.py` renders the payload
without making that network request.

Top-level payload fields:

| Field | Value or source | Notes |
| --- | --- | --- |
| `model` | default `vllm_hunyuan_image3` | Must match the server `--served-model-name`. |
| `messages` | empty system message plus user prompt | Mirrors the source client. |
| `max_completion_tokens` | `1` for `image` and `auto` | Source client overrides max tokens for these task types. |
| `temperature` | default `0` | Source client default. |
| `seed` | provided seed or random integer | Source client randomizes when no seed is supplied. |
| `chat_template` | pretrain template for `image` or `auto` | The request trusts a client-supplied chat template. |
| `task_type` | `hunyuan_image3` | Required task discriminator. |
| `task_extra_kwargs` | task-specific dict | Includes inference-step and bot-task controls. |

`task_extra_kwargs` contains:

- `diff_infer_steps`, default `50`.
- `use_system_prompt`, default string `None` in the source client.
- `bot_task`, normally `image` or `auto` for the verified payload shapes.
- `image_size` only for `bot_task=image`.

Image-size ordering is `height x width`, not `width x height`. For example,
`--height 768 --width 1280` renders `"image_size": "768x1280"`. For
`bot_task=auto`, the source client does not add an `image_size` field.

The pretrain chat-template split is:

- `image`: the user prompt is inserted after `<|startoftext|>`.
- `auto`: the user prompt is inserted after `<|startoftext|>` and followed by
  `<boi><image_shape_1024>`.

The source client help advertises `sequence_template` values `pretrain` and
`instruct`, but the inspected `build_payload` implementation only implements
`pretrain`. It also advertises `think` and `recaption`, but the verified safe
payload-builder contract in this skill covers only `image` and `auto` request
shapes.

## Response handling

The source client expects a successful response to contain an `image` field
holding a base64 PNG string. It strips an optional `data:image/png;base64,`
prefix, decodes the bytes, and writes `output.png`. This skill does not bundle
a network client or decoder because the safe construction target is payload and
command rendering, not a live request.

## Minimal safe workflow

1. Render a server launch command:

   ```bash
   python scripts/render_vllm_server_command.py --model-path /model --tensor-parallel-size 8
   ```

2. Run the rendered server command only in an environment that has the custom
   vLLM branch, HunyuanImage-3.0 dependencies, a CUDA-capable runtime, and the
   checkpoint mounted at the chosen model path.
3. Render a payload:

   ```bash
   python scripts/build_vllm_payload.py --bot-task image --height 768 --width 1280 --prompt "sunset beach" --pretty
   ```

4. Post that JSON to the server endpoint with a client of your choice, keeping
   the payload `model` equal to the server alias.
5. If the server or client fails, use `references/troubleshooting.md` before
   changing unrelated dependencies.

## Evidence distilled

This reference was distilled from the repo vLLM README, the server shell
wrapper, the vLLM client payload builder, the Dockerfile, the root README vLLM
news/link, and live `openai_client.py --help` output. The runtime instructions
above are self-contained and do not require reopening those source files.
