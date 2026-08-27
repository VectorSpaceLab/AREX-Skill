---
name: "serving-and-adapters"
description: "Plan LoRA merge commands and Gradio inference for Qwen-VL merged
  or adapter-backed models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Serving and Adapters

Use this sub-skill for LoRA merge planning, model loading, and Gradio multimodal inference.

## Covers

- `merge_lora_weights.py` command planning.
- LoRA adapter loading and merge behavior.
- Gradio multimodal inference.
- Device, quantization, and generation controls.
- Safe output-path planning for merged checkpoints.

## Excludes

- Training loops.
- Dataset schema design.
- Preference or classification training.

## Read first

- `../../references/workflow-map.md` for route confirmation.
- `../../references/cli-reference.md` for the serving and merge flag surface.
- `../../references/model-compatibility.md` for model and backend caveats.
- `../../references/troubleshooting.md` for serving and merge failures.
- `references/adapter-workflows.md` for merge/load details.
- `references/inference.md` for the Gradio launch pattern.
- `scripts/adapter_command.py` for a safe command builder.

## Typical user requests

- "How do I merge a LoRA adapter?"
- "How do I launch the Gradio demo?"
- "Should I load 4-bit or 8-bit for inference?"
- "How do I load a merged checkpoint versus an adapter checkpoint?"

## Workflow

1. Determine whether the user wants merge or inference.
2. Check whether the model is merged, adapter-backed, or a plain base checkpoint.
3. Decide whether quantization or a specific device should be used for serving.
4. Emit the command with the bundled command builder.
5. For merge tasks, verify the output path is explicit before execution.

## Decision rules

- Use merged weights for LoRA inference when the user wants the simplest serving path.
- Keep `model-base` explicit when loading adapter-backed checkpoints.
- Treat merge as an output-producing step that should not run accidentally.
- Gradio launch is a network-facing service; keep it as a deliberate action.

## Safe command builder

Start with the bundled helper:

```bash
python scripts/adapter_command.py merge --help
python scripts/adapter_command.py gradio --help
```

## If you need more detail

Read `references/adapter-workflows.md` for merge/load notes and `references/inference.md` for the serving path.
