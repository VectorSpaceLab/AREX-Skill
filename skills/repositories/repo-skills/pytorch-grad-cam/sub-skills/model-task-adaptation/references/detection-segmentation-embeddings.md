# Detection, Segmentation, and Embeddings

## Object detection

Detection models usually return dictionaries with boxes, labels, and scores.
Use `FasterRCNNBoxScoreTarget(labels, bounding_boxes, iou_threshold=0.5)` when
explaining why the detector produced a particular box and class. The target
matches each requested box to the model output by IoU and label, then combines
IoU and score; it returns zero when no box matches.

Important behavior verified from tests:

- The target uses the device of `model_outputs["boxes"]`.
- It preserves the box dtype when creating target tensors.
- It returns a zero tensor on the output device/dtype when no boxes exist.

For Faster R-CNN feature pyramid activations, use the package's
`fasterrcnn_reshape_transform` pattern to interpolate FPN maps to the pooled
spatial size and concatenate channels.

## Semantic segmentation

For segmentation logits shaped like `C x H x W` per sample, define a binary
mask and category:

```python
from pytorch_grad_cam.utils.model_targets import SemanticSegmentationTarget

targets = [SemanticSegmentationTarget(category=car_class_id, mask=mask_numpy)]
```

The target sums scores for one category over masked pixels. Keep the mask shape
aligned with the model output spatial size; the class handles device transfer
inside `__call__`.

`SegEigenCAM` is a segmentation-tailored CAM method that weights activations by
absolute gradients before an SVD projection with sign correction. Use it when
the task specifically asks for Seg-Eigen-CAM or segmentation-oriented EigenCAM.

## Embeddings and similarity

For embedding similarity, write a custom target callable that returns the scalar
similarity of interest. Examples:

```python
class SimilarityTarget:
    def __init__(self, reference_embedding):
        self.reference_embedding = reference_embedding
    def __call__(self, model_output):
        # adapt field selection to the model's actual output
        embedding = model_output["embedding"] if isinstance(model_output, dict) else model_output
        ref = self.reference_embedding.to(embedding.device)
        return torch.nn.functional.cosine_similarity(embedding, ref, dim=-1)
```

If the output is batched, ensure each target receives the matching batch member
or returns the scalar for that member.

## Routing with DFF

Deep Feature Factorization is concept discovery rather than scalar-output CAM.
Route DFF questions to `metrics-and-evaluation` unless the user's blocker is a
target/reshape problem in the underlying model.
