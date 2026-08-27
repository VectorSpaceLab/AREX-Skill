---
name: bertviz
description: "Route BertViz Transformer attention visualization, neuron-view,
  notebook, and HTML export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BertViz

Use this repo skill when a task involves BertViz, Transformer attention
visualization, head/model view rendering, neuron-level query/key inspection, or
saving BertViz notebook visualizations as HTML.

## Install and quick check

For ordinary use:

```bash
pip install bertviz
```

For interactive notebooks also install and enable a notebook frontend such as
JupyterLab plus widgets:

```bash
pip install jupyterlab ipywidgets
```

Minimal package/API check:

```bash
python - <<'PY'
from bertviz import head_view, model_view
from bertviz.neuron_view import get_attention
print("bertviz import ok", head_view.__name__, model_view.__name__, get_attention.__name__)
PY
```

For a stronger no-network check, run [`scripts/check_bertviz_environment.py`](scripts/check_bertviz_environment.py).

## Route by task

| User need | Read next |
| --- | --- |
| Visualize standard self-attention tensors from Hugging Face or another Transformer model. | [`sub-skills/attention-views/SKILL.md`](sub-skills/attention-views/SKILL.md) |
| Render sentence-pair head/model views with `sentence_b_start`. | [`sub-skills/attention-views/SKILL.md`](sub-skills/attention-views/SKILL.md) |
| Render encoder, decoder, or cross-attention for sequence-to-sequence models. | [`sub-skills/attention-views/SKILL.md`](sub-skills/attention-views/SKILL.md) |
| Save BertViz output as standalone HTML or use it outside a notebook display call. | [`sub-skills/attention-views/SKILL.md`](sub-skills/attention-views/SKILL.md), or [`sub-skills/neuron-view/SKILL.md`](sub-skills/neuron-view/SKILL.md) for neuron view |
| Inspect query/key neuron contributions using BertViz's modified model classes. | [`sub-skills/neuron-view/SKILL.md`](sub-skills/neuron-view/SKILL.md) |
| Diagnose package installation, notebook display, PyTorch/IPython dependency, or JS asset issues. | [`references/troubleshooting.md`](references/troubleshooting.md) |
| Check whether this skill matches the current BertViz checkout/version. | [`references/repo-provenance.md`](references/repo-provenance.md) |

## Core distinctions

- `head_view` and `model_view` consume attention tensors. They are the right
  choice when the model can return Hugging Face-style attention weights with
  `output_attentions=True`.
- `neuron_view.show` computes a visualization payload from BertViz's modified
  BERT/GPT-2/RoBERTa/XLNet classes because neuron view needs query and key
  vectors, not only attention probabilities.
- BertViz is a visualization tool, not a model explanation guarantee. It helps
  inspect attention patterns but should not be presented as proving causal
  feature attribution.

## Repo-level references and scripts

- [`references/environment-and-install.md`](references/environment-and-install.md)
  explains dependencies, notebook frontend expectations, backend assumptions,
  and offline validation strategy.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers
  cross-cutting install/import/display/runtime symptoms.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the
  source snapshot and evidence paths used to build this skill.
- [`scripts/check_bertviz_environment.py`](scripts/check_bertviz_environment.py)
  checks imports, function signatures, packaged JavaScript assets, and optional
  neuron-view imports without downloading models.

## Safety defaults

- Do not run public notebooks or `from_pretrained(...)` examples automatically
  when network/model downloads are not explicitly allowed.
- Prefer bundled no-network helpers for validation: the root environment check,
  `attention-views/scripts/render_synthetic_attention.py`, and
  `neuron-view/scripts/validate_toy_bert_attention.py`.
- Keep generated outputs and saved HTML in user-chosen working directories;
  BertViz does not require modifying its installed package files.
