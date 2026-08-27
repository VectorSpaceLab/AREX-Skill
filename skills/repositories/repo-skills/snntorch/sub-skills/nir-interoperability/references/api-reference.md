# API reference

## Entry points

| Call | Live signature | Purpose |
| --- | --- | --- |
| `export_to_nir` | `export_to_nir(module: torch.nn.Module, sample_data: torch.Tensor, model_name: str = "snntorch", model_fwd_args=[], ignore_dims=[]) -> nir.NIRNode` | Trace a live model with `sample_data`, convert supported modules, and infer graph types before returning the NIR node. |
| `import_from_nir` | `import_from_nir(graph: nir.NIRGraph) -> torch.nn.Module` | Collapse simple recurrent cycles back into snnTorch modules and return an executable `torch.nn.Module`. |

## Export mapping

| snnTorch / torch module | Exported NIR node | Notes |
| --- | --- | --- |
| `torch.nn.Linear` with bias | `nir.Affine` | Weight and bias are copied into the NIR node. |
| `torch.nn.Linear` without bias | `nir.Linear` | Bias-free linear layer. |
| `torch.nn.Flatten` | `nir.Flatten` | Batch axis is usually removed by `ignore_dims=[0]`. |
| `snntorch.Leaky` | `nir.LIF` | Uses vectorized `beta` and `threshold` when provided. |
| `snntorch.Synaptic` | `nir.CubaLIF` | Uses vectorized `alpha`, `beta`, and `threshold` when provided. |
| `snntorch.RLeaky` | embedded `nir.NIRGraph` | Exported as a recurrent subgraph with `lif` and `w_rec` nodes. |
| `snntorch.RSynaptic` | embedded `nir.NIRGraph` | Exported as a recurrent subgraph with `CubaLIF` and recurrent weight nodes. |
| `torch.nn.Conv2d` | `nir.Conv2d` | Convolution round-trips are currently only reliable when the traced shapes and import parameters are compatible. |
| `torch.nn.AvgPool2d` | `nir.AvgPool2d` | Prefer tuple-valued `kernel_size` and `stride`; scalar values can break import. |

## Import mapping

| NIR node | Reconstructed snnTorch / torch module | Notes |
| --- | --- | --- |
| `nir.Affine` | `torch.nn.Linear` | Bias is restored. |
| `nir.Linear` | `torch.nn.Linear(bias=False)` | Bias-free linear layer. |
| `nir.Conv2d` | `torch.nn.Conv2d` | Weight, stride, padding, dilation, groups, and bias are restored. |
| `nir.Flatten` | `torch.nn.Flatten` | Uses the NIR start and end dims. |
| `nir.AvgPool2d` | `torch.nn.AvgPool2d` | `kernel_size`, `stride`, and `padding` are converted back to torch args. |
| `nir.IF` | `snntorch.Leaky` | Rebuilt as a zero-reset leaky neuron. |
| `nir.LIF` | `snntorch.Leaky` | The import path expects zero leak and a stable `r` value. |
| `nir.CubaLIF` | `snntorch.Synaptic` | The import path expects zero leak and a stable `r` value. |
| simple recurrent `nir.NIRGraph` | `snntorch.RLeaky` or `snntorch.RSynaptic` | The importer recognizes the `input -> lif -> w_rec -> lif -> output` pattern. |

## Parameter notes

- `sample_data` is a representative tensor used to trace the live model. It is not stored in the graph.
- `ignore_dims` removes axes from traced shapes. The common batched pattern is `ignore_dims=[0]`.
- `model_fwd_args` is the passthrough list for extra forward arguments.
- `model_name` labels the extracted NIR graph.
- `export_to_nir` calls `nir_graph.infer_types()` before returning, so shape errors appear at export time.
- Imported graph executors may return `(output, state)`. Unwrap the first item when comparing tensors.

## Recurrent graph contract

- `RLeaky` and `RSynaptic` export as embedded `nir.NIRGraph` nodes.
- The simple recurrent block is named with sibling keys such as `1.lif` and `1.w_rec`.
- `all_to_all=False` expects a vector `V` with one value per neuron; a scalar `V` cannot be exported in that path.
- Dense recurrent weights are copied into `torch.nn.Linear` during import.
- Diagonal recurrent weights are reconstructed from `V` during import.
