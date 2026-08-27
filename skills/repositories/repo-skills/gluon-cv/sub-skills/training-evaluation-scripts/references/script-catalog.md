# Script catalog and bundling decisions

This catalog maps the source script zoo to generated-skill guidance. Source artifact names are evidence labels; the runtime skill does not depend on those files being present.

| Source script family | Workflow | Decision | Bundled replacement | Reason and safety |
| --- | --- | --- | --- | --- |
| Classification CIFAR scripts | CIFAR demo/train/mixup | adapt/reference-only | `scripts/build_training_command.py classification-cifar`; model checks in `../mxnet-model-zoo/` | Useful flags are reusable, but real execution downloads/reads CIFAR and trains. |
| Classification ImageNet scripts | ImageNet demo/train/verify/Horovod/DALI | reference-only | flag anatomy in `training-and-evaluation-scripts.md` | Requires ImageNet/RecordIO, DALI/Horovod optional deps, long jobs. |
| Classification finetune scripts | Minc/custom image finetuning | reference-only | flag anatomy in `training-and-evaluation-scripts.md` | Data-layout and runtime depend on user dataset; no safe generic execution. |
| Detection SSD/YOLO/Faster R-CNN/CenterNet scripts | detection demos/train/eval | adapt/reference-only | `scripts/build_training_command.py detection-ssd`, `detection-yolo`; model/data sub-skill recipes | Flags are valuable; full workflows need datasets, pretrained weights, optional GPU and COCO/VOC metrics. |
| Instance Mask R-CNN scripts | instance demo/train/eval | reference-only | flag anatomy and troubleshooting | COCO masks/pycocotools/GPU memory and pretrained artifacts required. |
| Segmentation train/test scripts | FCN/PSP/DeepLab/ICNet/FastSCNN/DANet | adapt/reference-only | `scripts/build_training_command.py segmentation` | Flag patterns are reusable; real runs need segmentation datasets and often GPU. |
| Pose simple/alpha/directpose scripts | image/webcam pose, validation, DDP, TVM | adapt/reference-only | `scripts/build_training_command.py pose-simple`; Torch/DirectPose route in `../torch-video-workflows/` | Input images/webcam, detector weights, COCO keypoints, TVM, and GPU are gated side effects. |
| Action-recognition MXNet scripts | train/test/infer/feature extraction | reference-only | `scripts/build_training_command.py action-mxnet`; model/data details in sibling sub-skills | Video lists, frame folders, decord, pretrained weights, and long clips make direct execution unsafe. |
| Action-recognition PyTorch scripts and YAML configs | train/test/DDP/FPS/FLOPS/features | adapt/reference-only | `scripts/build_training_command.py action-torch`; `../torch-video-workflows/scripts/torch_video_model_smoke.py` | Config-file shape is reusable; real DDP/FPS/train jobs need GPUs/data. |
| Dataset preparation scripts | download/extract/convert ImageNet, VOC, COCO, UCF101, Kinetics, HMDB51, etc. | reference-only | `../data-transforms-datasets/references/datasets-and-transforms.md` | Network/storage/large conversion side effects; no generic safe execution. |
| Depth Monodepth2 scripts | demo/test/train PoseNet/depth | reference-only | flag anatomy in training reference | KITTI data, image/video inputs, model zoo weights, and long training/testing. |
| Tracking SiamRPN/SMOT scripts | demo/test/benchmark/train/preprocess | reference-only | flag anatomy in training reference | Video/image sequences, MOT/OTB datasets, model paths, and evaluation writes. |
| GAN scripts | WGAN/CycleGAN/SRGAN/StyleGAN demo/train/data prep | reference-only/exclude internals | high-level route only | Large datasets, generated images, checkpoints, and specialized code. |
| Re-ID baseline scripts | Market1501 train/test | reference-only | high-level route only | Dataset-specific and GPU/training-heavy. |
| AutoGluon example scripts | auto classification/detection | route/reference-only | `../automl-deployment-export/` | Optional legacy AutoGluon dependency and training side effects. |
| Deployment export script | MXNet export pretrained model | route/adapt | `../automl-deployment-export/scripts/export_name_check.py` | Name validation is safe; actual export downloads/loads/writes artifacts. |
| Batch/docker tools | maintainer infrastructure | exclude/reference-only | root install/backend troubleshooting | Requires Docker/cluster side effects; not selected as public operating workflow. |

## Safety labels

- **Safe:** parser/help, non-executable flag-template generation, static validation of a small JSON, model-name registry checks, tiny CPU API smoke in sibling scripts.
- **Needs approval:** training, evaluation on real data, dataset preparation/download, pretrained weight download, webcam/video demo, export writing artifacts, GPU/benchmark/DDP jobs.
- **Do not do by default:** deleting/rebuilding datasets, overwriting checkpoints, launching Docker/cluster jobs, or mutating shared caches.
