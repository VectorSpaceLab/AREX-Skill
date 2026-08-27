# Layers and Nets Workflows

## MLP classifier

```python
model = snt.nets.MLP([128, 64, num_classes])
logits = model(tf.ones([batch_size, input_dim]))
assert logits.shape[-1] == num_classes
```

Enable dropout only when the caller can pass `is_training`:

```python
mlp = snt.nets.MLP([64, 10], dropout_rate=0.1)
y = mlp(x, is_training=True)
```

## Conv2D + BatchNorm block

```python
class ConvBlock(snt.Module):
  def __init__(self, channels):
    super().__init__()
    self.conv = snt.Conv2D(channels, kernel_shape=3, padding="SAME", with_bias=False)
    self.bn = snt.BatchNorm(create_scale=True, create_offset=True)
  def __call__(self, x, is_training):
    return tf.nn.relu(self.bn(self.conv(x), is_training=is_training))
```

## Initializers, regularizers, metrics

Pass initializers to constructors (`w_init`, `b_init`) and apply regularizers to built variables after a build call. Sonnet metric modules such as `Mean` own state; call `reset()` or create fresh metric instances between independent evaluations.

## VQ-VAE modules

Vector quantizers expect the input final dimension to equal the embedding dimension. The returned object contains quantized tensors and loss/perplexity fields; route optimizer updates through the training sub-skill.
