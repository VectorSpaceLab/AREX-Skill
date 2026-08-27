# DeblurGAN API reference

This repo exposes its public surface through source modules rather than a packaged distribution. The signatures below were verified from the repository source and a live inspection environment.

## Options and CLI helpers

| Object | Verified signature | Purpose | Notes |
| --- | --- | --- | --- |
| `options.base_options.BaseOptions.parse` | `parse(self)` | Parses shared CLI options and writes `opt.txt` under the checkpoint directory. | The parser includes data, model, logging, and output flags shared by train/test. |
| `options.train_options.TrainOptions.initialize` | `initialize(self)` | Adds training-specific flags. | Includes schedule, checkpoint, and optimization settings. |
| `options.test_options.TestOptions.initialize` | `initialize(self)` | Adds test-time flags. | Adds results, epoch, and evaluation limits. |

## Data loading

| Object | Verified signature | Purpose | Notes |
| --- | --- | --- | --- |
| `data.data_loader.CreateDataLoader` | `CreateDataLoader(opt)` | Builds the dataset wrapper used by training and inference. | Chooses between aligned and single-image routes; the shipped unaligned route is not initialized correctly. |
| `data.custom_dataset_data_loader.CreateDataset` | `CreateDataset(opt)` | Creates the underlying dataset instance. | Uses `dataset_mode` to choose `aligned`, `single`, or the unsupported `unaligned` stub. |
| `data.image_folder.make_dataset` | `make_dataset(dir)` | Recursively collects supported image files. | Supported extensions are JPG/JPEG/PNG/PPM/BMP in upper and lower case. |
| `data.single_dataset.SingleDataset.initialize` | `initialize(self, opt)` | Prepares single-image inference input. | Returns `A` and `A_paths`. |
| `data.aligned_dataset.AlignedDataset.__init__` | `__init__(self, opt)` | Prepares paired AB training/evaluation input. | Splits each image horizontally into A and B halves. |
| `data.unaligned_dataset.UnalignedDataset.initialize` | `initialize(self, opt)` | Defines an unaligned loader stub. | Not initialized by the shipped factory; avoid as a supported workflow. |

## Model factory and networks

| Object | Verified signature | Purpose | Notes |
| --- | --- | --- | --- |
| `models.models.create_model` | `create_model(opt)` | Chooses the test model or the conditional GAN. | Asserts `dataset_mode == 'single'` when `model == 'test'`. |
| `models.networks.define_G` | `define_G(input_nc, output_nc, ngf, which_model_netG, norm='batch', use_dropout=False, gpu_ids=[], use_parallel=True, learn_residual=False)` | Builds the generator. | Supports `resnet_9blocks`, `resnet_6blocks`, `unet_128`, and `unet_256`. |
| `models.networks.define_D` | `define_D(input_nc, ndf, which_model_netD, n_layers_D=3, norm='batch', use_sigmoid=False, gpu_ids=[], use_parallel=True)` | Builds the discriminator. | Supports `basic` and `n_layers`. |
| `models.losses.init_loss` | `init_loss(opt, tensor)` | Chooses the content and discriminator losses. | `model=content_gan` selects perceptual loss; `model=pix2pix` selects L1 loss. |
| `models.conditional_gan_model.ConditionalGAN` | `__init__(self, opt)` | Full training model wrapper. | Builds `netG`, `netD`, losses, and optimizers. |
| `models.test_model.TestModel` | `__init__(self, opt)` | Inference-only model wrapper. | Requires `opt.isTrain == False` and `model == 'test'`. |

## Utility helpers

| Object | Verified signature | Purpose | Notes |
| --- | --- | --- | --- |
| `util.metrics.PSNR` | `PSNR(img1, img2)` | Computes a simple PSNR metric. | Uses NumPy arrays from `tensor2im`-style outputs. |
| `util.metrics.SSIM` | `SSIM(img1, img2)` | Computes SSIM for tensor inputs. | This is the local helper used in the generated skill; the shipped `test.py` also imports an external `ssim` package. |
| `util.visualizer.Visualizer` | `Visualizer(opt)` | Handles HTML output and logging. | Expects `checkpoints_dir/name` to exist. |
| `util.html.HTML` | `HTML(web_dir, title, reflesh=0)` | Builds the results gallery. | The generated inference wrapper uses it to save restored images. |
| `util.util.mkdirs` | `mkdirs(paths)` | Creates directories. | Useful for checkpoint/result tree setup. |

## Training and inference defaults to remember

- `BaseOptions` includes `--gpu_ids`, `--checkpoints_dir`, `--name`, `--dataset_mode`, `--model`, `--learn_residual`, `--gan_type`, `--resize_or_crop`, and related flags.
- `TrainOptions` adds `--niter`, `--niter_decay`, `--beta1`, `--lr`, `--lambda_A`, `--lambda_B`, `--save_latest_freq`, and `--save_epoch_freq`.
- `TestOptions` adds `--results_dir`, `--which_epoch`, and `--how_many`.
- The generated wrappers keep the source options but remove the brittle hardcoded repository-local overrides.
