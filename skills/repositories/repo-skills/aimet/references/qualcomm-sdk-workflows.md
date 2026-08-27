# Qualcomm AI Hub, QAIRT, and QNN workflows

AIMET prepares quantized model artifacts; Qualcomm AI Hub or local QAIRT/QNN tooling performs target compile/profile/inference. Do not claim target readiness until target-specific tooling has accepted the exported artifacts.

## Required AIMET artifacts

Most flows need one of these forms:

1. AIMET export pair: an `.onnx` model plus matching `.encodings` JSON.
2. ONNX QDQ model: an `.onnx` model containing `QuantizeLinear`/`DequantizeLinear` nodes.

Validate first:

```bash
python scripts/inspect_export.py <export-dir-or-model.onnx>
```

## Local QAIRT/QNN command sequence

Use `scripts/qairt_command_builder.py` to print path-filled commands. The distilled sequence is:

```bash
qairt-converter \
  --input_network exported_model.onnx \
  --quantization_overrides exported_model.encodings \
  --output_path model.dlc

qairt-quantizer \
  --input_dlc model.dlc \
  --output_dlc model_quantized.dlc \
  --float_fallback

qnn-context-binary-generator \
  --model libQnnModelDlc.so \
  --backend libQnnHtp.so \
  --dlc_path model_quantized.dlc \
  --output_dir qnn_context \
  --binary_file model.bin

qnn-net-run \
  --backend libQnnHtp.so \
  --retrieve_context qnn_context/model.bin \
  --input_list input_list.txt \
  --output_dir qnn_outputs
```

The exact SDK library paths and backend names depend on the installed Qualcomm AI Runtime/QNN SDK. Source the SDK environment before running local commands.

## AI Hub QNN compile/profile path

Use `scripts/qai_hub_qnn_job.py --dry-run --qdq-model model_qdq.onnx --device "<device>"` to verify arguments without credentials. A real run requires the `qai_hub` Python package and authenticated AI Hub account.

A compile/profile job should record:

- model path;
- target device name;
- compile options;
- compile job URL;
- compiled zip path;
- profile job URL;
- latency if returned by the profile.

## Inference/evaluation constraints

- AI Hub inference inputs use actual input names from the model/input spec.
- Many QNN-compiled graphs expect batch dimension `N=1`; split larger batches into per-sample arrays when needed.
- Channel-last conversion must match compile options such as forced channel-last input.
- Accuracy requires labels and output semantics; profile latency alone is not an accuracy result.

## Common failure categories

| Failure | Likely cause | Next action |
| --- | --- | --- |
| Missing encodings | Exported model and encodings were separated or not generated | Re-export with AIMET and validate with `inspect_export.py`. |
| Unsupported op | Target backend cannot compile an ONNX op pattern | Simplify/export differently, choose fallback, or change target. |
| SDK command missing | QAIRT/QNN SDK not sourced or installed | Source the SDK setup and verify `qairt-converter`/`qnn-net-run` on `PATH`. |
| AI Hub auth error | Missing/expired AI Hub credentials | Re-authenticate with AI Hub tooling and rerun dry-run/real job. |
| Layout mismatch | Input names, dtypes, shape, or channel order differ | Inspect model inputs and rebuild input-list/data generation. |
