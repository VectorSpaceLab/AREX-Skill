# AutoModel Customization Troubleshooting

## `Inputs and outputs not connected`

Trace from each input node through block calls to each output node. In input/output API, pass heads directly. In functional API, call the head and pass the returned node.

## Missing required input

A block consumes an input node that was not included in `AutoModel(inputs=...)`. Include every source node in the declared `inputs` list in the same order you will pass `x` arrays.

## Cycle in graph

AutoKeras rejects cyclic node/block relationships. Build a directed acyclic graph from inputs to outputs.

## Wrong array count

The nested structure passed to `fit` or `predict` does not match `inputs` or `outputs`:

```python
model = ak.AutoModel(inputs=[image_input, text_input], outputs=[reg_head, class_head])
model.fit(x=[image_x, text_x], y=[reg_y, class_y], ...)
```

## Pretrained image blocks trigger downloads or shape constraints

For offline smoke checks, set `pretrained=False` or use `ImageBlock(block_type="vanilla")`. Use three-channel images for ImageNet-style pretrained models.

## Shape incompatibility in merges

Use `SpatialReduction`, `TemporalReduction`, or `Flatten` to turn branch outputs into vector-like representations before merging when shapes differ.
