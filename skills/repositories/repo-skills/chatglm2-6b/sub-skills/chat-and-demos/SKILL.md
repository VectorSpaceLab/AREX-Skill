---
name: chat-and-demos
description: "Guides ChatGLM2-6B local generation, streaming chat, CLI and
  Gradio/Streamlit demos, quantization, CPU/MPS fallback, and multi-GPU
  placement."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ChatGLM2-6B Chat and Demos

Use this route when the task asks to load ChatGLM2-6B locally, generate a
response, preserve conversation history, run the terminal/Gradio/Streamlit
examples, use quantization, or split a model across GPUs. Use
[`api-serving`](../api-serving/SKILL.md) for HTTP endpoints, [`ptuning`](../ptuning/SKILL.md)
for tuned checkpoints, and [`evaluation`](../evaluation/SKILL.md) for C-Eval.

## First decisions

1. Identify the model source: a Hub id such as `THUDM/chatglm2-6b`, a pinned
   Hub revision such as `v1.0`, or a complete local model directory. Model
   weights are not bundled with this skill.
2. Choose the backend before writing a command. The repository's official
   demos call `.cuda()`. CPU inference is slower and memory-heavy; Mac MPS
   requires a local model path and a compatible PyTorch build.
3. Check memory, model variant, and context limits. FP16/BF16 is documented as
   roughly 13 GB; INT4 reduces the reported minimum to about 5–6 GB but uses
   quantization kernels and can change quality.
4. Run the bundled environment check before loading weights:
   `python sub-skills/chat-and-demos/scripts/check_chatglm2_environment.py --backend auto`.
5. For a multi-GPU plan, inspect the deterministic placement first:
   `python sub-skills/chat-and-demos/scripts/inspect_device_map.py --num-gpus 2`.

## Common loading shape

Use the Transformers remote-code contract and keep the model in evaluation
mode:

```python
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_OR_PATH, trust_remote_code=True, revision=REVISION  # optional
)
model = AutoModel.from_pretrained(
    MODEL_OR_PATH, trust_remote_code=True, revision=REVISION  # optional
).eval()
```

For a normal CUDA model, move the model to CUDA after loading. For CPU use
`.float()` and expect much slower generation. For Apple MPS, load from a local
path and use `.to("mps")`; the repository documents this as a Mac-specific
path, not a Linux fallback.

The usual single-turn call is `model.chat(tokenizer, query, history=[])` and
returns `(response, history)`. For incremental output use
`model.stream_chat(...)`; pass the returned `history` into the next turn. The
CLI and web demos also retain `past_key_values` when the model implementation
supports it. Do not mix a prefix-tuned checkpoint with the base-model route;
use [`ptuning`](../ptuning/SKILL.md) for that distinction.

## Demo routing

- **CLI:** use the interactive loop only after model loading succeeds. Enter a
  prompt, `clear` to reset history, and `stop` to exit. This is a blocking
  interactive process, not a smoke test.
- **Gradio:** use the legacy-compatible dependency range documented in
  [`demo-workflows.md`](references/demo-workflows.md). The source calls the
  deprecated `.style()` method; recent Gradio 6 releases fail before launch.
- **Streamlit:** launch with `streamlit run` and keep model loading in the
  cached resource path. The sidebar controls `max_length`, `top_p`, and
  `temperature`; the session stores history and past key values.
- **Quantization:** use a model/checkpoint that supports the requested 4- or
  8-bit route. Do not claim that a CPU or MPS run supports CUDA-only INT4
  kernels; read the compatibility notes before choosing a device.
- **Multi-GPU:** call the bundled map inspector first. The repository's helper
  keeps embeddings, final layer norm, output layer, rotary positions, and
  `lm_head` on GPU 0, then distributes encoder layers. Use `accelerate` for
  dispatch and verify the actual map on the target model.

Read [`model-loading.md`](references/model-loading.md) for loading and device
choices, [`demo-workflows.md`](references/demo-workflows.md) for command
recipes, and [`troubleshooting.md`](references/troubleshooting.md) when a
model, backend, UI, or memory error appears. The bundled helpers are safe
preflight tools; they never download weights or start a server.
