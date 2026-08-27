# Dataset Reference

## COCO captioning

Required paths:

- `--coco_train_image_dir_path`: train2014 image directory
- `--coco_val_image_dir_path`: val2014 image directory
- `--coco_karpathy_json_path`: Karpathy split JSON
- `--coco_annotations_json_path`: caption annotations JSON

Schema notes:

- The Karpathy-style JSON must expose an `images` array.
- Each image entry needs `split`, `filepath`, `filename`, `sentences[0].raw`, and `cocoid`.
- The loader chooses train or val images from `filepath`.

## Flickr30K captioning

Required paths:

- `--flickr_image_dir_path`: Flickr30K image directory
- `--flickr_karpathy_json_path`: Karpathy split JSON
- `--flickr_annotations_json_path`: caption annotations JSON

Schema notes:

- The JSON must expose an `images` array with `split`, `filename`, `sentences[0].raw`, and `cocoid`-style identifiers.
- All images live in one directory; there is no separate val image directory.

## VQAv2

Required paths:

- `--vqav2_train_image_dir_path`
- `--vqav2_train_questions_json_path`
- `--vqav2_train_annotations_json_path`
- `--vqav2_test_image_dir_path`
- `--vqav2_test_questions_json_path`
- `--vqav2_test_annotations_json_path` for local accuracy runs
- `--vqav2_final_test_questions_json_path` for submission filling when annotations are unavailable

Schema notes:

- Image directories must end in `train2014`, `val2014`, or `test2015`.
- Question JSON must contain a `questions` array with `question`, `image_id`, and `question_id`.
- Annotation JSON must contain an `annotations` array with the same question order the dataset expects.
- Images are loaded as `COCO_<split>_<image_id:012d>.jpg`.

## OK-VQA

Required paths:

- `--ok_vqa_train_image_dir_path`
- `--ok_vqa_train_questions_json_path`
- `--ok_vqa_train_annotations_json_path`
- `--ok_vqa_test_image_dir_path`
- `--ok_vqa_test_questions_json_path`
- `--ok_vqa_test_annotations_json_path`

Schema notes:

- The file format matches the VQAv2-style question and annotation layout.
- The image directory naming rule is the same as VQAv2.

## TextVQA

Required paths:

- `--textvqa_image_dir_path`
- `--textvqa_train_questions_json_path`
- `--textvqa_train_annotations_json_path`
- `--textvqa_test_questions_json_path`
- `--textvqa_test_annotations_json_path`

Schema notes:

- The image directory is shared by train and test splits.
- Question JSON must contain `questions` entries with `question`, `image_id`, and `question_id`.
- Annotation JSON must contain `annotations` entries with `question_id`, `image_id`, `answers`, and `multiple_choice_answer`.
- Image files are loaded as `<image_id>.jpg`.

## VizWiz

Required paths:

- `--vizwiz_train_image_dir_path`
- `--vizwiz_train_questions_json_path`
- `--vizwiz_train_annotations_json_path`
- `--vizwiz_test_image_dir_path`
- `--vizwiz_test_questions_json_path`
- `--vizwiz_test_annotations_json_path` for local accuracy runs

Schema notes:

- Question JSON uses the same VQA-style `questions` layout.
- Annotation JSON uses the same `annotations` layout as TextVQA.
- Test image IDs already include the filename, for example `VizWiz_test_00000000.jpg`.
- When annotations are unavailable, the fill workflow uses the test-question file to build the submission JSON.

## ImageNet

Required paths:

- `--imagenet_root`

Schema notes:

- The root must contain `train/` and `val/` folders in ImageFolder layout.
- The class-name mapping comes from the bundled ImageNet class list.

## Hateful Memes

Required paths:

- `--hateful_memes_image_dir_path`
- `--hateful_memes_train_annotations_json_path`
- `--hateful_memes_test_annotations_json_path`

Schema notes:

- Annotation files are JSONL, one object per line.
- Each line needs `id`, `img`, `text`, and `label`.
- `label` maps `0 -> no` and `1 -> yes`.
- Image paths use the basename of `img` inside the provided image directory.
