# Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `ImageFolder` cannot find classes or the extractor sees the wrong labels | Wrong dataset root layout | For ImageNet, the root must contain class subdirectories. If you are working from a flat image folder, do not point the ImageNet extractor at it. |
| `FileNotFoundError` for `imagenet256_codes` or `imagenet256_labels` | Code cache missing, stale, or written to the wrong root | Rebuild the cache with `scripts/extract_codes_c2i.sh` into a fresh `code-path`. Do not mix partial and fresh trees. |
| Downstream training says a T5 feature file is missing | T5 cache tree basename does not match the source `.jsonl` name | Check that the output tree is `${t5_path}/<jsonl_stem>/<line_index>.npy` and that `short_t5_feat_path` mirrors the same nested folders. |
| Caption conditioning looks wrong or quality drops sharply | Wrong `--caption-key` or missing `--trunc-caption` choice | Use `blip` for the stage-1 LAION/COCO cache, and use the truncated variant only when you intentionally want the stage-2 short-caption cache. |
| `AutoTokenizer` / model download fails | Local T5 model cache is missing or Hugging Face access is blocked | Populate `--t5-model-path` with a local `flan-t5-xl` cache first, or mirror the required Hugging Face files into `pretrained_models/t5-ckpt/`. |
| The output tree is only partially written | Run was interrupted partway through | For T5 caches, rerun the same slice and overwrite the same filenames. For ImageNet code caches, it is usually cleaner to delete the incomplete output root and rerun from scratch. |
| OpenImages manifest misses files or includes bad paths | Folder naming does not match the helper defaults, or some images are unreadable | The default scan is `openimages_0001` through `openimages_0047`. If your tree uses a different prefix or folder width, pass matching `--folder-prefix`, `--folder-start`, `--folder-end`, and `--folder-width`. |
| The manifest helper skips images you expected to keep | An image file is corrupted or not a supported extension | Run the helper in `--strict` mode to fail fast, then fix the bad path or remove the unreadable file. |

## Fast checks

1. Confirm the input root layout before starting extraction.
2. Confirm the cache root names before handing them to training.
3. Confirm the caption key and truncation mode before building T5 features.
4. Confirm OpenImages paths are relative to `data_path`.
