# Custom layer checklist

Use this checklist when you are adding or evaluating a custom layer, parser handler, backend template, or backend plugin.

## Before coding

- [ ] Decide whether the behavior can reuse an existing hls4ml IR layer.
- [ ] Choose the frontend contract: Keras v2, Keras v3, PyTorch, or ONNX.
- [ ] Decide whether the extension needs a backend-specific optimizer pass or only parsing plus templates.
- [ ] Keep the custom layer name, parser key, and IR class name aligned.

## Keras v2 custom layer

- [ ] Implement a Keras layer class with a stable `get_config()` method.
- [ ] Register the parser with the exact frontend `class_name`.
- [ ] Return one IR layer dict and one output-shape list.
- [ ] Use an existing IR layer class when the custom layer is only a thin wrapper.
- [ ] Keep the parser output `class_name` equal to the name used in `register_layer()`.

## Keras v3 custom layer

- [ ] Subclass `KerasV3LayerHandler`.
- [ ] Set the `handles` tuple so the metaclass registers the handler.
- [ ] Implement `handle(layer, in_tensors, out_tensors)`.
- [ ] Override `load_weight()` if the layer stores custom weight names.
- [ ] If the handler splits one logical layer into multiple HLS nodes, make sure each returned dict contains the mandatory keys.

## PyTorch custom layer

- [ ] Subclass `HLS4MLModule` so FX keeps the module as a leaf.
- [ ] Implement the custom module's `forward()` method.
- [ ] Register the parser with the exact PyTorch module or functional name you want to support.
- [ ] Use the parser inputs to capture the node, class object, names, and shapes.
- [ ] Prefer a named module over a raw functional call when you need a custom parser hook.
- [ ] If the custom module is just a readout or wrapper, consider mapping it to a built-in IR layer instead of inventing a new one.

## ONNX custom layer

- [ ] Register an ONNX handler for the exact node type.
- [ ] Read attributes and shapes from the ONNX graph, not from frontend assumptions.
- [ ] Return a single layer dict and output shape unless the design truly needs more than one IR node.
- [ ] Keep the ONNX handler narrow and deterministic.

## IR layer and backend wiring

- [ ] Subclass `Layer` and declare `_expected_attributes`.
- [ ] Use `Attribute`, `ConfigurableAttribute`, `TypeAttribute`, `WeightAttribute`, and `ChoiceAttribute` where they fit.
- [ ] Implement `initialize()` to create the output variable.
- [ ] Add weights or bias variables only when the layer needs them.
- [ ] Write a `LayerConfigTemplate` for the config block.
- [ ] Write a `FunctionCallTemplate` for the generated call site.
- [ ] Register the backend source file with an absolute path.
- [ ] Register templates on every backend that can compile the source.
- [ ] If the behavior needs a custom optimizer, register the pass and add it to a reachable flow.
- [ ] Remember that a pass with no flow membership does not execute.
- [ ] If the backend needs a writer, register that writer with the same canonical backend name.

## Source and path hygiene

- [ ] Use a unique basename for every registered source file.
- [ ] Avoid relative source paths.
- [ ] Register custom sources on the same backend instance that will generate the project.
- [ ] Prefer small, reusable headers over large ad hoc blobs.

## Test checklist

- [ ] Confirm the parser or handler is visible in the supported-layer registry.
- [ ] Confirm the IR layer appears in the converted model.
- [ ] Confirm the pass is present in the applied flow record when you expect it to run.
- [ ] Compile or predict on a tiny model when the extension is meant to be executable.
- [ ] Add at least one test for new behavior.
- [ ] Run formatting or pre-commit checks on any edited files.

## Minimal success criteria

A custom extension is in good shape when the following are all true:

- the layer is registered,
- the parser recognizes it,
- the IR layer is created,
- any required backend pass is actually applied,
- the generated model still compiles on a tiny example,
- plugin registration or source copying works without warnings.
