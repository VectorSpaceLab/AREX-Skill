# Model-Zoo Routing

`ppdet.model_zoo` exposes `list_model`, `get_config_file`, `get_weights_url`, and `get_model`.

- `list_model(filters=[])` reads the packaged `MODEL_ZOO` file and logs all names containing every filter. A filter with no matches raises `ValueError`.
- `get_weights_url(model_name)` returns a `ppdet://models/<basename>.pdparams` URI for the download helper.
- `get_config_file(model_name)` resolves a `ppdet://configs/<name>.yml` URI and may download a versioned archive into a cache. It is not a local path lookup.
- `get_model(model_name, pretrained=True)` resolves the config, constructs `cfg.architecture`, and downloads weights when `pretrained` is true. Use it only with network approval and a cache policy.

The model zoo covers object detection, instance segmentation, keypoints, MOT, rotated detection, small-object detection, PP-Human, PP-Vehicle, slimming, and newer RT-DETR/DINO/DEIM families. For a local source checkout, direct YAML paths under `configs/` are more reproducible than remote model-zoo lookup.

Representative families to route:

- General/high-accuracy detection: Faster/Mask/Cascade RCNN, PP-YOLO/PP-YOLOE, RT-DETR, DINO, GFL, FCOS, RetinaNet.
- Lightweight/edge: PicoDet, PP-YOLOE-T, SSD/SSDLite, TinyPose.
- Segmentation: Mask RCNN, SOLOv2, QueryInst, PP-YOLOE-Seg.
- Keypoint/pose: HRNet, HigherHRNet, Lite-HRNet, PP-TinyPose, pose3d.
- Tracking: FairMOT, JDE, DeepSORT, ByteTrack, OC-SORT, BoT-SORT, CenterTrack.
- Specialized: rotated detection, face, lane, small-object/sliced inference, semi-supervised detection, PP-Human, PP-Vehicle.

Model names, weights, and accuracy tables are versioned; do not infer current benchmark numbers from this reference. Use the target checkout's model-zoo/config files and record the exact commit/config/weight URL in experiment notes.
