# Benchmark notes

## NMS defaults from the repository benchmark table

| Family group | Eval `nms-iou-threshold` |
| --- | --- |
| Darknet | `0.6` |
| YOLOv5, YOLOv6, YOLOv7, YOLOR, YOLOX | `0.65` |
| Paddle, YOLO-NAS, DAMO-YOLO, YOLOv8, YOLOv7-u6 | `0.7` |

## Common test values

| Setting | Test value |
| --- | --- |
| `nms-iou-threshold` | `0.45` |
| `pre-cluster-threshold` | `0.25` |
| `topk` | `300` |

## Performance caveats

- The benchmark table in the repository was recorded on a V100-class GPU and is not a universal throughput guarantee.
- The GPU decoder can become the bottleneck even when the model itself is light.
- Darknet and PyTorch models in the benchmark notes use `maintain-aspect-ratio=1`.
- Families that use `cluster-mode=4` in their config templates should keep the no-NMS expectation in mind when comparing benchmark values.

## Practical guidance

- Use the benchmark notes to pick a sane starting point, not as a hard performance contract.
- If the family-specific config template already sets `cluster-mode=4`, do not try to force the NMS defaults above onto it.
