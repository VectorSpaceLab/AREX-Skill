# PyGAD neural-network API reference

This reference covers the public neural helper modules used with `pygad.GA`. The core pure-NumPy modules import with PyGAD's base dependencies. The Keras and PyTorch adapters require optional deep-learning frameworks.

## Dependency boundaries

| Module | Import | Requires |
| --- | --- | --- |
| Dense NumPy NN | `import pygad.nn` | Core PyGAD dependencies. |
| Dense GA population | `import pygad.gann` | Core PyGAD dependencies. |
| NumPy CNN | `import pygad.cnn` | Core PyGAD dependencies. |
| CNN GA population | `import pygad.gacnn` | Core PyGAD dependencies. |
| Keras adapter | `import pygad.kerasga` | TensorFlow/Keras installed, for example via `pygad[deep_learning]`. |
| PyTorch adapter | `import pygad.torchga` | PyTorch installed, for example via `pygad[deep_learning]` or a framework-specific wheel. |

Use Keras/Torch imports lazily inside scripts so users who only need core GA workflows do not need the heavy optional frameworks.

## `pygad.nn`: pure NumPy dense layers

### Classes

```python
pygad.nn.InputLayer(num_inputs)
pygad.nn.DenseLayer(num_neurons, previous_layer, activation_function="sigmoid")
```

- A network is a one-way linked list from the last layer back to the input layer through `previous_layer`.
- `InputLayer.num_neurons` stores input width.
- `DenseLayer` creates `initial_weights` and `trained_weights` arrays of shape `(previous_layer.num_neurons, num_neurons)`.
- Supported activation names are `"sigmoid"`, `"relu"`, `"softmax"`, and `"None"`. Use `"None"` for unconstrained regression outputs.

### Functions

| Function | Signature | Contract |
| --- | --- | --- |
| `layers_weights` | `layers_weights(last_layer, initial=True)` | Return per-layer weight matrices in input-to-output order. |
| `layers_weights_as_vector` | `layers_weights_as_vector(last_layer, initial=True)` | Flatten all trainable weights into one NumPy vector. |
| `layers_weights_as_matrix` | `layers_weights_as_matrix(last_layer, vector_weights)` | Reshape a flat vector back into per-layer matrices. |
| `layers_activations` | `layers_activations(last_layer)` | Return activation names in layer order. |
| `train` | `train(num_epochs, last_layer, data_inputs, data_outputs, problem_type="classification", learning_rate=0.01)` | Simple built-in training helper; not a replacement for GA optimization. |
| `update_layers_trained_weights` | `update_layers_trained_weights(last_layer, final_weights)` | Copy matrices into each layer's `trained_weights`. |
| `predict` | `predict(last_layer, data_inputs, problem_type="classification")` | Use trained weights to predict labels or regression outputs. |
| `to_vector` | `to_vector(array)` | Flatten a NumPy array. |
| `to_array` | `to_array(vector, shape)` | Reshape a 1D NumPy vector into `shape`. |

Validation points:

- The first linked layer must be `InputLayer`.
- Dense layer sizes must be positive.
- `problem_type` is either `"classification"` or `"regression"`.
- `to_array()` expects a 1D NumPy vector whose length equals the product of `shape`.

## `pygad.gann`: GA populations for dense NumPy networks

```python
pygad.gann.GANN(
    num_solutions,
    num_neurons_input,
    num_neurons_output,
    num_neurons_hidden_layers=[],
    output_activation="softmax",
    hidden_activations="relu",
)
```

### Attributes and helpers

| API | Signature / value | Contract |
| --- | --- | --- |
| `GANN.population_networks` | list | One last-layer reference per solution/network. |
| `create_network` | `create_network(num_neurons_input, num_neurons_output, num_neurons_hidden_layers=[], output_activation="softmax", hidden_activations="relu", parameters_validated=False)` | Build one linked-list dense network. |
| `population_as_vectors` | `population_as_vectors(population_networks)` | Convert all networks to flat weight vectors for `initial_population`. |
| `population_as_matrices` | `population_as_matrices(population_networks, population_vectors)` | Convert GA population vectors back to weight matrices. |
| `GANN.update_population_trained_weights` | `update_population_trained_weights(population_trained_weights)` | Update every network with converted matrices. |

`hidden_activations` may be a string shared by all hidden layers or a list with exactly one activation per hidden layer.

## `pygad.cnn`: pure NumPy CNN layers

### Layer classes

```python
pygad.cnn.Input2D(input_shape, logger=None)
pygad.cnn.Conv2D(num_filters, kernel_size, previous_layer, activation_function=None, logger=None)
pygad.cnn.MaxPooling2D(pool_size, previous_layer, stride=2, logger=None)
pygad.cnn.AveragePooling2D(pool_size, previous_layer, stride=2, logger=None)
pygad.cnn.Flatten(previous_layer, logger=None)
pygad.cnn.ReLU(previous_layer, logger=None)
pygad.cnn.Sigmoid(previous_layer, logger=None)
pygad.cnn.Dense(num_neurons, previous_layer, activation_function="relu", logger=None)
```

Supported CNN activation names include `"sigmoid"`, `"relu"`, and `"softmax"`. `Input2D` accepts 2D or 3D input shapes; 2D shapes are promoted by adding a one-channel dimension.

### Model and functions

```python
pygad.cnn.Model(last_layer, epochs=10, learning_rate=0.01, logger=None)
```

`Model` methods:

| Method | Signature | Contract |
| --- | --- | --- |
| `get_layers` | `get_layers()` | Return linked CNN layers in model order. |
| `train` | `train(train_inputs, train_outputs)` | Built-in small training helper. |
| `update_weights` | `update_weights(network_error)` | Update weights from a scalar error. |
| `predict` | `predict(data_inputs)` | Run forward predictions from trained weights. |
| `summary` | `summary()` | Print architecture layer sequence. |

Module helper functions:

| Function | Signature | Contract |
| --- | --- | --- |
| `layers_weights` | `layers_weights(model, initial=True)` | Return Conv/Dense weight matrices. |
| `layers_weights_as_vector` | `layers_weights_as_vector(model, initial=True)` | Flatten Conv/Dense weights into one vector. |
| `layers_weights_as_matrix` | `layers_weights_as_matrix(model, vector_weights)` | Reshape one vector back into per-layer matrices. |
| `update_layers_trained_weights` | `update_layers_trained_weights(model, final_weights)` | Update Conv/Dense `trained_weights` in a model. |

Keep CNN smoke fixtures very small. The pure NumPy convolution path is not optimized for large images.

## `pygad.gacnn`: GA populations for NumPy CNN models

```python
pygad.gacnn.GACNN(model, num_solutions)
pygad.gacnn.population_as_vectors(population_networks)
pygad.gacnn.population_as_matrices(population_networks, population_vectors)
```

- `GACNN` deep-copies the passed `pygad.cnn.Model` into `population_networks`.
- Convert `population_networks` to vectors and pass them as `pygad.GA(initial_population=...)`.
- Convert the GA population or best solution back with `population_as_matrices()` and then call `GACNN.update_population_trained_weights()` or `pygad.cnn.update_layers_trained_weights()`.

## `pygad.kerasga`: Keras model adapter

```python
pygad.kerasga.KerasGA(model, num_solutions)
pygad.kerasga.model_weights_as_vector(model)
pygad.kerasga.model_weights_as_matrix(model, weights_vector)
pygad.kerasga.predict(model, solution, data, batch_size=None, verbose=0, steps=None)
```

Key behavior:

- Only trainable Keras layer weights are included in the chromosome; non-trainable layer weights are preserved when matrices are rebuilt.
- `KerasGA.population_weights` is the initial GA population. The first solution is the model's current flattened weights; later solutions add uniform `[-1, 1]` perturbations.
- `predict()` temporarily sets a solution as model weights, runs a forward pass, and restores the original Keras weights in a `finally` block.
- The adapter expects a built Keras model whose weights already exist. Build/call/compile the model as appropriate before constructing `KerasGA`.

## `pygad.torchga`: PyTorch model adapter

```python
pygad.torchga.TorchGA(model, num_solutions)
pygad.torchga.model_weights_as_vector(model)
pygad.torchga.model_weights_as_dict(model, weights_vector)
pygad.torchga.predict(model, solution, data)
```

Key behavior:

- Weights are flattened from `model.state_dict().values()` after tensors are moved to CPU and detached.
- `TorchGA.population_weights` is the initial GA population. The first solution is the model's current flattened weights; later solutions add uniform `[-1, 1]` perturbations.
- `model_weights_as_dict()` rebuilds tensors with the original state-dict shapes and keys.
- `predict()` deep-copies the model, loads the solution state dict, and runs the forward pass under `torch.no_grad()`, so the caller's model is not mutated.

## Data contracts

- Dense NumPy inputs are 2D arrays: `(num_samples, num_features)`.
- Pure NumPy classification labels are integers from `0` to `num_classes - 1`.
- Regression outputs may be vectors/arrays; choose output activation `"None"` or a compatible activation.
- CNN inputs should include the channel dimension, e.g. `(num_samples, height, width, channels)`, or match the model's documented expected shape.
- Keras and Torch adapters accept whatever input tensor/array shape the model architecture expects.
- Fitness must still use the modern PyGAD signature `(ga_instance, solution, solution_idx)`.
