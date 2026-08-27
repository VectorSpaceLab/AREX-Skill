# Export troubleshooting

## `onnx` or `coremltools` is missing

Those backends are optional and not always installed.

Recovery:

- Use the export helper to confirm availability before starting a conversion.
- Install the missing package if you truly need that format.
- Fall back to a format that is already supported in the environment.

## Checkpoint loads but export fails

The checkpoint may be fine while the export backend or tracing path is not.

Recovery:

- Confirm that the checkpoint works in a normal model-forward smoke check.
- Check the backend package version.
- Try the simplest target first.

## ONNX checker failure

The ONNX export can succeed syntactically and still fail validation.

Recovery:

- Use the checker failure as a signal that the exported graph or opset is not compatible.
- Re-run with the expected input shape.
- Reduce the export to the format your runtime actually needs.

## CoreML conversion failure

CoreML conversion depends heavily on the platform and optional packages.

Recovery:

- Treat CoreML as the most environment-sensitive export target.
- Confirm that `coremltools` imports before you try to convert.
- Use TorchScript or ONNX if CoreML is not the right target.

## Shape or trace mismatch

Export can fail when the trace input shape does not match what the downstream consumer expects.

Recovery:

- Choose a realistic image size.
- Keep the dry-run batch shape small.
- Re-run the model-forward smoke helper first if you suspect the model stack itself is broken.
