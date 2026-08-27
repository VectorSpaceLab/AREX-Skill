# CLI reference

All shell wrappers resolve the repo root and then run `torchrun` from there.

## `scripts/extract_codes_c2i.sh`
Launcher:

- `torchrun --nnodes=1 --nproc_per_node=8 --node_rank=0 --master_port=12335 autoregressive/train/extract_codes_c2i.py`

Underlying CLI:

- required: `--data-path`, `--code-path`, `--vq-ckpt`
- notable: `--dataset {imagenet,coco,openimage,pexels,t2i_image,t2i,t2i_code}`, `--vq-model {VQ-16,VQ-8}`, `--codebook-size`, `--codebook-embed-dim`, `--image-size {256,384,448,512}`, `--ten-crop`, `--crop-range`, `--global-seed`, `--num-workers`, `--debug`

Notes:

- `--ten-crop` stores a 10-way augmentation axis.
- Without `--ten-crop`, the script still writes a 2-way flip axis.
- The output tree is dense and numeric; use a fresh `code-path` when you want a clean rerun.

## `scripts/extract_flan_t5_feat_laion_coco_stage1.sh`
Launcher:

- `torchrun --nnodes=1 --nproc_per_node=8 --node_rank=0 --master_port=12337 language/extract_t5_feature.py --data-path /path/to/laion_coco50M --t5-path /path/to/laion_coco50M_flan_t5_xl --caption-key blip`

Underlying CLI:

- required: `--data-path`, `--t5-path`, `--data-start`, `--data-end`
- notable: `--caption-key {blip,llava,llava_first}`, `--trunc-caption`, `--t5-model-path`, `--t5-model-type flan-t5-xl`, `--precision {none,fp16,bf16}`, `--global-seed`, `--num-workers`

Notes:

- `--data-start` and `--data-end` are inclusive file-index bounds over the sorted `.jsonl` listing.
- `--trunc-caption` removes the text after the first period before embedding.
- The script expects a local T5 cache unless the model can be downloaded from Hugging Face.

## `scripts/extract_flan_t5_feat_stage2.sh`
Launcher:

- `torchrun --nnodes=1 --nproc_per_node=8 --node_rank=0 --master_port=12337 language/extract_t5_feature.py --data-path /path/to/high_aesthetic_10M --t5-path /path/to/high_aesthetic_10M_flan_t5_xl`

Underlying CLI:

- same flags as `extract_flan_t5_feat_laion_coco_stage1.sh`

Notes:

- Stage-2 training typically consumes the default caption cache and a matching `short_t5_feat_path` if you build a truncated alternate cache.

## `scripts/extract_flan_t5_feat_trunc_stage2.sh`
Launcher:

- `torchrun --nnodes=1 --nproc_per_node=8 --node_rank=0 --master_port=12337 language/extract_t5_feature.py --data-path /path/to/high_aesthetic_10M --t5-path /path/to/high_aesthetic_10M_trunc_flan_t5_xl --trunc-caption`

Underlying CLI:

- same flags as `extract_flan_t5_feat_laion_coco_stage1.sh`

Notes:

- This variant is for the truncated-caption cache used by stage-2 text conditioning.

## `scripts/build_openimage_index.py`

- required: `--data-path`
- notable: `--output-path`, `--folder-prefix`, `--folder-start`, `--folder-end`, `--folder-width`, `--extensions`, `--workers`, `--strict`

Notes:

- Default output is `image_paths.json` under `data-path`.
- `--strict` makes bad or missing image files fail fast.
- Without `--strict`, invalid image files are skipped with warnings and the manifest is written from the valid subset.
