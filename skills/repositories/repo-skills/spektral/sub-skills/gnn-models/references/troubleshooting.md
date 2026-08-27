# GNN Model Troubleshooting

## `GCNConv` or `GCN` fails with a mask/`None` Tensor error

**Symptom**

An error mentions converting `None` to a tensor inside `GCNConv.call()` or `output *= mask[0]`.

**Likely cause**

This Spektral 1.3.1 source revision predates Keras 3 mask behavior. In latest TensorFlow/Keras 3 stacks, Keras may pass a list of `None` masks, which the layer treats as a real mask.

**Fix**

- Prefer a TensorFlow/Keras 2.x-compatible environment for this source revision, e.g. TensorFlow `2.15.x` with Keras `2.15.x`.
- If you must use a newer Keras stack, validate every layer/model call with `scripts/smoke_models.py` and patch/wrap the affected layer behavior intentionally rather than assuming old examples still work.

## `MessagePassing` says adjacency must be sparse

`MessagePassing` requires a rank-2 TensorFlow `SparseTensor` adjacency. Use `SingleLoader` or `DisjointLoader`, or convert SciPy sparse adjacency with `spektral.utils.sparse.sp_matrix_to_sp_tensor`. Do not feed dense batch adjacency from `BatchLoader` to a `MessagePassing` subclass.

## Layer input count is wrong

Most convolution layers expect `[x, a]` or `[x, a, e]`. Edge-feature layers need `e`; disjoint global pooling also needs graph ids `i`. Print one loader batch and compare it to the layer catalog before editing the model.

## Dense pooling ignores padded nodes

When using `BatchLoader`, padded nodes are zeros but still present. Use `BatchLoader(mask=True)` and `GraphMasking` at the model input if a layer/pooling path should ignore padded nodes. Dense pooling layers such as MinCut/DiffPool-style workflows are the common trigger.

## GCN results look wrong after preprocessing

`GCNConv` expects the modified adjacency produced by `gcn_filter`/`GCNFilter`/`LayerPreprocess(GCNConv)`. Applying no preprocessing or applying it twice can change results. Keep preprocessing in one place in the pipeline.

## `GlobalAttnSumPool` single-mode softmax error

In some TensorFlow/Keras versions, `GlobalAttnSumPool` in single mode can fail because the layer squeezes attention coefficients to a 1D tensor and then calls `K.softmax`, which rejects rank-1 input. If this path is required, validate it with a tiny single-graph smoke, use another global pooling layer (`GlobalSumPool`, `GlobalAvgPool`, `GlobalMaxPool`, or `GlobalAttentionPool`) when equivalent, or patch/wrap the attention-sum path intentionally for the target Keras version.

## Shape mismatch between loader and model inputs

- For disjoint mode, `x` is rank 2, `a` is sparse rank 2, and `i` is rank 1.
- For batch mode, `x` is rank 3 and `a` is dense rank 3.
- For mixed mode, `x` is rank 3 and `a` is shared rank 2.
- For single mode, `x` is rank 2 and `a` is rank 2.

Set Keras `Input` layers to match these ranks and set `sparse=True` when the adjacency is a sparse tensor.

## Edge-feature layers fail

Layers such as `ECCConv`, `CensNetConv`, `CrystalConv`, and `XENetConv` use edge features. Confirm that each graph has `e`, that sparse edge features match adjacency nonzero ordering, and that the selected loader includes `e` in its output.

## `GNNExplainer` has no useful subgraph

- Confirm the model produces meaningful probabilities before explaining it.
- Set `n_hops` explicitly if automatic inference cannot count graph convolution layers.
- Pass the same adjacency preprocessing function used by the model, such as `GCNConv.preprocess`, when needed.
- Increase `epochs` for real explanations; the bundled smoke tests intentionally avoid training-scale explanation runs.

## TensorFlow GPU warnings

Warnings about missing CUDA drivers, cuDNN, cuFFT, cuBLAS, or TensorRT are not Spektral failures for CPU workflows. They matter only when the requested workflow explicitly requires GPU acceleration.

## `get_config()` or serialization behaves unexpectedly

Spektral layers often serialize Keras kwargs such as activations, regularizers, constraints, and initializers. If custom callables are used for aggregation or activation, test `layer.get_config()` and reconstruction before relying on model serialization.
