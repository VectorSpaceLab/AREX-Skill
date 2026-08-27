# CLI reference

All shell wrappers are launchers; invoke them from the repository root. Training wrappers require the usual `torchrun` shell variables.

## Training

### `scripts/train_vq.sh` -> `tokenizer/tokenizer_image/vq_train.py`
- wrapper env vars: `nnodes`, `nproc_per_node`, `node_rank`, `master_addr`, `master_port`
- required args: `--data-path`, `--cloud-save-path`
- notable args: `--vq-model {VQ-16,VQ-8}`, `--vq-ckpt`, `--finetune`, `--ema`, `--no-local-save`, `--dataset`, `--image-size {256,512}`, `--codebook-size`, `--codebook-embed-dim`, `--disc-start`, `--disc-type`, `--disc-loss`, `--gen-loss`, `--mixed-precision {none,fp16,bf16}`

### `scripts/train_vq_finetune.sh`
- built-in args: `--finetune --disc-start 0 --vq-ckpt ./pretrained_models/vq_ds16_c2i.pt --dataset t2i_image --data-path /path/to/high_aesthetic_10M --data-face-path /path/to/face_2M --cloud-save-path /path/to/cloud_disk`
- caller adds any extra `vq_train.py` flags after the wrapper.

### `scripts/train_vq_finetune_continue.sh`
- same as the finetune wrapper, but no default `--vq-ckpt`; caller supplies the resume checkpoint.

## Reconstruction and validation

### `scripts/reconstruct_vq.sh` -> `tokenizer/tokenizer_image/reconstruction_vq_ddp.py`
- required: `--data-path`
- notable: `--dataset {imagenet,coco}`, `--vq-model {VQ-16,VQ-8}`, `--vq-ckpt`, `--codebook-size`, `--codebook-embed-dim`, `--image-size {256,384,512}`, `--image-size-eval`, `--sample-dir`, `--per-proc-batch-size`, `--global-seed`, `--num-workers`

### `scripts/validate_vq.sh` -> `tokenizer/validation/val_ddp.py`
- required: `--data-path`
- notable: `--dataset {imagenet,coco}`, `--image-size {256,512}`, `--sample-dir`, `--per-proc-batch-size`, `--global-seed`, `--num-workers`

### `scripts/reconstruct_vqgan.sh` -> `tokenizer/vqgan/reconstruction_vqgan_ddp.py`
- required: `--data-path`
- notable: `--dataset {imagenet,coco}`, `--vqgan`, `--image-size {256,512}`, `--sample-dir`, `--per-proc-batch-size`, `--global-seed`, `--num-workers`

### `scripts/reconstruct_vae.sh` -> `tokenizer/vae/reconstruction_vae_ddp.py`
- required: `--data-path`
- notable: `--dataset {imagenet,coco}`, `--vae {sdxl-vae,sd-vae-ft-mse}`, `--image-size {256,512}`, `--sample-dir`, `--per-proc-batch-size`, `--global-seed`, `--num-workers`

### `scripts/reconstruct_consistency_decoder.sh` -> `tokenizer/consistencydecoder/reconstruction_cd_ddp.py`
- required: `--data-path`
- notable: `--dataset {imagenet,coco}`, `--image-size {256,512}`, `--sample-dir`, `--per-proc-batch-size`, `--global-seed`, `--num-workers`

### `scripts/check_image_codes.py`
- required: `--code-path`, `--vq-ckpt`
- notable: `--output-path`, `--nrow`, `--vq-model {VQ-16,VQ-8}`, `--codebook-size`, `--codebook-embed-dim`, `--image-size {256,384,448,512}`, `--downsample-size {8,16}`, `--seed`

## Demo entry points

### `tokenizer/tokenizer_image/vq_demo.py`
- `--image-path`, `--output-dir`, `--suffix`, `--vq-model`, `--vq-ckpt`, `--codebook-size`, `--codebook-embed-dim`, `--image-size`, `--seed`

### `tokenizer/vqgan/taming_vqgan_demo.py`
- `--image-path`, `--vqgan`, `--image-size`, `--seed`

### `tokenizer/vae/sd_vae_demo.py`
- `--image-path`, `--vae`, `--image-size`, `--seed`

### `tokenizer/consistencydecoder/cd_demo.py`
- `--image-path`, `--image-size`, `--seed`

## Torchrun defaults in wrappers
- training wrappers expect shell variables for multi-node launches.
- reconstruction and validation wrappers use the repo's single-node defaults and fixed master ports.
