# CLI reference

## Execution model

- `BaseOptions.parse()` turns `--gpu_ids` into a list of integers and sets the first id as the active CUDA device.
- `models/models.py` wraps the training model in `torch.nn.DataParallel` when GPUs are present and `--fp16` is off.
- When `--fp16` is on, `train.py` initializes Apex AMP and then wraps the model in `DataParallel`.
- There is no true DDP initialization path in `train.py`; `--local_rank` exists in the parser but is not consumed by the training loop.

## Core experiment flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--name` | `label2city` | Experiment name; also the checkpoint directory name under `checkpoints/`.
| `--checkpoints_dir` | `./checkpoints` | Root directory for checkpoints, logs, and HTML previews.
| `--gpu_ids` | `0` | Comma-separated GPU ids. `-1` leaves the list empty, but the training code still calls `.cuda()` in several places, so CPU training is not supported.
| `--batchSize` | `1` | Batch size used by the data loader and print cadence.
| `--model` | `pix2pixHD` | The repo's training model selector.
| `--norm` | `instance` | Normalization layer for the networks.
| `--verbose` | `False` | Prints network and loading details.
| `--fp16` | `False` | Apex AMP path. This is the published FP16 switch; it is not the same thing as `--data_type 16`.
| `--data_type` | `32` | Tensor storage precision knob used by input encoding paths. Do not treat it as a drop-in replacement for Apex AMP.
| `--local_rank` | `0` | Legacy distributed-launch hook; the training loop does not initialize DDP.

## Input and resolution flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--dataroot` | `./datasets/cityscapes/` | Root for the paired training data.
| `--label_nc` | `35` | Number of label channels. Use `0` for RGB-to-RGB translation.
| `--input_nc` | `3` | Input channel count when `label_nc == 0`.
| `--output_nc` | `3` | Output image channel count.
| `--resize_or_crop` | `scale_width` | Baseline preprocessing mode. `none` is the safe full-resolution mode; `crop` is used by the 12G 1024p recipes; `resize_and_crop` is compatibility-risky on current torchvision because `data/base_dataset.py` still calls `transforms.Scale`.
| `--loadSize` | `1024` | Width target for `scale_width` / `resize_and_crop` modes.
| `--fineSize` | `512` | Crop size used by crop-based recipes.
| `--serial_batches` | `False` | Disable shuffling.
| `--no_flip` | `False` | Disable flip augmentation.
| `--nThreads` | `2` | Data-loader workers.
| `--max_dataset_size` | `inf` | Useful for debug runs; `--debug` clamps it to 10.

## Generator and staging flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--netG` | `global` | Generator type. Use `local` for the full-resolution recipes.
| `--ngf` | `64` | Generator width; 1024p recipes reduce it to `32`.
| `--n_downsample_global` | `4` | Global generator depth.
| `--n_blocks_global` | `9` | Residual blocks in the global generator.
| `--n_blocks_local` | `3` | Residual blocks in the local enhancer.
| `--n_local_enhancers` | `1` | Number of local enhancer stages.
| `--niter_fix_global` | `0` | Number of epochs that train only the outer local enhancer before fine-tuning the rest of the generator.

## Feature-conditioning flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--no_instance` | `False` | Drop the instance map from the generator input.
| `--instance_feat` | `False` | Add encoded instance features as a generator input.
| `--label_feat` | `False` | Add encoded label features as a generator input.
| `--feat_num` | `3` | Feature-vector width.
| `--load_features` | `False` | Load precomputed feature maps instead of running the encoder on the fly.
| `--n_downsample_E` | `4` | Encoder depth when features are generated on the fly.
| `--nef` | `16` | Encoder width when features are generated on the fly.
| `--n_clusters` | `10` | Feature-clustering parameter used by the feature workflow; see `../instance-features/SKILL.md`.

### Feature flag interpretation

- `--instance_feat` without `--load_features` means the training loop creates `netE` and computes features during training.
- `--instance_feat --load_features` means the training loop expects feature maps produced by the separate feature workflow.
- `--label_feat` switches the feature source from instance ids to label ids.

## Training, loss, and checkpoint flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--continue_train` | `False` | Resume from the same experiment's latest checkpoint and `iter.txt` cursor.
| `--load_pretrain` | `''` | Load weights from another checkpoint directory before starting a new run.
| `--which_epoch` | `latest` | Checkpoint label to load from the selected directory.
| `--niter` | `100` | Flat-learning-rate epochs.
| `--niter_decay` | `100` | Linear-decay epochs after `niter`.
| `--beta1` | `0.5` | Adam beta1.
| `--lr` | `0.0002` | Adam learning rate.
| `--num_D` | `2` | Number of discriminators; 1024p recipes raise this to `3`.
| `--n_layers_D` | `3` | PatchGAN depth.
| `--ndf` | `64` | Discriminator width.
| `--lambda_feat` | `10.0` | Weight for GAN feature-matching / VGG loss terms.
| `--no_ganFeat_loss` | `False` | Disable discriminator feature matching.
| `--no_vgg_loss` | `False` | Disable VGG feature loss; useful for offline smoke runs.
| `--no_lsgan` | `False` | Switch to vanilla GAN loss.
| `--pool_size` | `0` | Fake-image buffer size. `Pix2PixHDModel.initialize()` raises `NotImplementedError` if `pool_size > 0` and multiple GPUs are used together.

## Logging and debug flags

| Flag | Default | Meaning / caveat |
|---|---|---|
| `--display_freq` | `100` | Display cadence; `--debug` forces it to 1.
| `--print_freq` | `100` | Console logging cadence; `--debug` forces it to 1.
| `--save_latest_freq` | `1000` | Iteration-level checkpoint save cadence.
| `--save_epoch_freq` | `10` | Epoch-level checkpoint save cadence.
| `--no_html` | `False` | Skip `checkpoints/<name>/web/` output.
| `--debug` | `False` | One-epoch, 10-sample, high-frequency smoke mode. It does **not** force a save.
| `--tf_log` | `False` | TensorBoard logging. Requires TensorFlow.

## Recipe-specific reminders

- 512p baseline: simplest first smoke.
- 1024p 12G: crop-based and memory-saving.
- 1024p 24G: full-resolution and much more VRAM hungry.
- FP16: requires Apex.
- Multi-GPU: published script uses `DataParallel` and is documented as untested.
- Full-resolution and debug runs are still subject to the current Python/runtime compatibility caveats documented in `troubleshooting.md`.
