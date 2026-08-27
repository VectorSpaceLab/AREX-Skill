---
name: attention-views
description: "Route BertViz head_view and model_view attention-visualization tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# attention-views

Use this sub-skill for BertViz attention visualizations built from `bertviz.head_view.head_view`, `bertviz.model_view.model_view`, and `bertviz.util.format_attention`.

## Route here when
- You need self-attention, sentence-pair, or encoder-decoder/cross-attention visualizations.
- You need `html_action='return'` for saved HTML or non-notebook workflows.
- You need `include_layers`, `include_heads`, `layer`, `heads`, `sentence_b_start`, `display_mode`, or token prettification control.
- You want a quick offline smoke check using synthetic tensors.

## Do not route here when
- The task is about query/key neuron inspection or `get_attention`; use [`../neuron-view/SKILL.md`](../neuron-view/SKILL.md).
- The task is generic Hugging Face training, serving, or model selection.
- The task needs vendored JS assets; BertViz loads its own package data.

## Start with
- [`references/api-reference.md`](references/api-reference.md)
- [`references/workflows.md`](references/workflows.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`scripts/render_synthetic_attention.py`](scripts/render_synthetic_attention.py)

## Routing shortcuts
- Self-attention: pass `attention` plus `tokens`.
- Sentence pairs: add `sentence_b_start` to split the token list.
- Encoder-decoder: pass `encoder_attention`, `decoder_attention`, `cross_attention`, `encoder_tokens`, and `decoder_tokens`.
- `head_view` uses `layer` and `heads` as default selections.
- `model_view` uses `include_layers` and `include_heads` as filters, plus `display_mode='dark'|'light'`.
- For notebooks and scripts that save HTML, call with `html_action='return'` and write the returned `.data`.
- Use `include_layers` and `include_heads` to keep long inputs responsive.
