# BertViz Troubleshooting

## Purpose

Use this for package-level install/import/display failures before diving into a
specific view sub-skill.

## Cross-cutting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'bertviz'` | Package is not installed in the active Python environment. | Run `pip install bertviz`, then rerun `python scripts/check_bertviz_environment.py`. |
| `ModuleNotFoundError` for `torch`, `IPython`, `sentencepiece`, `boto3`, or `transformers` | Runtime dependencies are missing or environment resolution failed. | Reinstall BertViz in a clean environment; do not rely on partial source checkout imports. |
| `ImportError` from PyTorch shared libraries | PyTorch/backend wheel mismatch or broken low-level runtime. | Verify `python -c "import torch; print(torch.__version__)"`; reinstall a CPU or CUDA PyTorch build compatible with the host. |
| Notebook cell displays blank output | Jupyter/Colab frontend blocked JavaScript or lacks widget/display support. | Install/enable JupyterLab and ipywidgets, or use `html_action="return"` and save HTML. |
| Browser, Colab, or notebook disconnects on long text | BertViz renders many tokens/layers/heads in JavaScript. | Shorten input and filter layers/heads where supported. |
| Saved HTML is missing BertViz JavaScript behavior | Packaged JS assets are missing or blocked by the viewer. | Reinstall BertViz from a complete distribution; open the HTML in a browser that allows embedded scripts. |
| User asks whether attention is an explanation | BertViz visualizes attention patterns but does not prove causal attribution. | Present it as an inspection/visualization aid; use saliency or interpretability methods when causal explanations are required. |

## Decide which sub-skill owns the issue

- Use `attention-views` for tensor shapes, token length mismatches,
  `output_attentions=True`, sentence-pair `sentence_b_start`, encoder-decoder
  arguments, and `include_layers`/`include_heads` issues.
- Use `neuron-view` for `model_type`, modified model/tokenizer imports,
  query/key schema, sentence-pair support limits, and pretrained download/cache
  issues for neuron view.

## No-network checks

```bash
python scripts/check_bertviz_environment.py --include-neuron-view
python sub-skills/attention-views/scripts/render_synthetic_attention.py --view both --action validate
python sub-skills/neuron-view/scripts/validate_toy_bert_attention.py --include-query-key-schema
```

If these pass, the local BertViz APIs are usable; remaining failures are likely
model-download, notebook-frontend, input-shape, or upstream Transformer issues.
