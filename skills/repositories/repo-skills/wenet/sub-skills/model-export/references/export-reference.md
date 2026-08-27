# WeNet Export Reference

Read this before creating deployment artifacts from a trained WeNet experiment.

## Required inputs

Most export modes need:

| Input | Purpose |
|---|---|
| `train.yaml` | model architecture, tokenizer, feature, and export metadata |
| checkpoint such as `final.pt` or `avg_N.pt` | trained model weights |
| `units.txt` or tokenizer resources | required by downstream package/runtime use even when a specific export script only loads config/checkpoint |
| optional `global_cmvn` | copied with model artifacts when the trained config uses it |

Preflight without loading the model:

```bash
python sub-skills/model-export/scripts/check_export_inputs.py \
  --model-dir exp/conformer --mode jit
```

## TorchScript / JIT

TorchScript export uses WeNet's JIT export entry point and can also produce a
dynamic quantized JIT file:

```bash
python -m wenet.bin.export_jit \
  --config exp/conformer/train.yaml \
  --checkpoint exp/conformer/avg_30.pt \
  --output_file exp/conformer/final.zip \
  --output_quant_file exp/conformer/final_quant.zip
```

The export forces CPU visibility for model export. Use this path for libtorch
runtime targets unless a runtime specifically requires ONNX or a vendor format.

## ONNX CPU

ONNX CPU export creates separate graph files for streaming/non-streaming
runtime pieces:

```bash
python -m wenet.bin.export_onnx_cpu \
  --config exp/conformer/train.yaml \
  --checkpoint exp/conformer/avg_30.pt \
  --output_dir exp/conformer/onnx \
  --chunk_size 16 \
  --num_decoding_left_chunks 4 \
  --reverse_weight 0.5
```

Expected outputs include encoder, CTC, and decoder ONNX graphs plus quantized
variants. The exporter attaches metadata such as chunk size, left chunks,
subsampling rate, right context, symbol ids, encoder/decoder type, and decoder
direction. It also checks ONNX Runtime CPU output against PyTorch for the
exported subgraphs.

Chunk choices:

- `chunk_size > 0` and `num_decoding_left_chunks >= 0` are streaming-style
  choices.
- `chunk_size=-1` and `num_decoding_left_chunks=-1` are non-streaming. Do not
  reuse this export as a fixed-chunk streaming model.
- A positive `num_decoding_left_chunks` requires positive `chunk_size`.

## ONNX GPU and TensorRT-related paths

GPU ONNX export/recognition and TensorRT/Triton deployment require CUDA-capable
PyTorch/ONNX Runtime or TensorRT stacks. Validate CUDA and provider availability
before promising runtime execution. Use CPU ONNX export when the user only needs
portable graph creation and no GPU provider-specific behavior.

## IPEX export

IPEX export targets Intel extension optimized paths. It requires a compatible
Intel extension for PyTorch and runtime environment. Use the preflight helper
with `--mode ipex` to detect whether the optional module is importable before
attempting export.

## Horizon BPU export

BPU conversion uses Horizon-specific tooling after ONNX preparation. It is
hardware/toolchain bound. Preflight with `--mode bpu`, then verify the user's
Horizon SDK/toolchain separately before running conversion.

## Artifact handoff to runtime

After export, hand the runtime target these artifacts as applicable:

- JIT/libtorch: `final.zip` or `final_quant.zip`, `units.txt`, config-derived
  feature/tokenizer resources, optional `global_cmvn`.
- ONNX Runtime: encoder/ctc/decoder ONNX files, metadata, units/tokenizer
  resources, CMVN/config values, chosen chunk/cache parameters.
- Vendor runtimes: ONNX or vendor binaries plus the vendor-specific model,
  dictionary, feature, and runtime configuration expected by that platform.

Route deployment selection to [../../runtime-deployment/SKILL.md](../../runtime-deployment/SKILL.md).
