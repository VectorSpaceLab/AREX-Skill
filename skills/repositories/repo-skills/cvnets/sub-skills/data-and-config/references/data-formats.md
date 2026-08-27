# CVNets Data Formats

## Purpose

Read this when a config or loader problem is really about how the repo expects the data to be laid out on disk or how a modality is encoded.

## Config and split layout

- CVNets uses dotted config keys after flattening YAML.
- Common split fields are `dataset.root_train`, `dataset.root_val`, and `dataset.root_test`.
- The effective training batch size is controlled by the per-GPU batch setting plus the number of visible GPUs and any accumulation frequency.
- Most real workflows also depend on the matching `dataset.category` and `dataset.name` values.

## Image classification, detection, and segmentation

- Classification recipes usually load a standard image dataset with train/val/test roots and a sampler/collate pair that matches the backbone.
- Detection and segmentation recipes reuse classification backbones but add task-specific class-count, anchor, matcher, or decoder settings.
- `tests/data/datasets/classification/test_base_image_classification_dataset.py`, `tests/data/datasets/classification/test_mock_imagenet.py`, and `tests/data/datasets/segmentation/test_mock_ade20k.py` are the main shape references for those families.

## CLIP and other image-text layouts

- The zero-shot image-text path expects image paths plus prompt lists.
- The mock zero-shot dataset test returns a tuple of `(img_path, text_prompts, target)`.
- The RangeAugment CLIP example stores image-text pairs in tar files and uses a separate metadata file that maps shard ranges to tar names.
- CLIP text tokenization depends on `text_tokenizer.clip.merges_path` and `text_tokenizer.clip.encoder_json_path`.

## Audio and ByteFormer layouts

- Speech Commands v2 tests mock `torchaudio.load` and use `dataset.root_train`, `dataset.root_val`, and `dataset.root_test` alongside audio augmentation settings.
- ByteFormer image recipes use byte-saving and shuffling settings inside `image_augmentation.*`.
- ByteFormer audio recipes use `audio_augmentation.torchaudio_save.*` settings and a byte-aware collate function.
- The collate tests expect padded byte batches and a configurable `model.classification.byteformer.padding_index`.

## Video layouts

- The video-reader registry supports PyAV and optional decord backends.
- `video_reader.frame_stack_format` controls whether the tensor layout is channel-first or sequence-first.
- The video reader tests use dummy `.mov` files and assert that clip counts, frame counts, and audio/video timestamps stay aligned.
- If decord is absent, decord-specific tests skip rather than fail.

## Sampler and collate names

- Training and validation collate functions are selected independently.
- Test-time collate selection is separate from train/val.
- The sampler registry supports batch-style, variable-batch, video, and chain-style sampling paths.
- DDP may switch sampler names to DDP-specific variants automatically.

## What to check before handing off to another sub-skill

1. The config can be loaded without unexpected key warnings.
2. The selected dataset/category pair matches the intended model family.
3. The selected sampler and collate names match the modality.
4. Any tokenizer, byte, video, or audio backend needed by the recipe is installed.
