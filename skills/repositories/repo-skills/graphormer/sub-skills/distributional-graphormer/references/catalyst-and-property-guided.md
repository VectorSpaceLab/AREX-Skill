# Catalyst and property-guided workflows

These workflows are the most script-like parts of the DiG subtree. They both use
Graphormer diffusion-style fairseq commands, external LMDB datasets, and GPU
training/sampling loops.

## Catalyst adsorption

### Training

Typical command shape:

```bash
python -m torch.distributed.launch --nproc_per_node=<num_gpus> --master_port=<port> \
  $(which fairseq-train) \
  --user-dir ./graphormer --ddp-backend legacy_ddp --task graph_diffusion \
  --data-path ./dataset/ \
  --arch graphormer_diff_base \
  --num-workers 16 \
  --train-subset train-100 \
  --valid-subset grid-1681620 \
  --batch-size <batch_size> \
  --validate-interval 1 \
  --max-update 1 \
  --max-epoch 1 \
  --optimizer adam --adam-betas '(0.9, 0.98)' \
  --lr 2e-4 --lr-scheduler polynomial_decay \
  --num-diffusion-timesteps 5000 \
  --diffusion-beta-schedule sigmoid \
  --diffusion-sampling ddpm \
  --ddim-steps 50 \
  --diffusion-beta-end 2e-3 \
  --warmup-updates 0 \
  --total-num-update 1 \
  --keep-best-checkpoints 5 --keep-last-epochs 5 \
  --save-dir <save_dir> \
  --best-checkpoint-metric kde_kl \
  --criterion oc_kde \
  --kde-temperature 1.0 \
  --pbc-cutoff 6.0 \
  --pbc-approach cutoff \
  --diffusion-noise-std 1.0 \
  --fp16 \
  --batch-size-valid <batch_size> \
  --num-epsilon-estimator 1 \
  --n-kde-samples 1 \
  --result-save-dir <save_dir> \
  --seed 0
```

### Sampling and density

The source material uses the same fairseq diffusion stack with a different
validation subset and, for density calculation, a `z` offset. A bundled command
renderer should keep these knobs visible:

- GPU count and device selection
- batch size per GPU
- save directory
- criterion (`oc_kde` or `flow_ode_calc_density`)
- validation subset name
- whether density needs a `z` offset

## Property-guided generation

### Training

Typical command shape:

```bash
python -m torch.distributed.launch --nproc_per_node=<num_gpus> --master_port=<port> \
  $(which fairseq-train) \
  --user-dir ./graphormer --ddp-backend legacy_ddp --task graph_diffusion \
  --data-path ./dataset/rss_carbon/ \
  --arch graphormer_diff_base \
  --num-workers 16 \
  --train-subset all_last_conf_10x \
  --valid-subset sampling_natoms_<n_atoms> \
  --batch-size <batch_size> \
  --validate-interval 1 \
  --max-update 1 \
  --max-epoch 1 \
  --optimizer adam --adam-betas '(0.9, 0.98)' \
  --lr 2e-4 --lr-scheduler polynomial_decay \
  --num-diffusion-timesteps 500 \
  --diffusion-beta-schedule sigmoid \
  --diffusion-sampling ode \
  --ddim-steps 50 \
  --diffusion-beta-end 2e-2 \
  --warmup-updates 0 \
  --total-num-update 1 \
  --keep-best-checkpoints 5 --keep-last-epochs 5 \
  --save-dir <save_dir> \
  --best-checkpoint-metric loss \
  --criterion diffusion_loss \
  --pbc-cutoff 20.0 \
  --pbc-approach cutoff \
  --diffusion-noise-std 1.0 \
  --fp16 \
  --batch-size-valid <batch_size> \
  --seed 1 \
  --lattice-size 4.0 \
  --conditioned-ode-factor <factor> \
  --device-id 0 \
  --target-bandgap-interval <target> \
  --target-bandgap-softmax-temperature 1.0 \
  --sampling-result-dir <save_dir> \
  --gpu-device-id-record 0 \
  --seed-record 1
```

### Sampling

The sampling command family keeps the same diffusion model but changes the
validation subset, target bandgap conditioning, and result directories. Treat
those runs as GPU-heavy and data-dependent.

## Advice

- do not collapse these workflows into the core Graphormer property-prediction
  sub-skill; they are distinct research code
- always check external data layout before rendering a command as executable
- prefer the command renderer for a reviewable plan, not as proof that the
  workflow is runnable on the current host
