# AI core and image flow

## Purpose

Read this when you need the image pipeline from file input to saved output, including the verified class and helper signatures.

## Verified APIs

- `AI_upscale(selected_AI_model: str, selected_gpu: str, input_resize_factor: float, tiles_resolution: int)`
- `AI_upscale.AI_orchestration(image)`
- `AI_upscale.AI_upscale(image)`
- `AI_upscale.AI_upscale_with_tilling(image)`
- `prepare_output_image_filename(image_path, selected_output_path, selected_AI_model, input_resize_factor, output_resize_factor, selected_image_extension, selected_blending_factor)`
- `resize_with_output_factor(image, output_resize_factor)`
- `blend_images_and_save(target_path, starting_image, upscaled_image, starting_image_importance, file_extension='.jpg')`
- `copy_file_metadata(original_file_path, upscaled_file_path)`

## Image workflow

1. Load the image with OpenCV-based decoding.
2. Build or reuse the ONNX session for the selected model.
3. Normalize and preprocess the image into the model input shape.
4. Run inference with the selected provider.
5. Postprocess the output back into image layout.
6. Resize with the output factor.
7. Blend the original and upscaled images if requested.
8. Write the output file and copy metadata when available.

## Image-mode behavior

- RGB images follow the standard preprocess/inference/postprocess path.
- RGBA images are handled with a separate alpha pass before recombining channels.
- Grayscale images are promoted for inference and then converted back.

## Output contract

- Output filenames keep the input stem and append the model, input-resize, output-resize, and optional blending suffixes.
- The file extension comes from the selected image extension.
- The output path defaults to the input folder when the coded default output path is used.

## Notes worth remembering

- The ONNX session is created lazily.
- The source assumes the DirectML provider is available in the intended runtime.
- `copy_file_metadata` is best-effort and suppresses failures.
