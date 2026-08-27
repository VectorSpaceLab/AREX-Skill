# Troubleshooting

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `The first layer in the network architecture must be an input layer.` | The layer chain does not start at `InputLayer`/`Input2D`, or the `previous_layer` chain is broken. | Rebuild the chain from input to output and pass the last layer to the helper. |
| `num_solutions: The number of solutions within the population must be at least 2.` | `GANN` was created with fewer than 2 solutions. | Use `num_solutions >= 2`. |
| `num_neurons_hidden_layers: A list or a tuple is expected...` | Hidden-layer sizes were passed as a scalar or other unsupported type. | Pass a list or tuple such as `[8, 4]`. |
| `Hidden activation functions... length must match...` | The hidden-activation list does not match the number of hidden layers. | Pass one activation name per hidden layer, or pass one string to repeat it. |
| `The specified activation function ... is not among the supported activation functions` | The activation name is misspelled or not supported by that module. | Use the documented names only: `sigmoid`, `relu`, `softmax`, `"None"` for `pygad.nn`; CNN layer-specific activations are stricter. |
| `The value of the problem_type parameter can be either classification or regression...` | `nn.train()` or `nn.predict()` got a different string. | Pass exactly `classification` or `regression`. |
| `The length of layers ... is not equal to the number of activations functions ...` | The dense chain and activation chain are inconsistent, or the wrong layer object is being passed to `predict()`. | Rebuild the chain, then call the helper on the true last layer. |
| `Mismatch between the vector length and the array shape.` | A vector was restored into the wrong shape. | Reuse the same layer/model that created the vector, and keep the architecture unchanged. |
| `The input to the dense layer must be of type int ...` | A CNN dense layer received a multi-dimensional tensor because `Flatten` was skipped. | Insert `Flatten` before the first dense layer. |
| `The training data input has ... but it must have 4 dimensions.` | `cnn.Model.train()` or `cnn.Model.predict()` got the wrong input rank. | Reshape data to `(samples, height, width, channels)`. |
| `Number of dimensions in the conv filter and the input do not match.` | CNN input depth does not match the convolution filter depth. | Make the input channel count match the conv kernel depth. |
| `A filter must be a square matrix...` | The convolution kernel is not square. | Use a square kernel size. |
| `A filter must have an odd size...` | The convolution kernel size is even. | Use an odd kernel size such as 3 or 5. |
| `The weights of the dense layer cannot be of Type 'None'.` | A CNN dense layer has been cleared or not initialized before inference. | Rebuild the model or restore the trained weights before predicting. |
| `ModuleNotFoundError: No module named 'tensorflow'` when importing `pygad.kerasga` | The optional deep-learning dependency is missing. | Install the deep-learning extras or the framework directly, then rerun the Keras workflow. |
| `ModuleNotFoundError: No module named 'torch'` when importing `pygad.torchga` | PyTorch is missing. | Install PyTorch, then rerun the Torch workflow. |
| `The previous layer cannot be of Type 'None'.` | A layer constructor was given `previous_layer=None`. | Pass a real previous layer object. |
| `The first layer in the network architecture must be an input layer.` in CNN or NN helpers | The helper was pointed at an intermediate or output object from a different chain. | Always pass the true output layer for the same model. |

## Weight-adapter gotchas

### Keras

- `model_weights_as_vector()` only flattens trainable layer weights.
- Rebuild the vector from the same model architecture and the same trainable/freezing state.
- `predict()` temporarily replaces the model weights, then restores the original weights.

### Torch

- `model_weights_as_vector()` reads `state_dict()` order.
- `model_weights_as_dict()` must be paired with the exact same model structure.
- `predict()` deep-copies the model, so the caller's model is not mutated.

### Pure NumPy helpers

- `layers_weights_as_vector()` and `layers_weights_as_matrix()` are strict about layer order.
- `GANN.population_as_matrices()` and `GACNN.population_as_matrices()` must receive the population vectors for the same solution order.

## Fast checks before handing off

- Can you build the model from input to output without manual attribute edits?
- Does the vector length match the total number of trainable parameters?
- Does the prediction helper return one output per sample?
- If the task uses Keras or Torch, is the optional dependency available in the runtime?
