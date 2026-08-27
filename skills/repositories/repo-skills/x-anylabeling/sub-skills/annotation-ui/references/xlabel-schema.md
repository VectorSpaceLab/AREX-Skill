# XLABEL Schema and Field Semantics

XLABEL is the native JSON label shape used by the GUI. Treat it as a stable
operating interchange for this package, but preserve unknown fields when editing
because task-specific tools store additional data beside the core fields.

## 1. Top-level core fields

The core template contains these fields:

| Field | Type | Semantics |
|---|---|---|
| `version` | string | X-AnyLabeling version that wrote the file. Unknown/missing versions can still load with a warning. |
| `flags` | object | Image-level boolean flags. Image Classifier stores classification labels here. |
| `checked` | boolean | Annotation review status. Missing or non-`true` values are treated as unchecked. |
| `shapes` | array | List of shape objects. Empty for pure classifier/VQA/chatbot examples. |
| `imagePath` | string | Relative image path from the label file directory to the image. When loading, the basename is used internally after resolution. |
| `imageData` | string or null | Base64 image bytes when image embedding is enabled; usually `null`. |
| `imageHeight` | integer | Pixel height. If it conflicts with actual image data, the loader uses actual image dimensions. |
| `imageWidth` | integer | Pixel width. If it conflicts with actual image data, the loader uses actual image dimensions. |

Common additional top-level fields:

| Field | Type | Semantics |
|---|---|---|
| `description` | string | Image-level caption/description entered when no shape is selected. Added as `""` if absent. |
| `chat_history` | array | Chatbot per-image message list with `role`, `content`, and optional `image`. |
| `vqaData` | object | VQA component values keyed by component title/name. |

Unknown top-level fields are preserved by the loader/saver unless they collide
with core template keys.

## 2. Shape object fields

Canonical shape fields are:

| Field | Type | Required? | Semantics |
|---|---|---:|---|
| `label` | string | yes | Category/instance label. Exact validation rejects labels outside the configured label list. |
| `score` | number or null | no | Confidence score from model inference or other source. Search filters can query ranges. |
| `points` | array of `[x, y]` | yes | Pixel coordinates in image space. Shape type determines required count and interpretation. |
| `group_id` | integer or null | no | Groups related shapes such as pose keypoints with a person box, track ids, or multi-part objects. |
| `description` | string or null | no | Shape-level note. Distinct from top-level image description. |
| `difficult` | boolean | no | Marks hard/ambiguous instances; drawn with difficult styling and searchable. |
| `shape_type` | string | no | Defaults to `polygon` if omitted. Must be one of the supported shape types below. |
| `flags` | object or null | no | Shape-level flags, often configured per label. |
| `attributes` | object | no | Custom per-shape attributes from uploaded/configured attribute widgets. |
| `kie_linking` | list of `[int, int]` | no | KIE relation links. The loader rejects non-list pairs and non-integer pair values. |
| `locked` | boolean | no | Serialized only when true. Locked shapes cannot be moved/resized/deleted until unlocked. |
| `direction` | number | rotation only | Rotation angle metadata for rotated rectangles. |
| `cuboid3d` | object | cuboid only when present | Cuboid depth metadata: version, mode, vertex order, depth vector, and source. |

Unknown shape-level fields are preserved as `other_data` unless they are one of
the canonical shape keys.

## 3. Supported shape types and point rules

| `shape_type` | Point rule | Operational notes |
|---|---|---|
| `polygon` | Three or more points. | Closed contour. Brush polygon and magic wand produce this type. |
| `rectangle` | Saved as four corner points. Legacy two-point diagonal rectangles can load and are normalized on save. | Axis-aligned box. |
| `rotation` | Four points plus optional `direction`. | Rotated rectangle/oriented box. |
| `quadrilateral` | Exactly four ordered points. | Vertex order matters; selected display marks the first edge. |
| `point` | Exactly one point. | Keypoint/landmark. Use `group_id` for pose association. |
| `line` | Two points. | Open line segment. |
| `linestrip` | Two or more points. | Open polyline; not closed. |
| `circle` | Two points. | First point is center; second defines radius. |
| `cuboid` | Eight points. | Four front-face vertices plus four rear-face vertices; depth vector may be mirrored in `cuboid3d`. |

Invalid point counts can fail drawing or be skipped by preview/quality checks.
Repair point counts before conversion or training export.

## 4. Classifier and multimodal fields

### Image classification flags

Image Classifier stores labels in top-level `flags`:

```json
{
  "flags": {"cat": true, "dog": false, "outdoor": true},
  "shapes": [],
  "imagePath": "sample.jpg",
  "imageData": null,
  "imageHeight": 480,
  "imageWidth": 640,
  "description": ""
}
```

- MultiClass convention: exactly one class flag should be true.
- MultiLabel convention: any number of class flags may be true.
- Deleting/renaming classifier labels rewrites flag keys across labels.

### VQA data

VQA stores component values under top-level `vqaData`. Values can be strings,
numbers, booleans, or arrays depending on component type:

```json
{
  "vqaData": {
    "question": "What is the object on the table?",
    "answer": "a scanner",
    "split": "train",
    "tags": ["indoor", "tool"]
  }
}
```

Component names should be stable; renaming a component changes the key used for
future autosaves.

### Chatbot data

Chatbot stores per-image conversations under top-level `chat_history`:

```json
{
  "chat_history": [
    {"role": "user", "content": "<image> Count the people.", "image": "frame001.jpg"},
    {"role": "assistant", "content": "There are two people.", "image": null}
  ]
}
```

The UI converts `@image` prompts to `<image>` and records the current image path
on user messages that use the image token.

### Video classifier sidecar

Video Classifier does not use per-frame XLABEL shape files for clip labels. It
stores a sidecar JSON next to the video with:

- `version`: currently `1.0.0`.
- `type`: `video_classification`.
- `video`: video basename.
- `fps`, `duration_ms`, `width`, `height`.
- `labels`: class names.
- `label_colors`: class-to-hex-color mapping.
- `segments`: list of segment objects with `id`, `label`, `start_ms`, `end_ms`,
  `start_frame`, `end_frame`, and `description`.

Sidecars with another `type` are ignored by the Video Classifier; unsupported
sidecar versions or invalid segment schemas are reported as load errors.

## 5. Validation and repair guidance

- Exact label validation requires a configured label list. With `validate_label:
  exact`, any new or edited shape label must match a configured label exactly.
- If exact validation is needed, provide labels through `--labels`, config
  `labels`, or GUI label-class upload before labeling.
- Duplicate configured labels are invalid.
- Missing `checked` is safe and becomes unchecked. Missing `description` is safe
  and becomes an empty string.
- Missing/corrupt `imagePath` is not safe when `imageData` is null; the loader
  must find the image relative to the label file or the provided image dir.
- Avoid storing huge base64 `imageData` unless labels must be self-contained.
- For pose/keypoint exports, all shapes representing one person/object should
  share the same `group_id`; a box and its keypoints with mismatched group ids
  will not stay associated downstream.
- Locked shapes can look selectable but resist geometry edits. Check `locked` if
  an object cannot be moved, resized, brush-edited, or deleted.
