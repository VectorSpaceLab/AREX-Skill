# Training workflows

The helper scripts in this sub-skill are dry-run only: they print canonical commands and never launch training.

## Choose a path
1. Validate dataset layout in `../setup-and-data/SKILL.md`.
2. If you need feature-conditioned training with cached maps, finish `../instance-features/SKILL.md` first.
3. Run `scripts/inspect_training_setup.py --repo-root <repo-root>`.
4. Print the canonical command with `scripts/build_train_command.py --repo-root <repo-root> --recipe <recipe>`.
5. Launch manually only after checking memory, checkpoints, and backend caveats.

## Canonical recipes

| Recipe | Canonical command | When to use | Notes |
|---|---|---|---|
| `512p` | `cd "<repo-root>" && python train.py --name label2city_512p` | Baseline label-only training | Closest to the README quick-start.
| `512p_feat` | `cd "<repo-root>" && python train.py --name label2city_512p_feat --instance_feat` | Feature-conditioned 512p training | This variant trains the encoder on the fly; it does **not** require `--load_features`.
| `1024p_12G` | `cd "<repo-root>" && python train.py --name label2city_1024p --netG local --ngf 32 --num_D 3 --load_pretrain checkpoints/label2city_512p/ --niter_fix_global 20 --resize_or_crop crop --fineSize 1024` | 2048×1024 on limited VRAM | Cropped full-resolution recipe; lower memory, lower fidelity than the 24G recipe.
| `1024p_24G` | `cd "<repo-root>" && python train.py --name label2city_1024p --netG local --ngf 32 --num_D 3 --load_pretrain checkpoints/label2city_512p/ --niter 50 --niter_decay 50 --niter_fix_global 10 --resize_or_crop none` | Full-resolution 2048×1024 training | Uses the entire resolution and expects much more VRAM.
| `1024p_feat_12G` | `cd "<repo-root>" && python train.py --name label2city_1024p_feat --netG local --ngf 32 --num_D 3 --load_pretrain checkpoints/label2city_512p_feat/ --niter_fix_global 20 --resize_or_crop crop --fineSize 896 --instance_feat --load_features` | Feature-conditioned 2048×1024 on limited VRAM | The feature-cache step lives in `../instance-features/SKILL.md`; this row is only the training half.
| `1024p_feat_24G` | `cd "<repo-root>" && python train.py --name label2city_1024p_feat --netG local --ngf 32 --num_D 3 --load_pretrain checkpoints/label2city_512p_feat/ --niter 50 --niter_decay 50 --niter_fix_global 10 --resize_or_crop none --instance_feat --load_features` | Feature-conditioned full-resolution training | The feature-cache step lives in `../instance-features/SKILL.md`; this row is only the training half.
| `512p_multigpu` | `cd "<repo-root>" && python train.py --name label2city_512p --batchSize 8 --gpu_ids 0,1,2,3,4,5,6,7` | Baseline multi-GPU run | The model uses `DataParallel`, not DDP; README says multi-GPU was not fully tested.
| `512p_fp16` | `cd "<repo-root>" && python -m torch.distributed.launch train.py --name label2city_512p --fp16` | FP16/Apex run | Legacy launcher style; requires NVIDIA Apex.
| `512p_fp16_multigpu` | `cd "<repo-root>" && python -m torch.distributed.launch train.py --name label2city_512p --batchSize 8 --gpu_ids 0,1,2,3,4,5,6,7 --fp16` | FP16 plus multiple GPUs | Legacy launcher style; requires NVIDIA Apex and enough VRAM for the batch size.

## Debug and smoke runs

`--debug` reduces the run to one epoch, one-display/one-print cadence, and a 10-sample dataset cap. It is useful for flow checks, but it is **not** guaranteed to write a checkpoint because the default save cadence is still large.

For a checkpoint smoke, use a debug command with explicit save overrides:

```bash
cd "<repo-root>" && python train.py --name <smoke> --debug --no_vgg_loss --save_latest_freq 1 --save_epoch_freq 1
```

## Resume and pretrain semantics

- `--continue_train` resumes the same experiment from `checkpoints/<name>/iter.txt` and the latest saved weights.
- `--load_pretrain` points at another checkpoint directory and bootstraps a new run from those weights.
- `--which_epoch` selects the checkpoint label inside the chosen directory; the default is `latest`.
- For 1024p staging, the normal pattern is: train 512p, then load the 512p checkpoint into the 1024p run.
