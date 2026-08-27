# Image Tool Reference

This reference lists the prompt-decorated tools that the controller can expose for image, mask, OCR, Husky, inpainting, and Stable Diffusion / ControlNet workflows.

## How tool names are exposed

- The controller turns every loaded method whose name starts with `inference` into a LangChain tool.
- The tool name is the prompt-decorated `name`, not the Python class name.
- Argument parsing is comma-sensitive, so the exact grammar matters.

## Mask, OCR, caption, and Husky tools

| Tool name | Python class.method | Input grammar | Return | Notes |
| --- | --- | --- | --- | --- |
| `Segment Anything On Image` | `SegmentAnything.inference` | `image_path` | mask PNG | Full-scene SAM segmentation. |
| `Segment The Clicked Region In The Image` | `SegmentAnything.inference_by_mask` | `image_path,mask_path` | mask PNG | Refines a clicked region. Use both paths. |
| `Extract The Masked Anything` | `ExtractMaskedAnything.inference` | `image_path,mask_path` | RGBA PNG | Keeps the masked pixels and alpha. |
| `Remove the Masked Object` | `LDMInpainting.inference` | `image_path,mask_path` | inpainted PNG | Removal / inpainting path. |
| `Replace The Masked Object` | `ReplaceMaskedAnything.inference` | `image_path,mask_path,prompt` | edited PNG | Replacement path with Stable Diffusion inpainting. |
| `Recognize The Optical Characters By Clicking` | `ImageOCRRecognition.inference_by_mask` | `image_path,mask_path` | text | Returns `No characters in the image` when the selection is empty or no OCR text overlaps the mask. |
| `Recognize All Optical Characters` | `ImageOCRRecognition.inference` | `image_path` | list of text strings | Full-image OCR. |
| `Get Photo Description` | `HuskyVQA.inference_captioning` | `image_path` | text | Husky captioning used when an image is uploaded. |
| `Answer Question About The Image` | `HuskyVQA.inference` | `image_path,question` | text | Commas are allowed after the first comma because the question is rejoined. |
| `Answer Question About The Masked Image` | `HuskyVQA.inference_by_mask` | `image_path,mask_path,question` | text | Masks the region first, then asks Husky. |
| `Get Photo Description` | `ImageCaptioning.inference` | `image_path` | text | BLIP caption fallback if loaded. |
| `Answer Question About The Image` | `VisualQuestionAnswering.inference` | `image_path,question` | text | BLIP VQA fallback if loaded. |

## Stable Diffusion and ControlNet generators

| Tool name | Python class.method | Input grammar | Return | Notes |
| --- | --- | --- | --- | --- |
| `Instruct Image Using Text` | `InstructPix2Pix.inference` | `image_path,text` | edited PNG | Direct style edit from a prompt. |
| `Generate Image From User Input Text` | `Text2Image.inference` | `text` | generated PNG | Pure text-to-image. |
| `Edge Detection On Image` | `Image2Canny.inference` | `image_path` | canny PNG | Deterministic preprocessor. |
| `Generate Image Condition On Canny Image` | `CannyText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from canny. |
| `Line Detection On Image` | `Image2Line.inference` | `image_path` | line PNG | Deterministic preprocessor. |
| `Generate Image Condition On Line Image` | `LineText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from line art. |
| `Hed Detection On Image` | `Image2Hed.inference` | `image_path` | HED boundary PNG | Deterministic preprocessor. |
| `Generate Image Condition On Soft Hed Boundary Image` | `HedText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from HED. |
| `Sketch Detection On Image` | `Image2Scribble.inference` | `image_path` | scribble PNG | Deterministic preprocessor. |
| `Generate Image Condition On Sketch Image` | `ScribbleText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from scribble. |
| `Pose Detection On Image` | `Image2Pose.inference` | `image_path` | pose PNG | Deterministic preprocessor. |
| `Generate Image Condition On Pose Image` | `PoseText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from pose. |
| `Generate Image Condition On Segmentations` | `SegText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from segmentation maps. |
| `Beautify The Image` | `ImageText2Image.inference` | `image_path,prompt` | generated PNG | Template model that first segments, then feeds `SegText2Image`. |
| `Predict Depth On Image` | `Image2Depth.inference` | `image_path` | depth PNG | Deterministic preprocessor. |
| `Generate Image Condition On Depth` | `DepthText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from depth. |
| `Predict Normal Map On Image` | `Image2Normal.inference` | `image_path` | normal PNG | Deterministic preprocessor. |
| `Generate Image Condition On Normal Map` | `NormalText2Image.inference` | `image_path,prompt` | generated PNG | ControlNet from normal maps. |

## Checkpoint and config expectations

- `SegmentAnything` expects `model_zoo/sam_vit_h_4b8939.pth`.
- `HuskyVQA` expects a converted Husky checkpoint directory built from the LLaMA base plus delta files.
- `LDMInpainting` expects `model_zoo/ldm_inpainting_big.ckpt` and the bundled inpainting config used by the class loader.
- LaMa-style materials may refer to a separate `big-lama` model directory; do not confuse that historical inpainting asset with the controller's `LDMInpainting` checkpoint.
- `ReplaceMaskedAnything` uses the Stable Diffusion inpainting checkpoint from Hugging Face.
- The ControlNet generators use their matching Stable Diffusion v1.5 ControlNet checkpoints.
- `ImageOCRRecognition` uses EasyOCR with Chinese and English readers and may download its own reader assets on first use.

## e-mode behavior

- When `e_mode` is enabled, several model classes hold the weights on CPU until inference time, move them to the requested device for a call, and then move them back to CPU.
- This applies to the SAM, Husky, inpainting, replacement, and most Stable Diffusion / ControlNet generators.
- Do not assume a successful call leaves the model resident on GPU for the next turn.

## Grammar reminders

- Path-first tools always expect the image path before the mask path.
- Prompt-bearing tools usually join the remaining comma-separated text, but not all classes do this equally.
- If a prompt may contain commas, prefer the exact contract shown in the table and avoid inventing extra separators.
