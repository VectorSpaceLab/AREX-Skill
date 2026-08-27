# Qwen-VL model and workflow overview

## Model families

| Model | Typical use | Sub-skill |
| --- | --- | --- |
| `Qwen/Qwen-VL` | Base multimodal generation, not chat-style assistant turns | `inference` |
| `Qwen/Qwen-VL-Chat` | Chat-style multimodal prompting and most end-user workflows | `inference`, `serving`, `finetuning` |
| `Qwen/Qwen-VL-Chat-Int4` | Low-memory chat or quantization-oriented workflows | `inference`, `finetuning` |

## Workflow map

| User intent | What to read | What the skill should help with |
| --- | --- | --- |
| Direct image chat or grounding | `sub-skills/inference/SKILL.md` | Prompt format, image list handling, `<ref>/<box>` preservation, box rendering, generation settings |
| Local demo or API server | `sub-skills/serving/SKILL.md` | Gradio launch flags, OpenAI-compatible service behavior, localhost vs exposed binding |
| Adapter training | `sub-skills/finetuning/SKILL.md` | JSON conversation layout, LoRA/Q-LoRA flags, DeepSpeed templates, validation |
| Official benchmark run | `sub-skills/evaluation/SKILL.md` | Dataset layouts, distributed launch arguments, scoring helpers, submission formatting |

## Prompt conventions

- Multimodal chat data often uses `Picture n: <img>...</img>` inside the user turn.
- Grounding responses preserve `<ref>`, `<box>`, and optional `<quad>` tags when you need coordinates.
- The helper scripts assume the user supplies real image paths, URLs, or dataset roots; they do not rely on bundled demo assets.

## Decision hints

1. If the user asks “what checkpoint should I load?”, start with `inference`.
2. If the user asks “how do I expose this as a service?”, start with `serving`.
3. If the user asks “how do I train LoRA/Q-LoRA?”, start with `finetuning`.
4. If the user asks “how do I get benchmark numbers?”, start with `evaluation`.
5. If the request spans more than one row, use the root router and then follow the relevant sub-skill links.
