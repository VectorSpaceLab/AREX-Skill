# Workflows

## Tiny static model

```python
import tensorflow as tf
import tensorlayer as tl

x = tl.layers.Input([None, 4], name='input')
y = tl.layers.Dense(8, act=tf.nn.relu, name='hidden')(x)
y = tl.layers.Dense(3, name='logits')(y)
model = tl.models.Model(inputs=x, outputs=y, name='tiny')
```

## Tiny dynamic model

```python
class TinyModel(tl.models.Model):
    def __init__(self):
        super().__init__(name='tiny_dynamic')
        self.hidden = tl.layers.Dense(8, act=tf.nn.relu, in_channels=4)
        self.out = tl.layers.Dense(3, in_channels=8)

    def forward(self, x):
        x = self.hidden(x)
        return self.out(x)
```

## Safe save/load round-trip

1. Build the model.
2. Run one forward pass on a tiny NumPy array.
3. Save the weights to a temporary path.
4. Zero the weights or create a second model instance.
5. Reload the saved weights and confirm the output returns to the original value.

The bundled `scripts/smoke_model.py` uses `tl.files.save_weights_to_hdf5` plus a temporary HDF5 attribute normalization step before load because that path is the most reliable tiny round-trip in the current inspection environment.

## Optional pretrained constructor check

Instantiate each constructor with `pretrained=False` when you only need to verify the API surface:

- `tl.models.vgg16(pretrained=False)`
- `tl.models.MobileNetV1(pretrained=False)`
- `tl.models.ResNet50(pretrained=False, n_classes=10)`
- `tl.models.SqueezeNetV1(pretrained=False)`

The smoke script exposes these checks behind `--image-models` so they stay optional.
