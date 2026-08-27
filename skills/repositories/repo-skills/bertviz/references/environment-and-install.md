# Environment and Install Reference

## Purpose

Read this before setting up BertViz for attention visualization, notebook use,
or offline validation.

## Package installation

BertViz is distributed as the Python package `bertviz`.

```bash
pip install bertviz
```

The package metadata for version 1.4.1 declares these runtime dependencies:

- `transformers>=2.0`
- `torch>=1.0`
- `tqdm`
- `boto3`
- `requests`
- `regex`
- `sentencepiece`
- `IPython>=7.14`

Interactive notebook display also requires a Jupyter frontend. The README
recommends:

```bash
pip install jupyterlab
pip install ipywidgets
```

Colab users normally install in the notebook with:

```python
!pip install bertviz
```

## Quick import checks

Use the root helper for a no-network check:

```bash
python scripts/check_bertviz_environment.py
python scripts/check_bertviz_environment.py --include-neuron-view
```

The helper verifies imports, public signatures, packaged JavaScript files, and
optional neuron-view class exports. It does not download pretrained models.

## Backends and hardware

BertViz itself renders PyTorch attention data and HTML. CPU is sufficient for:

- Package import checks.
- `head_view` and `model_view` synthetic tensor validation.
- Toy `neuron_view.get_attention` validation.
- Saving HTML returned by `html_action="return"`.

A GPU may be useful upstream when computing attention tensors from a large
Transformer model, but GPU execution is not a BertViz requirement. Do not claim
CUDA validation unless the upstream model forward pass actually ran on CUDA.

## Notebook display expectations

BertViz uses `IPython.display.HTML` and `IPython.display.Javascript` and injects
RequireJS. In notebooks, `html_action="view"` displays immediately. In scripts,
CI, Databricks-style custom display, or when frontend JavaScript is blocked, use
`html_action="return"` and write the returned `.data` string to an HTML file.

## Packaged JavaScript assets

The Python package includes:

- `bertviz/head_view.js`
- `bertviz/model_view.js`
- `bertviz/neuron_view.js`

The view functions load these assets from the installed package. Do not copy or
edit the JavaScript files to make ordinary workflows work. If an asset is
missing, reinstall BertViz from a complete wheel/source distribution.

## Offline validation order

1. Run `scripts/check_bertviz_environment.py`.
2. For head/model views, run
   `sub-skills/attention-views/scripts/render_synthetic_attention.py --view both --action validate`.
3. For neuron view, run
   `sub-skills/neuron-view/scripts/validate_toy_bert_attention.py --include-query-key-schema`.
4. Only after those pass, try cache/network-dependent pretrained examples.
