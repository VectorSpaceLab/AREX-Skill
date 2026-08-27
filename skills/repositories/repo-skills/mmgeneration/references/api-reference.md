# API Reference

## Purpose

Read this when you need the verified public function, class, or registry names for MMGeneration workflows.

## Package-level exports

### `mmgen.apis`

Verified public functions:

- `init_model(config, checkpoint=None, device='cuda:0', cfg_options=None)`
- `sample_unconditional_model(model, num_samples=16, num_batches=4, sample_model='ema', **kwargs)`
- `sample_conditional_model(model, num_samples=16, num_batches=4, sample_model='ema', label=None, **kwargs)`
- `sample_img2img_model(model, image_path, target_domain=None, **kwargs)`
- `sample_ddpm_model(model, num_samples=16, num_batches=4, sample_model='ema', same_noise=False, **kwargs)`
- `set_random_seed(seed, deterministic=False, use_rank_shift=True)`
- `train_model(model, dataset, cfg, distributed=False, validate=False, timestamp=None, meta=None)`

`init_model` accepts either a config file path or an `mmcv.Config`, loads a checkpoint if provided, moves the model to the requested device, and stores the config on `model._cfg`.

### `mmgen.models`

Builders and registries:

- `build_model(cfg, train_cfg=None, test_cfg=None)`
- `build_module(cfg, default_args=None)`
- `MODELS`
- `MODULES`

Verified model constructors used in docs/tests:

- `StaticUnconditionalGAN(generator, discriminator, gan_loss, disc_auxiliary_loss=None, gen_auxiliary_loss=None, train_cfg=None, test_cfg=None)`
- `ProgressiveGrowingGAN(generator, discriminator, gan_loss, disc_auxiliary_loss, gen_auxiliary_loss=None, train_cfg=None, test_cfg=None)`
- `BasicConditionalGAN(generator, discriminator, gan_loss, disc_auxiliary_loss=None, gen_auxiliary_loss=None, train_cfg=None, test_cfg=None, num_classes=None)`
- `SinGAN(generator, discriminator, gan_loss, disc_auxiliary_loss, gen_auxiliary_loss=None, train_cfg=None, test_cfg=None)`
- `MSPIEStyleGAN2(generator, discriminator, gan_loss, disc_auxiliary_loss=None, gen_auxiliary_loss=None, train_cfg=None, test_cfg=None)`
- `StaticTranslationGAN(generator, discriminator, gan_loss, *args, pretrained=None, disc_auxiliary_loss=None, gen_auxiliary_loss=None, **kwargs)`
- `Pix2Pix(*args, **kwargs)`
- `CycleGAN(*args, **kwargs)`
- `BasicGaussianDiffusion(denoising, ddpm_loss, betas_cfg, num_timesteps=1000, num_classes=0, sample_method='DDPM', timestep_sampler='UniformTimeStepSampler', train_cfg=None, test_cfg=None)`

### `mmgen.datasets`

Builders and dataset classes:

- `build_dataset(cfg, default_args=None)`
- `build_dataloader(dataset, samples_per_gpu, workers_per_gpu, num_gpus=1, dist=True, shuffle=True, seed=None, persistent_workers=False, **kwargs)`
- `UnconditionalImageDataset(imgs_root, pipeline, test_mode=False)`
- `PairedImageDataset(dataroot, pipeline, test_mode=False, testdir='test')`
- `UnpairedImageDataset(dataroot, pipeline, test_mode=False, domain_a=None, domain_b=None)`
- `GrowScaleImgDataset(imgs_roots, pipeline, len_per_stage=1000000, gpu_samples_per_scale=None, gpu_samples_base=32, test_mode=False)`
- `SinGANDataset(img_path, min_size, max_size, scale_factor_init, num_samples=-1)`
- `QuickTestImageDataset(*args, size=None, **kwargs)`

### `mmgen.core.evaluation`

Verified helpers:

- `build_metric(cfg)`
- `offline_evaluation(model, data_loader, metrics, logger, basic_table_info, batch_size, samples_path=None, **kwargs)`
- `online_evaluation(model, data_loader, metrics, logger, basic_table_info, batch_size, **kwargs)`
- `make_metrics_table(train_cfg, ckpt, eval_info, metrics)`
- `make_vanilla_dataloader(img_path, batch_size, dist=False)`
- `slerp(a, b, percent)`

Metric classes and signatures:

- `FID(num_images, image_shape=None, inception_pkl=None, bgr2rgb=True, inception_args={'normalize_input': False})` lives in `mmgen.core.evaluation.metrics`.
- `PPL(num_images, image_shape=None, crop=True, epsilon=0.0001, space='W', sampling='end', latent_dim=512)`
- `IS(num_images, image_shape=None, bgr2rgb=True, resize=True, splits=10, use_pil_resize=True, inception_args={...})`
- `MS_SSIM(num_images, image_shape=None)`
- `PR(num_images, image_shape=None, num_real_need=None, full_dataset=False, k=3, bgr2rgb=True, vgg16_script='work_dirs/cache/vgg16.pt', row_batch_size=10000, col_batch_size=10000)`
- `SWD(num_images, image_shape)`
- `GaussianKLD(num_images, base='e', reduction='batchmean')`

### Hooks, runners, and utilities

- `GenerativeEvalHook(dataloader, interval=1, dist=True, metrics=None, sample_kwargs=None, save_best_ckpt=True, best_metric='fid')`
- `TranslationEvalHook(*args, target_domain, **kwargs)`
- `ExponentialMovingAverageHook(module_keys, interp_mode='lerp', interp_cfg=None, interval=-1, start_iter=0, momentum_policy='fixed', momentum_cfg=None)`
- `VisualizationHook(output_dir, res_name_list, interval=-1, filename_tmpl='iter_{}.png', rerange=True, bgr2rgb=True, nrow=1, padding=4)`
- `VisualizeUnconditionalSamples(output_dir, fixed_noise=True, num_samples=16, interval=-1, filename_tmpl='iter_{}.png', rerange=True, bgr2rgb=True, nrow=4, padding=0, kwargs=None)`
- `DynamicIterBasedRunner(*args, is_dynamic_ddp=False, pass_training_status=False, fp16_loss_scaler=None, use_apex_amp=False, **kwargs)`
- `LinearLrUpdaterHook(target_lr=0, start=0, interval=1, **kwargs)`
- `build_optimizers(model, optimizer_cfg)`
- `collect_env()`
- `download_from_url(url, dest_path=None, dest_dir='~/.cache/openmmlab/mmgen/', hash_prefix=None)`
- `get_root_logger(log_file=None, log_level=20, file_mode='w')`
- `sync_random_seed(seed=None, device='cuda')`

## Notes for future agents

- `mmgen.core.__init__` re-exports the major subpackages, but not every class is surfaced at the same import level. For example, `FID` is easiest to import from `mmgen.core.evaluation.metrics`.
- Use `inspect.signature()` on a live install if you need to confirm a parameter order or default before writing a user-facing helper.
