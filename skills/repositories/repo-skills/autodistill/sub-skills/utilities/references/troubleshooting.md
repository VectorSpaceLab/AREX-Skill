# Utility Troubleshooting

Use this when Autodistill helpers fail around image conversion, plotting, video splitting, dataset movement, or Roboflow synchronization.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `return_format must be one of ...` | Typo or unsupported return format | Use exactly `PIL`, `cv2`, or `numpy`. |
| `<path> is not a valid file path or URI` | Missing file, relative path from wrong working directory, or unsupported URI | Resolve the file path before calling `load_image`; use a local fixture for tests. |
| URL image load hangs/fails | Network unavailable, invalid URL, TLS/proxy issue, or non-image response | Prefer local images; only use URL branch after network approval. |
| OpenCV returns `None` or colors look wrong | File unreadable or RGB/BGR conversion mismatch | Validate with Pillow, then use `load_image(..., return_format="cv2")` for cv2-style inputs. |
| Plot does not display | Headless environment or non-interactive backend | Use `plot(..., raw=True)` and save/inspect the returned array. |
| Labels crash in `plot` | Detection `class_id` or `confidence` missing/incompatible with `classes` | Check `detections.class_id`, `detections.confidence`, and class index bounds. |
| `compare` is slow or downloads weights | It runs every model on every image | Start with one model and one image; verify plugin/model cache and hardware first. |
| `split_data` moved or converted files unexpectedly | It mutates the output dataset layout by moving images/labels and converting `.png`/`.jpeg` | Run it only on a generated output folder, not source data; keep backups if needed. |
| Video frame splitting output is empty | Wrong video path, unsupported extension, stride too large, or source path issue | Test with a tiny `.mp4`; inspect discovered files and `source_path` before large jobs. |
| Roboflow sync prompts/errors | Credentials, network, workspace/project access, or batch id required | Do not run as dry run; obtain explicit credentials and destination approval. |

## Debug Order

1. Run `check_image_loading.py` with the local default fixture.
2. Test your actual local file path with `--image`.
3. Convert to the exact format expected by the plugin.
4. Use `raw=True` for plotting in headless contexts.
5. Only then try URL, video, or Roboflow branches after approval.
