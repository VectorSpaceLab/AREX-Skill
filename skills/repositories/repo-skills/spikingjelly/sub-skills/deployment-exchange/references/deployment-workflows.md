# Deployment Workflows

This reference covers the deployment-exchange paths that are safe to teach from the prepared SpikingJelly evidence set:

- NIR export/import and round-tripping
- Lava / Loihi exchange notes
- Lynxi-oriented compilation and inference notes

It intentionally does **not** cover training loops, dataset acquisition, backend profiling, or ANN2SNN recipe math.

## 1) NIR round-trip contract

### What NIR means here

NIR is the exchange format for a **single-sample, single-time-step** computational graph. In the SpikingJelly docs, NIR graphs store per-node `input_type` and `output_type` metadata, plus edges between nodes.

The important shape rule is:

- `example_input` may include batch/time axes because shape propagation needs a real executable tensor.
- NIR node metadata does **not** keep batch or time axes.
- The exported graph describes the per-sample structure only.

### Verified public entry points

| API | Verified signature in the prepared env | Notes |
| --- | --- | --- |
| `export_to_nir` | `export_to_nir(net, example_input, save_path=None, dt=1e-4)` | Writes HDF5 when `save_path` is set. |
| `import_from_nir` | `import_from_nir(graph, dt=1e-4, device='cpu', dtype=torch.float32, step_mode='s') -> fx.GraphModule` | Accepts either an `NIRGraph` object or a path. |

### Supported source modules from the docs / source

- `torch.nn.Linear`, `spikingjelly.activation_based.layer.Linear`
- `torch.nn.Conv2d`, `spikingjelly.activation_based.layer.Conv2d`
- `torch.nn.AvgPool2d`, `spikingjelly.activation_based.layer.AvgPool2d`
- `torch.nn.Flatten`, `spikingjelly.activation_based.layer.Flatten`
- `spikingjelly.activation_based.neuron.IFNode`
- `spikingjelly.activation_based.neuron.LIFNode`
- `spikingjelly.activation_based.neuron.ParametricLIFNode`

### Supported NIR nodes from the docs / source

- `nir.Linear`, `nir.Affine`
- `nir.Conv2d`
- `nir.AvgPool2d`
- `nir.Flatten`
- `nir.IF`
- `nir.LIF`

### Round-trip behavior

1. Build a model from supported modules only.
2. Pass an executable `example_input` into `export_to_nir`.
3. Save to HDF5 if you want file-based round-tripping.
4. Import the graph back with `import_from_nir`.
5. Use `step_mode='s'` for a single-step graph, or `step_mode='m'` for a sequence graph.
6. The imported model returns a tuple: `(output, state_dict)`.

### Shape rules to remember

| Original model input | NIR graph shape metadata | Imported `step_mode='s'` input | Imported `step_mode='m'` input |
| --- | --- | --- | --- |
| `[B, C, H, W]` | `[C, H, W]` | `[B, C, H, W]` | `[T, B, C, H, W]` |
| `[B, F]` | `[F]` | `[B, F]` | `[T, B, F]` |

Additional rules from the source:

- `Flatten` strips the batch/time axes when NIR shapes are inferred.
- `example_input` must match the actual module path so `ShapeProp` can infer shapes.
- The imported graph is reconstructed as a single-step model first, then `functional.set_step_mode` applies the requested step mode.

### What the bundled smoke proves

The bundled `scripts/nir_roundtrip_smoke.py` verifies:

- HDF5 export works for a stateless model.
- Per-node shape metadata is correct and omits batch/time axes.
- Import from both `NIRGraph` object and HDF5 path works.
- `step_mode='s'` reproduces the original per-frame output.
- `step_mode='m'` reproduces the frame-wise stack of the original model.

### Current environment note

The prepared env uses `nir 1.0.8` and `nirtorch 2.6`. The stateless round-trip is verified. The source path for neuron-node export/import currently expects `nir.IF` / `nir.LIF` constructors with shape-bearing arguments, and that path should be treated as environment-sensitive until the installed NIR release matches that contract.

## 2) Lava / Loihi exchange notes

### Always-available helpers in `spikingjelly.activation_based.lava_exchange`

These pieces are available even when Lava-DL itself is not installed:

- `step_quantize_forward(x, step)`
- `step_quantize(x, step=1.0)`
- `quantize_8b(x, scale, descale=False)` / `quantize_8bit`
- `right_shift_to_zero(x, bits)`
- `BatchNorm2d(...)`
- `LeakyIntegratorStep`
- `CubaLIFNode(...)`

### Quantization and neuron notes

- `step_quantize` rounds to the nearest `k * step`.
- `quantize_8b` quantizes to 8-bit levels using the configured scale.
- `right_shift_to_zero` is the signed right-shift helper that rounds toward zero.
- `BatchNorm2d` is the Lava-oriented quantized BN variant; it uses power-of-two quantized standard deviation.
- `CubaLIFNode` is the deployment-oriented neuron.
  - It only supports hard reset with `v_reset=0`.
  - `scale` determines the internal quantization constants.
  - `store_v_seq` / `store_i_seq` are optional sequence caches, not a deployment requirement.

### Lava-DL-dependent helpers

These appear only when the optional Lava-DL stack is importable:

- `TNX_to_NXT` and `NXT_to_TNX`
- `to_lava_neuron`
- `linear_to_lava_synapse_dense`
- `conv2d_to_lava_synapse_conv`
- `avgpool2d_to_lava_synapse_pool`
- `to_lava_block_dense`, `to_lava_block_conv`, `to_lava_block_pool`, `to_lava_block_flatten`
- `to_lava_blocks`
- `BlockContainer`
- `SumPool2d`

### Lava conversion constraints from the docs and source

- Conv/linear layers must be bias-free in the Lava conversion helpers.
- LIF conversion requires `v_reset=0` and `decay_input=False`.
- Average pooling becomes sum pooling in the Lava path; do not describe it as true average pooling.
- `Flatten` must use `start_dim == 1` in the Lava block path.
- The Lava data layout uses `shape = [N, *, T]`; the SpikingJelly multi-step layout is `shape = [T, N, *]`.

### Deployment guidance

- If the user asks for Loihi deployment but does not have Lava-DL installed, present the helper contracts and shape rules only.
- If they want a training recipe or accuracy benchmark, route out of this sub-skill.
- If they need profiling or backend performance comparisons, route to `../performance-and-analysis/`.

## 3) Lynxi path notes

### Always-available module rewriting helpers

The source exposes these helpers without the vendor compilation stack:

- `BaseNode`
- `IFNode`
- `LIFNode`
- `to_lynxi_supported_module(m_in, T)`
- `to_lynxi_supported_modules(net, T)`

### Lynxi shape / execution rules

- Multi-step Lynxi-compatible neurons require an explicit `T`.
- The source and tutorial warn that Lynxi does not accept 5D tensors anywhere in the compiled path.
- In-place operations are not supported.
- For multi-step paths, the input is treated as `[TN, *]` and internally reshaped to `[T, N, *]`.
- The output is commonly reshaped back to `[T, N, *]` and reduced over time by the caller.

### Supported module conversion table

| SpikingJelly module | Lynxi-compatible result |
| --- | --- |
| `layer.Conv2d` | `torch.nn.Conv2d` |
| `layer.BatchNorm2d` | `torch.nn.BatchNorm2d` |
| `layer.MaxPool2d` | `torch.nn.MaxPool2d` |
| `layer.AvgPool2d` | `torch.nn.AvgPool2d` |
| `layer.AdaptiveAvgPool2d` | `torch.nn.AdaptiveAvgPool2d` |
| `layer.Flatten` | `torch.nn.Flatten` |
| `neuron.IFNode` | `lynxi_exchange.IFNode` |
| `neuron.LIFNode` | `lynxi_exchange.LIFNode` |

Unsupported modules are deep-copied to CPU and logged as critical, so do not promise a full compile unless the model was rewritten first.

### Vendor-stack helpers

When `lyngor` and `lynpy` are installed, the module also exposes:

- `torch_tensor_to_lynxi`
- `lynxi_tensor_to_torch`
- `compile_lynxi_model`
- `load_lynxi_model`

Path notes:

- `compile_lynxi_model(output_dir, net, in_data_type='float32', out_data_type='float32', input_shape_dict={})` expects a Lynxi-compatible module graph.
- `load_lynxi_model(device_id, model_path)` loads the compiled `Net_0` artifact.
- The tutorial recommends `float16` for deployment because `float32` can accumulate errors across layers.

### Deployment guidance

- Route questions about module support or tensor layout here.
- Route questions about quantization or the deployment runtime to the Lava section above.
- Route questions about kernel profiling or accelerator troubleshooting to `../performance-and-analysis/`.

## 4) Quick decision tree

1. If the user wants a portable graph between frameworks, start with NIR.
2. If the user wants Loihi-oriented deployment and Lava-DL is present, use the Lava path.
3. If the user wants Lynxi APU compilation, use the Lynxi path and keep the explicit `T` and 4D limits visible.
4. If the user is asking for model composition, training, or performance tuning, route them away from this sub-skill.
