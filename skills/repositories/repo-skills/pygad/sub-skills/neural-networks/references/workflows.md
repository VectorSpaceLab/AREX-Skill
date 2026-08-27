# Workflows

## 1) Dense-only NumPy network (`pygad.nn`)

Use this when you need a small forward-pass network without framework dependencies.

1. Create an `InputLayer`.
2. Chain one or more `DenseLayer` instances through `previous_layer`.
3. For classification, use a `softmax` output layer. For regression, use `"None"` on the output layer.
4. Read or mutate weights with `layers_weights*()` helpers.
5. Call `predict()` for inference.

```python
import numpy as np
import pygad.nn as nn

np.random.seed(7)
input_layer = nn.InputLayer(num_inputs=2)
hidden = nn.DenseLayer(num_neurons=3, previous_layer=input_layer, activation_function="relu")
output = nn.DenseLayer(num_neurons=2, previous_layer=hidden, activation_function="softmax")

x = np.array([[1.0, 0.0], [0.0, 1.0]])
weights_vector = nn.layers_weights_as_vector(output)
weights_matrix = nn.layers_weights_as_matrix(output, weights_vector.copy())
nn.update_layers_trained_weights(output, weights_matrix)
preds = nn.predict(output, x)
```

### Notes

- `predict()` reads `trained_weights`, not `initial_weights`.
- `to_vector()` and `to_array()` are useful for debugging shape mismatches.
- `train()` is a lightweight NumPy update loop, not gradient descent.

## 2) GA over a dense NumPy network (`pygad.gann`)

Use this when you want `pygad.GA` to optimize the weights of a dense NumPy network.

1. Prepare the data as `(samples, features)`.
2. Build `GANN`.
3. Convert the initial population with `population_as_vectors()`.
4. Use a fitness function that reads the matching network with `pygad.nn.predict()`.
5. In `on_generation`, write the GA population back into the networks with `population_as_matrices()` and `update_population_trained_weights()`.

```python
import numpy as np
import pygad
import pygad.gann as gann
import pygad.nn as nn

x = np.array([[1, 1], [1, 0], [0, 1], [0, 0]])
y = np.array([0, 1, 1, 0])

net = gann.GANN(
    num_solutions=4,
    num_neurons_input=2,
    num_neurons_output=2,
    num_neurons_hidden_layers=[2],
    hidden_activations="relu",
    output_activation="softmax",
)
initial_population = gann.population_as_vectors(net.population_networks)

def fitness_func(ga_instance, solution, sol_idx):
    if sol_idx is None:
        sol_idx = 0
    preds = nn.predict(net.population_networks[sol_idx], x)
    return (np.mean(preds == y) * 100.0)

def on_generation(ga_instance):
    mats = gann.population_as_matrices(net.population_networks, ga_instance.population)
    net.update_population_trained_weights(mats)
```

### Notes

- Keep the callback update in `on_generation`, not only in the fitness function.
- For adaptive mutation, guard against `sol_idx is None`.
- Regression workflows usually use one output neuron and `output_activation="None"`.

## 3) GA over a NumPy CNN (`pygad.cnn` + `pygad.gacnn`)

Use this when you want to evolve a CNN built from the pure NumPy layers.

1. Create the layer chain: `Input2D -> Conv2D / pooling / activation -> Flatten -> Dense`.
2. Wrap the last layer in `cnn.Model`.
3. Create `GACNN` from the model.
4. Flatten the copied models with `gacnn.population_as_vectors()`.
5. In `on_generation`, restore the population with `gacnn.population_as_matrices()` and `update_population_trained_weights()`.

```python
import numpy as np
import pygad
import pygad.cnn as cnn
import pygad.gacnn as gacnn

x = np.random.RandomState(0).rand(2, 5, 5, 1)
input_layer = cnn.Input2D(input_shape=(5, 5, 1))
conv = cnn.Conv2D(2, 3, input_layer, activation_function=None)
relu = cnn.ReLU(conv)
pool = cnn.MaxPooling2D(pool_size=2, previous_layer=relu, stride=1)
flat = cnn.Flatten(pool)
out = cnn.Dense(2, flat, activation_function="softmax")
model = cnn.Model(last_layer=out, epochs=1, learning_rate=0.01)

gacnn_net = gacnn.GACNN(model=model, num_solutions=3)
initial_population = gacnn.population_as_vectors(gacnn_net.population_networks)
```

### Notes

- `cnn.Model.predict()` expects 4D input tensors.
- Insert `Flatten` before the first dense layer.
- For image classification, use one label per sample and a final `softmax` layer.

## 4) GA over a Keras model (`pygad.kerasga`)

Use this when the model is built with `tensorflow.keras` and you want to optimize its weights with GA.

1. Build a Sequential or Functional model.
2. Create `KerasGA(model, num_solutions)`.
3. Use `population_weights` as the GA initial population.
4. In the fitness function, either call `pygad.kerasga.predict(...)` or restore the weights with `model_weights_as_matrix(...)`.

```python
import numpy as np
import pygad
import pygad.kerasga as kerasga

x = np.array([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
y = np.array([[1., 0.], [0., 1.], [0., 1.], [1., 0.]])

keras_ga = kerasga.KerasGA(model=model, num_solutions=4)

def fitness_func(ga_instance, solution, sol_idx):
    preds = kerasga.predict(model=model, solution=solution, data=x, verbose=0)
    loss = loss_fn(y, preds).numpy()
    return 1.0 / (loss + 1e-8)
```

### Notes

- `predict()` restores the model's original weights after every call.
- Keep the model architecture fixed for the entire GA run.
- If an import fails, the missing dependency is usually `tensorflow` or `keras`.

## 5) GA over a PyTorch model (`pygad.torchga`)

Use this when the model is a `torch.nn.Module` and you want GA to optimize the parameters.

1. Build the `torch.nn.Module` or `torch.nn.Sequential` model.
2. Create `TorchGA(model, num_solutions)`.
3. Use `population_weights` as the GA initial population.
4. In the fitness function, call `pygad.torchga.predict(...)` or restore the weights with `model_weights_as_dict(...)`.

```python
import numpy as np
import torch
import pygad
import pygad.torchga as torchga

x = torch.tensor([[0., 0.], [0.1, 0.6], [1., 0.], [1.1, 1.3]])
y = torch.tensor([[1., 0.], [0., 1.], [0., 1.], [1., 0.]])

torch_ga = torchga.TorchGA(model=model, num_solutions=4)

def fitness_func(ga_instance, solution, sol_idx):
    preds = torchga.predict(model=model, solution=solution, data=x)
    loss = loss_fn(preds, y).detach().cpu().numpy()
    return 1.0 / (loss + 1e-8)
```

### Notes

- `predict()` deep-copies the model before loading a solution.
- Keep the input tensor shape consistent with the model definition.
- If an import fails, the missing dependency is usually `torch`.

## Shared callback pattern

For any GA-backed model optimization workflow, the common post-generation pattern is:

```python
def on_generation(ga_instance):
    population_matrices = population_helper(population_networks, ga_instance.population)
    wrapper.update_population_trained_weights(population_matrices)
```

Use the helper pair that matches the model family:

- `gann.population_as_matrices(...)`
- `gacnn.population_as_matrices(...)`

## Shared validation signals

- `ga.best_solution()` should return a solution vector, fitness value, and index.
- `population_*` helpers should preserve the number of solutions.
- Model prediction helpers should return the framework-native forward-pass output without mutating the caller's model instance.
