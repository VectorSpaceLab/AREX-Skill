# Conversion decision guide

Use conversion when the source checkpoint is not already in a registered
Diffusers/native layout. First identify model family and component target
(DiT, VAE, encoder, or auxiliary module). Then inspect the target config and
loader contract, create a mapping table, and record skipped keys.

Validation gates:

- Every required target key is present exactly once.
- Source-only optimizer/EMA/logvar/dynamic-buffer keys are explicitly skipped.
- Fused/split projections have expected shapes and ordering.
- Dtype/precision choices are intentional and serialized safely.
- A tiny load or forward check passes with the converted directory.
- The output can be consumed by the intended `VideoGenerator` preset.

Model-specific converters can require remote code, large memory, or a source
framework. Preserve them as an operator workflow rather than pretending a
portable generic script can replace them. Do not publish until local validation
passes; never put tokens or private paths into conversion configs.
