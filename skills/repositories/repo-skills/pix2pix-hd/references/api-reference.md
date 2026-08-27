# pix2pixHD API Reference

## Purpose

Read this when you need verified module signatures, object roles, or key defaults for the core pix2pixHD workflows.

## Verified signatures

### options.base_options
| Object | Signature | Notes |
| --- | --- | --- |
| `BaseOptions.parse` | `parse(self, save=True)` | Parses CLI flags, sets `opt.isTrain`, and writes experiment options unless `save=False`. |
| `BaseOptions.initialize` | `initialize(self)` | Defines the shared CLI surface for training and testing. |

### options.train_options / options.test_options
| Object | Signature | Notes |
| --- | --- | --- |
| `TrainOptions.initialize` | `initialize(self)` | Adds training-only flags such as `--continue_train`, `--load_pretrain`, `--niter`, `--niter_decay`, and discriminator/loss options. |
| `TestOptions.initialize` | `initialize(self)` | Adds inference-only flags such as `--results_dir`, `--which_epoch`, `--how_many`, `--cluster_path`, `--use_encoded_image`, `--export_onnx`, `--engine`, and `--onnx`. |

### data and utilities
| Object | Signature | Notes |
| --- | --- | --- |
| `get_params` | `get_params(opt, size)` | Computes crop position and flip state. |
| `get_transform` | `get_transform(opt, params, method=3, normalize=True)` | Uses `scale_width` by default. The `resize_and_crop` branch still calls the deprecated `torchvision.transforms.Scale`. |
| `normalize` | `normalize()` | Returns the standard `[-1, 1]` image normalization transform. |
| `AlignedDataset.initialize` | `initialize(self, opt)` | Resolves the paired label / image / instance / feature folders. |
| `AlignedDataset.__getitem__` | `__getitem__(self, index)` | Returns a dict with `label`, `inst`, `image`, `feat`, and `path`. |
| `AlignedDataset.__len__` | `__len__(self)` | Floors the dataset length to a multiple of `batchSize`. |
| `tensor2im` | `tensor2im(image_tensor, imtype=np.uint8, normalize=True)` | Converts a tensor to an image array. |
| `tensor2label` | `tensor2label(label_tensor, n_label, imtype=np.uint8)` | Converts a label tensor to a colored Cityscapes-style image. |
| `Visualizer.__init__` | `__init__(self, opt)` | Creates HTML/log output directories under the checkpoint root when training. |
| `Visualizer.save_images` | `save_images(self, webpage, visuals, image_path)` | Saves inference results into the HTML tree. |

### models
| Object | Signature | Notes |
| --- | --- | --- |
| `create_model` | `create_model(opt)` | Returns `Pix2PixHDModel` when `opt.isTrain` is true, otherwise `InferenceModel`. Wraps the model in `DataParallel` for training when GPUs are enabled. |
| `define_G` | `define_G(input_nc, output_nc, ngf, netG, n_downsample_global=3, n_blocks_global=9, n_local_enhancers=1, n_blocks_local=3, norm='instance', gpu_ids=[])` | Supports `global`, `local`, and `encoder` generator variants. Requires CUDA if `gpu_ids` is non-empty. |
| `define_D` | `define_D(input_nc, ndf, n_layers_D, norm='instance', use_sigmoid=False, num_D=1, getIntermFeat=False, gpu_ids=[])` | Builds the multiscale discriminator. Requires CUDA if `gpu_ids` is non-empty. |

## Core object roles

- `Pix2PixHDModel` owns the training forward pass, losses, checkpoint saving, and feature-aware encoding logic.
- `InferenceModel` is a thin wrapper around `Pix2PixHDModel.inference`.
- `UIModel` reuses the same generator for interactive editing and feature-bank manipulation.
- `HTML` from `util/html.py` is the minimal result-page writer used by `util/visualizer.py`.

## Important defaults

- `TestOptions` defaults to `which_epoch=latest`, `phase=test`, `how_many=50`, and `results_dir=./results/`.
- `BaseOptions` defaults to `gpu_ids=0`, `dataroot=./datasets/cityscapes/`, `resize_or_crop=scale_width`, and `label_nc=35`.
- The dataset length is truncated to a multiple of `batchSize`; keep `batchSize=1` for tiny smoke fixtures.
- `TestOptions().parse(save=False)` is the safe test-time pattern in smoke utilities, because the base parser otherwise expects the train-only `continue_train` flag.

## Signature and behavior notes

- `create_model` selects the model class before initialization, then wraps training in `DataParallel` only when GPUs are present and FP16 is disabled.
- `VGGLoss` loads `torchvision.models.vgg19(pretrained=True)` unless the training recipe disables VGG loss.
- `run_engine.py` is legacy and vendor-specific; do not treat it as the default inference API.
