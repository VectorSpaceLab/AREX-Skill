# Paddle training, quantization, and deployment workflows

This reference distills the PaddlePaddle branch of face.evoLVe. It is a checklist for editing or adapting a working checkout; it does not require opening original docs or running long native demos.

## Safe import rule first

The repository has a top-level source directory named `paddle/`. If the repository root is put on `PYTHONPATH` or used as an import root, `import paddle` may import the local empty package instead of the installed PaddlePaddle framework. For Paddle component work, import the installed framework from a neutral path, then add or run from the repository's `paddle/` source directory so source modules such as `config`, `backbone.model_irse`, `head.metrics`, and `loss.focal` can import while `sys.modules['paddle']` already points at the framework.

Use the bundled `scripts/inspect_paddle_components.py` for a safe CPU check before expensive training or deployment.

## Training configuration map

The Paddle training entry point reads `configurations[1]` from `paddle/config.py`. Important fields:

| Field | Meaning and safe operating notes |
| --- | --- |
| `DATA_ROOT` | Identity-folder training root. Expected layout is one directory per identity and image files inside each identity directory. Route generic validation to `data-preparation`. |
| `MODEL_ROOT` | Output directory for checkpoint and exported model files, usually `output`. |
| `LOG_ROOT` | Log directory name, usually `log`; the sampled training code mainly uses Python logging. |
| `BACKBONE_RESUME_ROOT`, `HEAD_RESUME_ROOT` | Optional `.pdparams` files to resume backbone/head weights. If either points at a non-file, training logs that no checkpoint was found and continues from scratch. |
| `BACKBONE_NAME` | Supports `ppResNet_50`, `ResNet_50`, `ResNet_101`, `ResNet_152`, `IR_50`, `IR_101`, `IR_152`, `IR_SE_50`, `IR_SE_101`, `IR_SE_152`. |
| `HEAD_NAME` | Supports `ArcFace`, `CosFace`, `SphereFace`, `Am_softmax`, `Softmax`. |
| `LOSS_NAME` | Supports `Focal` and `Softmax`. |
| `INPUT_SIZE` | Source constructors assert `[112, 112]` or `[224, 224]`; training comments emphasize `[112, 112]`. |
| `RGB_MEAN`, `RGB_STD` | Paddle data loader normalizes image arrays after HWC-to-CHW transpose. Defaults `[127.5, 127.5, 127.5]` for both, mapping image pixels approximately to `[-1, 1]`. |
| `EMBEDDING_SIZE` | Backbone embedding dimension, 512 in the source workflow. |
| `BATCH_SIZE`, `DROP_LAST`, `NUM_WORKERS` | DataLoader controls. `DROP_LAST=True` helps batch normalization consistency. |
| `LR`, `NUM_EPOCH`, `WEIGHT_DECAY`, `MOMENTUM`, `STAGES` | Momentum optimizer and warmup/step decay controls. `STAGES` are epoch indices where LR is divided by 10. |
| `GPU_ID` | Documented GPU id list, but the single-GPU training loader uses CPUPlace in the sampled code; adjust deliberately if enabling GPU. |
| `USE_PRETRAINED` | Applies to `ppResNet_50`; it may download/load pretrained PaddlePaddle ResNet weights and therefore needs `requests` and network/cache access. |
| `SAVE_CHECKPOINT` | Saves backbone/head `.pdparams` and optimizer `.pdopt` files each epoch when true. |
| `SAVE_QUANT_MODEL` | Switches from normal export to PaddleSlim QAT export; requires `paddleslim.dygraph.quant.QAT`. |

## Data loader behavior

`NormalDataset` and `BalancingClassDataset` read all images from the identity-folder tree during dataset construction with Paddle vision `image_load(..., backend='cv2')`.

- Labels are assigned from the order of `os.listdir(DATA_ROOT)`, so class-to-index order is filesystem-dependent unless callers sort or freeze the directory layout externally.
- The loader assumes every child of `DATA_ROOT` is an identity directory containing loadable images. Hidden files, empty folders, non-image files, or nested unexpected folders can break training or create wrong labels.
- The loader transposes HWC images to CHW and applies configured mean/std normalization; it does not resize by default in the active transform. Supply aligned 112x112 (or compatible 224x224) images before training.
- `NormalDataset.num_classes` is set to `len(self.image_data)` in the source, while training also uses `train_dataset.num_classes` as the number of classes. Check this behavior before serious training; the intended value is the number of identity folders, not the number of images.
- `BalancingClassDataset` computes per-class sampling weights but returns one sampled image per index; use it only after checking class counts and memory pressure.

## Model components

Backbones:

- IR and IR-SE constructors: `IR_50`, `IR_101`, `IR_152`, `IR_SE_50`, `IR_SE_101`, `IR_SE_152` from the Paddle IR-SE source. They output a 512-dimensional embedding for supported input sizes.
- ResNet constructors: `ResNet_50`, `ResNet_101`, `ResNet_152` from the Paddle ResNet source. They output a 512-dimensional embedding after the final FC and batch norm.
- `ppResNet_50`: PaddlePaddle-style ResNet implementation with optional pretrained weight download/load when training config sets `USE_PRETRAINED=True`.

Heads:

- `Softmax(in_features, out_features)` for plain classification logits.
- `ArcFace(embedding_size, class_dim, margin=0.50, scale=64.0, easy_margin=False)`.
- `CosFace(in_features, out_features, s=64.0, m=0.35)`.
- `SphereFace(in_features, out_features, m=4)`.
- `Am_softmax(in_features, out_features, m=0.35, s=30.0)`.

Losses:

- `FocalLoss(gamma=2, eps=1e-7)` wraps cross entropy with focal reweighting.
- `Softmax` loss uses `paddle.nn.CrossEntropyLoss`.

## Single-process training workflow

1. Prepare aligned ImageFolder identity folders with one directory per person and loadable 112x112 face images. Use `data-preparation` for validation before Paddle training.
2. Edit the Paddle configuration fields above. Keep `SAVE_CHECKPOINT=True` if you need `.pdparams` checkpoints in addition to final exported inference files.
3. Start with a component shape check using the bundled inspection script. For full training, use the Paddle source directory as the working directory and avoid putting the repository root on `PYTHONPATH`.
4. Run training only when data, runtime, and output disk are available. Full training is long-running and was not verified in this skill construction pass.
5. Normal non-QAT export writes a static backbone under `MODEL_ROOT` using a name pattern like `Backbone_epoch{epoch}`; Paddle creates paired files such as `Backbone_epoch99.pdmodel` and `Backbone_epoch99.pdiparams` depending on the final epoch index.

Checkpoint naming when `SAVE_CHECKPOINT=True`:

- `Backbone_{BACKBONE_NAME}_Epoch_{epoch}_Batch_{batch}_Time_{timestamp}_checkpoint.pdparams`
- `Head_{HEAD_NAME}_Epoch_{epoch}_Batch_{batch}_Time_{timestamp}_checkpoint.pdparams`
- optimizer state files ending in `.pdopt`

## Multi-GPU training caveats

The repository includes `start_mult_gpu_train.py` and `mult_gpu_training.py`, but treat them as a repair checklist rather than a ready command:

- The launcher string uses `fleetrun --gpus=0,1,2,3,4,5,6,7 start_mult_gpu_train.py`, which appears to recurse into the launcher name instead of launching `mult_gpu_training.py`. Confirm and correct the target before use.
- `mult_gpu_training.py` reads `CLIP` from config, but the sampled Paddle config does not define `CLIP`.
- `mult_gpu_training.py` constructs `LFWDataset`, but the Paddle data file defines `NormalDataset` and `BalancingClassDataset`, not `LFWDataset`.
- Do not begin distributed training until these source-level issues, GPU ids, dataset size, and Paddle distributed runtime are confirmed.

## Quantization-aware training (QAT)

Set `SAVE_QUANT_MODEL=True` in the Paddle config to use PaddleSlim QAT in the single-process training script.

The source QAT config uses:

- `weight_preprocess_type='PACT'`
- `weight_quantize_type='channel_wise_abs_max'`
- `activation_quantize_type='moving_average_abs_max'`
- `weight_bits=8`, `activation_bits=8`, `dtype='int8'`
- `window_size=10000`, `moving_rate=0.9`
- `quantizable_layer_type=['Conv2D', 'Linear']`

After training, QAT export calls `save_quantized_model` and writes a static int8 backbone under `MODEL_ROOT` with a name pattern like `Backbone_int8_epoch{epoch}`. Do not claim QAT quality without calibration/evaluation data and target-runtime tests.

## Post-training dynamic quantization

The dynamic quant script is a static-mode PaddleSlim example. It expects an already exported static model and params pair:

- model directory: typically `output/`
- model filename: `output/Backbone_epoch99.pdmodel` in the source example
- params filename: `output/Backbone_epoch99.pdiparams` in the source example
- output directory: `Backbone_epoch99` in the source example
- quantized ops: `conv2d`, `mul`
- `weight_bits=16`

Before running dynamic quantization, verify the exported `.pdmodel` and `.pdiparams` names match the actual final epoch and that `paddleslim.quant.quant_post_dynamic` imports in the active environment.

## Post-training static quantization

The static quant script needs more prerequisites than dynamic quantization:

- exported static `.pdmodel` and `.pdiparams` files;
- a calibration ImageFolder dataset;
- a calibration reader that yields normalized NCHW float arrays;
- compatible PaddleSlim and PaddlePaddle static graph runtime;
- CPU/GPU place selected intentionally.

Source defaults are hard-coded for a calibration root named `data/Casia_maxpy_clean`, `batch_size=128`, `batch_nums=10`, `USE_GPU=True`, and filenames under `./output`. Adapt these values before use. Static quantization was not verified in construction because exported models and calibration data were not supplied.

## Paddle Inference server demo prerequisites

The Paddle Inference demo is a video face-recognition application, not just a backbone call. It needs:

- exported backbone inference pair: model path base `../model/Backbone`, with files `../model/Backbone.pdmodel` and `../model/Backbone.pdiparams` relative to the demo's expected working directory;
- exported MTCNN predictor pairs for `../model/PNet`, `../model/RNet`, and `../model/ONet`, each with `.pdmodel` and `.pdiparams` files;
- Python dependencies: PaddlePaddle with inference API, OpenCV, NumPy, Pillow, scikit-image, tqdm;
- `FaceDatabase/` containing one reference face image per identity;
- permission to create or update `face_data.fdb`, a pickle of identity-name to face embedding;
- an input video named `test.mp4` if using the demo main loop;
- a font file named `simsun.ttc` for PIL text drawing, or a code change to use an available font;
- GPU availability or source changes, because the predictor config calls `config.use_gpu()` and `config.enable_use_gpu(..., 0)`.

Recognition flow:

1. Build/load MTCNN predictors and the backbone predictor.
2. If `face_data.fdb` is absent, iterate `FaceDatabase/`, skip images where MTCNN finds zero or multiple faces, preprocess each 112x112 crop as CHW `(img - 127.5) / 127.5`, infer 512-D features, and pickle the database.
3. For video frames, detect/align faces, infer features, compare against the database with cosine similarity, and label as known only if similarity exceeds the threshold.

The Paddle Inference demo threshold is `0.4` in the source. Recalibrate this threshold for any new model, quantization method, database size, or camera domain.

## Paddle Lite edge demo prerequisites

The Paddle Lite demo targets an edge runtime and uses `paddlelite.lite` APIs. It needs:

- a Paddle Lite Python runtime compatible with the target device and Python environment;
- backbone model file `Backbone.nb`;
- MTCNN model files `model/Pnet.nb`, `model/Rnet.nb`, `model/Onet.nb`;
- `FaceDatabase/`, optional `face_data.fdb`, and `test.mp4` if using the video loop;
- OpenCV, NumPy, Pillow, tqdm;
- a font file named `GBK-EUC-V.ttc` if using the PIL text path; the active code path mostly uses OpenCV text, but keep font availability in mind when adapting.

The Lite demo threshold is `0.6` in the source. The bundled README notes that models are not provided and must be converted for the user's Paddle Lite version. Do not claim Lite deployment is verified until `.nb` models and the target runtime are present and tested.
