---
name: neuron-view
description: "Route BertViz neuron_view query/key neuron inspection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# neuron-view

Use this sub-skill when a BertViz task needs the neuron view: per-head attention plus the query and key vectors that produced each attention score.

## Route here when

- You need `bertviz.neuron_view.show` to render the interactive neuron view in a notebook, Colab, or saved HTML workflow.
- You need `bertviz.neuron_view.get_attention` to compute the serialized attention/query/key payload for validation, custom inspection, or debugging.
- You need BertViz's vendored modified Transformer classes from `bertviz.transformers_neuron_view` because ordinary Hugging Face models do not expose query/key vectors in the schema expected by neuron view.
- You need sentence-pair neuron-view slicing for BERT or RoBERTa, or you need to explain why GPT-2 and XLNet sentence pairs fail.
- You need an offline toy BERT validation path that avoids pretrained model downloads.

## Do not route here when

- The user already has attention tensors and only wants head view or model view rendering; use [`../attention-views/SKILL.md`](../attention-views/SKILL.md).
- The task is generic Transformers fine-tuning, training, checkpoint serving, generation, or deployment.
- The task asks for encoder-decoder, cross-attention, or tensor-only head/model view workflows; use [`../attention-views/SKILL.md`](../attention-views/SKILL.md).
- The task requires interpreting attention as a causal explanation of model predictions; this skill only operates BertViz neuron-view mechanics.

## Start with

- [`references/api-reference.md`](references/api-reference.md) for signatures, `model_type` values, output schema, and token partition behavior.
- [`references/workflows.md`](references/workflows.md) for BERT, GPT-2, RoBERTa, toy validation, HTML export, and offline/cache-first recipes.
- [`references/model-compatibility.md`](references/model-compatibility.md) for vendored class choices, sentence-pair support, optional dependencies, and CPU expectations.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common errors and recovery steps.
- [`scripts/validate_toy_bert_attention.py`](scripts/validate_toy_bert_attention.py) for no-network local validation of `get_attention` behavior.

## Routing shortcuts

- Use `show(...)` for display/export; it calls `get_attention(..., include_queries_and_keys=True)` internally and injects the payload into BertViz HTML/JavaScript.
- Use `get_attention(...)` for assertions, schema inspection, and non-display workflows.
- Valid `model_type` strings are exactly `bert`, `gpt2`, `xlnet`, and `roberta`; they are not inferred from the model class.
- BERT and RoBERTa support sentence-pair partitions (`all`, `aa`, `ab`, `ba`, `bb`); GPT-2 sentence pairs raise `ValueError`; XLNet sentence pairs raise `NotImplementedError`.
- Keep core neuron-view validation CPU-local and no-network whenever possible. Prefer the bundled toy script before trying remote pretrained notebooks or uncached `from_pretrained(...)` calls.
- If the workflow does not need query/key vectors, route to [`../attention-views/SKILL.md`](../attention-views/SKILL.md) instead of forcing vendored neuron-view models.
