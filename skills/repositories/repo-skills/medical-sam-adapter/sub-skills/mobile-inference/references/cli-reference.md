# MobileSAMv2 CLI reference

## Source-compatible arguments and defaults

The standalone `Inference.py` parser declares the following flags. Spelling and
capitalization are significant.

| Argument | Type | Source default | Meaning and source behavior |
|---|---|---:|---|
| `--ObjectAwareModel_path` | `str` | `./PromptGuidedDecoder/ObjectAwareModel.pt` | Detector/ObjectAwareModel checkpoint path. The source `create_model()` does not consistently consume the parsed value and instead uses a relative path of its own. |
| `--Prompt_guided_Mask_Decoder_path` | `str` | `./PromptGuidedDecoder/Prompt_guided_Mask_Decoder.pt` | Prompt-guided mask-decoder checkpoint. The source model factory also uses a relative path rather than reliably using the parsed value. |
| `--encoder_path` | `str` | `./` | Declared custom encoder path. The source `main()` does not use this value for its actual encoder selection. |
| `--img_path` | `str` | `./test_images/` | Directory passed to `os.listdir`; despite the help text, the source expects a directory, not one image file. |
| `--imgsz` | `int` | `1024` | Detector image size. |
| `--iou` | `float` | `0.9` | Detector/NMS IoU threshold. |
| `--conf` | `float` | `0.4` | Detector object-confidence threshold. |
| `--retina` | `bool` using `type=bool` | `True` | Passed to the detector as `retina_masks`. With Python `type=bool`, the string `False` is truthy; do not rely on `--retina False` to disable it. |
| `--output_dir` | `str` | `./` | Output prefix in the source. The source concatenates it with each image name, so a trailing separator is effectively required. |
| `--encoder_type` | choice, no default | `None` | Parser choices: `tiny_vit`, `sam_vit_h`, `mobile_sam`, `efficientvit_l2`, `efficientvit_l1`, `efficientvit_l0`. |

The bundled `scripts/run_mobile_samv2.py` preserves these flag names and
source defaults in its help, but intentionally requires explicit values for
`--ObjectAwareModel_path`, `--Prompt_guided_Mask_Decoder_path`,
`--encoder_path`, `--encoder_type`, `--img_path`, and `--output_dir`. This avoids
current-working-directory ambiguity and prevents an accidental run with a
missing encoder selection. It also adds:

| Helper flag | Behavior |
|---|---|
| `--preflight` | Explicitly request validation. The helper is preflight-only even without this flag. |
| `--dry-run` | Alias for `--preflight`. |
| `--allow-overwrite` | Permit already-existing output filenames during validation. It never writes files. |

The helper rejects non-finite values, `imgsz <= 0`, `iou` or `conf` outside
`[0, 1]`, URLs, missing/non-file checkpoints, unsupported checkpoint
extensions, missing image directories, unsupported image extensions, and
output collisions. It performs these checks with the Python standard library
only, before any torch, OpenCV, detector, or model import.

## Operational encoder mapping

The parser accepts six names, but the standalone source path dictionary has
only three usable entries:

| `--encoder_type` | Source mapping | Required local encoder checkpoint |
|---|---|---|
| `tiny_vit` | TinyViT encoder | usually a MobileSAM/TinyViT `.pt` checkpoint |
| `sam_vit_h` | SAM ViT-H encoder | a compatible ViT-H encoder `.pt` checkpoint |
| `efficientvit_l2` | EfficientViT-L2 encoder | a compatible EfficientViT-L2 `.pt` checkpoint |

`mobile_sam`, `efficientvit_l1`, and `efficientvit_l0` are parser-only names:
they have no entry in the source mapping and fail before a model can be
selected. Do not silently substitute a checkpoint or infer a path from the
name. The package registry additionally exposes `vit_b`, `vit_l`, and other
builders, but that does not make them supported by this standalone CLI.
