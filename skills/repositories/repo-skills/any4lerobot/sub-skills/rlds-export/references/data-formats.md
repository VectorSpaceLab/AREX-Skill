# RLDS schema and LeRobot feature mapping

The conversion contract is derived from LeRobot feature metadata and produces
RLDS steps grouped into episodes. Field names below describe the evidence
behavior; always inspect the actual source feature keys because LeRobot versions
and datasets can add or rename fields.

## Episode envelope

The output split is `train`. Each example is an episode object with a `steps`
sequence. Each step contains:

```text
{
  observation: {...},
  action: <tensor or mapping>,
  language_instruction: <text>,
  is_first: <bool>,
  is_last: <bool>,
  is_terminal: <bool>,
}
```

The source implementation uses the following boundary contract:

| Marker | True when | Exactly expected per episode |
|---|---|---|
| `is_first` | `frame_index == 0` | Once, on the first step |
| `is_last` | last frame by episode length or episode transition | Once, on the final step |
| `is_terminal` | same final-frame condition in this exporter | Once, on the final step |

`is_terminal` is set equal to `is_last` by the evidence workflow. This is a
serialization convention, not proof of a task success, failure, timeout, or
physical terminal state. If the source has an independent termination field,
retain it only through an explicitly extended schema rather than overwriting
this convention.

The direct implementation detects an episode transition from `episode_index`.
The Beam implementation loads each metadata episode separately and uses its
recorded length. Compare the two paths on a representative fixture if source
episode ids are sparse, reordered, or not zero-based.

## Observation mapping

The converter derives `observation_info` by feature-key pattern:

| LeRobot key pattern | RLDS field name | RLDS feature | Transformation |
|---|---|---|---|
| `observation.image.*` excluding `depth` | final dotted component, e.g. `front` | `tfds.features.Image` | CHW `[0,1]` → HWC `uint8`; encoding selected by flag |
| `observation.image.*depth*` | final dotted component | `tfds.features.Tensor` | Remove only the singleton channel dimension; output float32 |
| `observation.state` | joined suffix after the observation segment, or final component | `tfds.features.Tensor` | Preserve source shape and NumPy dtype |
| `task` | `language_instruction` | `tfds.features.Text` | Per-step task string |

The source feature metadata supplies shape, dtype, and names/documentation for
schema construction. The exact schema should be generated only after metadata
inspection; do not hard-code a camera or state dimension.

### Ordinary images

LeRobot image values are expected by the evidence converter as channel-first
`(C, H, W)` arrays/tensors in `[0, 1]`. The step mapping is conceptually:

```text
image_uint8_hwc = uint8(image_chw * 255).transpose(1, 2, 0)
```

This is scaling followed by truncating conversion to `uint8`, not normalization
at export time. Validate the input range first. Values outside `[0,1]`, already
`uint8` HWC arrays, alpha channels, or a missing channel dimension require an
explicit adapter decision; do not silently transpose twice or rescale a second
time. Confirm the resulting HWC shape matches the image feature schema.

`--encoding-format jpeg` or `png` controls serialized image encoding. It does
not change the logical channel order or restore information lost by prior
quantization. Use PNG when exact pixel preservation is required; use JPEG only
when its loss is acceptable.

### Depth images

The evidence path recognizes depth when `depth` appears in an
`observation.image` key. At step time it applies:

```text
depth_out = depth.float().squeeze()
```

The comments and runtime operation imply a singleton-channel source such as
`(1, H, W)`, producing `(H, W)` float32. However, the evidence implementation
derives the declared depth shape with `source_shape[:-1]`, which is not the same
operation for `(1,H,W)`. Treat this as a compatibility gate: inspect the actual
metadata convention and one mapped sample, then declare the target shape that
matches the post-squeeze result. Do not blindly copy the declaration rule.

A `(C,H,W)` depth feature with `C > 1`, an HWC depth tensor, a vector, or an
absent depth value is not covered by this implicit rule. Preserve depth units and
calibration; this route does not convert meters, millimeters, disparity, or
invalid-value masks.

The schema uses `tfds.features.Tensor`, not an encoded image feature, for depth.
Do not apply ordinary-image `*255` scaling to depth.

### State

Keys containing `observation.state` become tensor fields. The evidence naming
rule joins key segments after the observation prefix when possible, otherwise it
uses the final dotted segment. Retain shape, dtype, and feature names/docs from
metadata. State is not padded, flattened, normalized, or converted to language
text by this route.

### Action

Keys containing `action` become action fields. When one action field remains,
the action is represented as that tensor directly; when multiple action fields
are found, the configuration retains a mapping of named tensors. The naming
rule is the same suffix-join convention used for state. Preserve action shape
and dtype. Do not assume that an action vector is a single robot arm, that it is
already aligned to the next observation, or that gripper inversion is needed;
those are source-workflow decisions, not RLDS export behavior.

The pattern match is deliberately broad for compatibility with both
`action`-style and `action.<name>` keys. Review collisions before exporting: two
source keys that reduce to the same RLDS field name are a schema error.

## Metadata and type checks

For each feature, compare these three views before writing:

1. Source metadata: key, shape, dtype, and names.
2. Generated RLDS config: logical field name and declared shape/dtype.
3. One mapped step: actual rank, dtype, and value range.

Require:

- image output rank 3 `(H,W,C)` and `uint8`;
- depth output rank 2 `(H,W)` and `float32` for the supported singleton-channel
  layout;
- state/action output shapes equal to their declarations;
- nonempty or intentionally empty task text documented;
- no duplicate reduced field names;
- all episode step lists nonempty unless an explicit empty-episode policy exists.

Source `names` metadata is used as the Tensor/Image documentation field where
available. Missing names should be treated as a documentation gap, not a reason
to invent semantics.

## Synthetic mapping fixtures

A safe fixture can contain two episodes with two `(3, H, W)` RGB images, one
`(1,H,W)` depth image, a state vector, an action vector, and a task string. Assert
that:

- RGB becomes `(H,W,3)` `uint8` with expected endpoint values;
- depth becomes `(H,W)` float32 and is not multiplied by 255;
- state and action values/shapes survive unchanged;
- task maps to `language_instruction`;
- the first frame only has `is_first`;
- each final frame only has `is_last` and `is_terminal`;
- the second episode starts a fresh boundary sequence.

This tests the mapping contract without TensorFlow dataset writing, downloads,
Beam, rendering, or source-repository imports.
