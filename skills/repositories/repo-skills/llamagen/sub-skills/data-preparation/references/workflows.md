# Data-preparation workflows

The verified environment already includes the core preprocessing stack: `torch 2.2.1+cu121`, `torchvision 0.17.1+cu121`, `transformers 4.41.2`, `tensorflow-cpu 2.16.1`, `sentencepiece`, `ftfy`, `beautifulsoup4`, `pandas`, and `accelerate`.

## 1. ImageNet code extraction for c2i
Use `scripts/extract_codes_c2i.sh` to launch `autoregressive/train/extract_codes_c2i.py`.

- Input root must be an ImageFolder-style tree with class subdirectories.
- The default dataset is `imagenet`.
- Output tree:
  - `${code_path}/imagenet${image_size}_codes/`
  - `${code_path}/imagenet${image_size}_labels/`
- Each input image writes one `.npy` code file and one `.npy` label file.
- `--ten-crop` stores a 10-way augmentation axis; without it, the helper still writes a 2-way flip axis.
- This cache is consumed by `dataset/imagenet.py::build_imagenet_code`.

## 2. T5 feature extraction for t2i
Use `scripts/extract_flan_t5_feat_laion_coco_stage1.sh`, `scripts/extract_flan_t5_feat_stage2.sh`, or `scripts/extract_flan_t5_feat_trunc_stage2.sh`.

- Input root is a directory of `.jsonl` files.
- `--data-start` and `--data-end` select inclusive positions from the sorted `.jsonl` list.
- `caption-key` choices are `blip`, `llava`, and `llava_first`.
- `--trunc-caption` trims the caption at the first period before embedding.
- Output tree:
  - `${t5_path}/<jsonl_stem>/<line_index>.npy`
- Each feature file stores a `float32` array with shape `[1, token_count, 2048]` after attention-mask trimming.
- Stage-2 training can pair `t5_feat_path` with `short_t5_feat_path` as a second cache root that mirrors the same subfolder names.
- This cache is consumed by `dataset/t2i.py`.

## 3. OpenImages manifest generation
Use `scripts/build_openimage_index.py`.

- It scans `openimages_0001` through `openimages_0047` by default.
- It writes `${data_path}/image_paths.json` unless `--output-path` overrides that location.
- The manifest stores relative paths such as `openimages_0001/000123.jpg`.
- `dataset/openimage.py` loads this file and joins each relative path against `data_path`.

## 4. Sanity checks for cached files
- Verify the ImageNet code tree has both `imagenet${size}_codes/` and `imagenet${size}_labels/`.
- Verify T5 feature trees mirror the `.jsonl` basenames that produced them.
- Verify OpenImages manifests only contain relative paths that exist under the dataset root.
- If a tree is partial, prefer deleting it and rerunning the same slice into a fresh output root rather than mixing old and new files.
