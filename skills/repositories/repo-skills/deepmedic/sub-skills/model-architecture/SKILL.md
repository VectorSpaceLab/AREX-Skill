---
name: model-architecture
description: "Author, inspect, and troubleshoot DeepMedic modelConfig
  architecture definitions for normal, subsampled, and fully connected
  pathways."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepMedic model architecture

Use this skill when a researcher must create or resize a DeepMedic model, or
explain why a model configuration cannot build. Keep this skill focused on the
architecture contract: model fields, pathway geometry, feature-map/channel
flow, and architecture-side memory trade-offs. Use
[model-config.md](references/model-config.md) for the field reference and
[troubleshooting.md](references/troubleshooting.md) for failure diagnosis.

## Operating procedure

1. Start with a trusted Python-syntax model config. The native loader is
   `ModelConfig(abs_path_to_cfg)` and executes the file as Python; therefore do
   not treat an untrusted config as harmless data. For a no-TensorFlow static
   check, use the bundled `scripts/inspect_model_config.py`.
2. Normalize the required task dimensions: `numberOfOutputClasses` includes
   background, and `numberOfInputChannels` must equal the number of channels
   supplied by every input-channel manifest. Data-list validation belongs to
   [data preparation](../data-preparation/SKILL.md), not this skill.
3. Define the normal pathway with one positive feature-map count and one
   3-integer kernel per layer. Its stride-1 receptive field is
   `1 + sum(kernel[d] - 1)` independently for each spatial dimension. Every
   configured train/validation/inference segment must be at least this large;
   account separately for any `VALID` FC kernels when checking actual output
   size.
4. Add a subsampled pathway only when needed. Normalize a single factor such
   as `[3,3,3]` to one pathway, or use `[[3,3,3], [5,5,5]]` for two. The source
   requires each active subsampled pathway to have exactly the same receptive
   field as the normal pathway. Prefer mirroring normal FMs and kernels first;
   then change FMs, not layer count, unless kernels are redesigned to preserve
   the field. Factors should be positive odd 3-vectors.
5. Treat `numberFMsPerLayerFC` as hidden FC layers only; the final classifier is
   appended automatically with `numberOfOutputClasses` feature maps. Supply
   exactly `len(numberFMsPerLayerFC) + 1` entries in
   `kernelDimPerLayerFC` and `padTypePerLayerFC`. The FC input has the final
   feature maps from the normal path plus every active subsampled path.
6. Use one-based layer numbers in residual and lower-rank config lists. Layer
   1 is invalid for residuals. Residual addition crops the earlier tensor at
   the center and pads or truncates channels; it is not a learned projection.
   Keep residual points on compatible, shrinking or same-sized geometry.
7. Re-run the inspector after each architecture edit. Before training or
   inference, ensure the checkpoint was made with the same classes, channels,
   pathway count/factors, layer widths, kernels, padding, activations, and FC
   layout. Training optimizer/session behavior is covered by
   [training](../training/SKILL.md); inference is relevant here only for
   architecture/checkpoint compatibility.

## Safe small-model recipe

For a minimal two-channel model, use `numberOfInputChannels = 2`, a small
normal list such as `[4, 5, 6]`, three `[3,3,3]` kernels, and
`segmentsDimTrain = [7,7,7]` (normal receptive field 7). Set
`useSubsampledPathway = False`, leave `numberFMsPerLayerFC = []`, and use the
single default classifier kernel `[[1,1,1]]`. Choose a validation segment at
least `[7,7,7]`; inference can be larger if memory permits. Set the class
count to the actual number of labels plus background, not the number of
foreground labels alone.

## Memory-safe resizing

Reduce inference/training segment dimensions only down to the required
receptive field; shrinking below it is invalid. To reduce model memory while
preserving geometry, first lower FMs in later normal/subsampled layers, remove
unused subsampled paths, or remove FC hidden layers. Keep all list lengths
aligned, preserve equal normal/subsampled receptive fields, and check residual
points after removing layers. Larger segments increase activation memory and
can be more expensive than modestly reducing FMs. A lower-rank layer can reduce
parameter cost, but this release's low-rank implementation has edge cases; see
[troubleshooting.md](references/troubleshooting.md) before applying it.
