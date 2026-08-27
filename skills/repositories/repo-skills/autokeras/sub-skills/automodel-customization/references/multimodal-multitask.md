# Multimodal and Multitask AutoModel Workflows

Multimodal means each sample has more than one input form. Multitask means the same model predicts more than one target.

## Minimal pattern

```python
import autokeras as ak
image_input = ak.ImageInput()
structured_input = ak.StructuredDataInput(column_names=["age", "fare"], column_types={"age": "numerical", "fare": "numerical"})
image_branch = ak.ImageBlock(block_type="vanilla", normalize=True, augment=False)(image_input)
structured_branch = ak.StructuredDataBlock(normalize=True)(structured_input)
merged = ak.Merge()([image_branch, structured_branch])
regression_output = ak.RegressionHead(output_dim=1, metrics=["mae"])(merged)
classification_output = ak.ClassificationHead(num_classes=3, metrics=["accuracy"])(merged)
model = ak.AutoModel(inputs=[image_input, structured_input], outputs=[regression_output, classification_output], max_trials=1, overwrite=True)
```

Fit with matching structures:

```python
model.fit(
    x=[image_x, structured_x],
    y=[regression_y, classification_y],
    validation_split=0.2,
    epochs=1,
    batch_size=2,
)
```

The order of `x` arrays must match `inputs`; the order of `y` arrays must match `outputs`. If an error reports a wrong array count or incompatible shape, check nesting and order before changing the model.

Use `ak.Merge()` to combine branches before one or more heads. If outputs should use different feature subsets, branch again before the heads.

The bundled `scripts/build_tiny_multimodal_automodel.py` constructs a two-input/two-output graph and can optionally run a tiny fit.
