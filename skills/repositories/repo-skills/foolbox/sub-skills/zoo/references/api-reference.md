# Model Zoo API Reference

- `fb.zoo.get_model(url, module_name='foolbox_model', overwrite=False, **kwargs)`
  calls the Git cloner, then loads `module_name` and calls its `create(**kwargs)`.
  The returned object should be a Foolbox `Model`.
- `fb.zoo.ModelLoader.get(key=None)` returns the default loader. A non-`None`
  unknown key raises `ValueError`; this version does not register alternate
  loaders through the public selector.
- `ModelLoader.load(path, module_name='foolbox_model', **kwargs)` imports the
  module from a local path and forwards kwargs to `create()`.
- `fb.zoo.fetch_weights(weights_uri, unzip=False)` downloads a URI into a cache
  keyed by a hash of the URI and returns the downloaded path, or an extracted
  folder when `unzip=True`.
- `fb.zoo.GitCloneError` wraps clone failures from the remote repository.

A minimal compatible module is:

```python
import foolbox as fb


def create(**kwargs):
    del kwargs
    return fb.NumPyModel(lambda x: x.reshape((len(x), -1)), bounds=(0, 1))
```

The real model's output should be a batch of logits. For framework models,
`create()` must import the framework and construct the appropriate Foolbox
wrapper itself.
