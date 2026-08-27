# CLI Reference

## When to read

Read this when translating a user request into `python neural_style.py ...` flags or checking whether README claims match the inspected source. Defaults below are source-verified from `parse_args()` and CLI help for the inspected commit.

## Single-image and shared flags

| Flag | Default | Choices / type | Notes |
| --- | --- | --- | --- |
| `--style_imgs` | required | one or more strings | Style image filenames, resolved under `--style_imgs_dir`. |
| `--content_img` | `None` | string | Content image filename, resolved under `--content_img_dir`; practically required for image runs. |
| `--style_imgs_dir` | `./styles` | path string | One directory for all style filenames. |
| `--content_img_dir` | `./image_input` | path string | Content image directory; style masks are also read here. |
| `--img_output_dir` | `./image_output` | path string | Output root for still images. |
| `--img_name` | `result` | string | Output subdirectory and image stem. |
| `--model_weights` | `imagenet-vgg-verydeep-19.mat` | path string | MatConvNet VGG-19 `.mat` weights. |
| `--device` | `/gpu:0` | `/gpu:0`, `/cpu:0` | GPU default follows repo recommendation; pass `/cpu:0` explicitly for CPU. |
| `--verbose` | false | flag | Prints graph/loss progress messages. |

## Image size, initialization, and optimizer

| Flag | Default | Choices / type | Notes |
| --- | --- | --- | --- |
| `--max_size` | `512` | integer | Longest side cap for input images. Lower first for memory issues. |
| `--init_img_type` | `content` | `random`, `content`, `style` | Still-image initialization. |
| `--noise_ratio` | `1.0` | float | Noise/content blend when random initialization is used. |
| `--seed` | `0` | integer | NumPy random seed for noise image. |
| `--optimizer` | `lbfgs` | `lbfgs`, `adam` | L-BFGS needs TensorFlow contrib; Adam is lower memory. |
| `--learning_rate` | `1.0` | float | Used by Adam. |
| `--max_iterations` | `1000` | integer | Main optimizer iteration cap for image runs. |
| `--print_iterations` | `50` | integer | Only visible with `--verbose`. |

## Style/content/loss controls

| Flag | Default | Choices / type | Notes |
| --- | --- | --- | --- |
| `--style_imgs_weights` | `1.0` | one or more floats | Normalized after parsing; count should match style images. |
| `--content_weight` | `5.0` | float | Multiplies content loss. |
| `--style_weight` | `10000.0` | float | Multiplies style loss. |
| `--tv_weight` | `0.001` | float | Total variation/denoising weight. |
| `--temporal_weight` | `200.0` | float | Used in video temporal loss after first frame. |
| `--content_loss_function` | `1` | `1`, `2`, `3` | Selects one of three constants in content loss. |
| `--content_layers` | `conv4_2` | one or more strings | Content feature layers. |
| `--style_layers` | `relu1_1 relu2_1 relu3_1 relu4_1 relu5_1` | one or more strings | Style Gram-matrix layers. |
| `--content_layer_weights` | `1.0` | one or more floats | Normalized after parsing; count should match content layers. |
| `--style_layer_weights` | five `0.2` values | one or more floats | Normalized after parsing; count should match style layers. |
| `--pooling_type` | `avg` | `avg`, `max` | VGG pooling mode in source graph construction. |

## Color and mask controls

| Flag | Default | Choices / type | Notes |
| --- | --- | --- | --- |
| `--original_colors` | false | flag | Convert stylized output to preserve content chroma. |
| `--color_convert_type` | `yuv` | `yuv`, `ycrcb`, `luv`, `lab` | Color space for original-color conversion. |
| `--color_convert_time` | `after` | `after`, `before` | Parsed but inspected source always applies conversion after stylization. |
| `--style_mask` | false | flag | Enables masked style losses. |
| `--style_mask_imgs` | `None` | one or more strings | Mask filenames read from `--content_img_dir`; count should match style images. |

## Video flags

| Flag | Default | Choices / type | Notes |
| --- | --- | --- | --- |
| `--video` | false | flag | Enables frame loop. |
| `--start_frame` | `1` | integer | First frame number. |
| `--end_frame` | `1` | integer | Last frame number. |
| `--first_frame_type` | `content` | `random`, `content`, `style` | Source default for first video frame. |
| `--init_frame_type` | `prev_warped` | `prev_warped`, `prev`, `random`, `content`, `style` | Later frame initialization; `prev_warped` requires flow files. |
| `--video_input_dir` | `./video_input` | path string | Input frames and flow/reliability files. |
| `--video_output_dir` | `./video_output` | path string | Stylized output frames. |
| `--content_frame_frmt` | `frame_{}.ppm` | Python format string | Source zero-pads frame number before formatting. |
| `--backward_optical_flow_frmt` | `backward_{}_{}.flo` | Python format string | Current-to-previous flow. |
| `--forward_optical_flow_frmt` | `forward_{}_{}.flo` | Python format string | Previous-to-current flow. |
| `--content_weights_frmt` | `reliable_{}_{}.txt` | Python format string | Reliability/consistency masks. |
| `--prev_frame_indices` | `1` | one or more integers | Parsed as list; long-term helpers exist but inspected stylize path uses short-term temporal loss. |
| `--first_frame_iterations` | `2000` | integer | Iterations for first video frame. |
| `--frame_iterations` | `800` | integer | Iterations for later frames. |

## Source quirks to remember

- The parser normalizes style-image, content-layer, and style-layer weights; it does not validate that list lengths match their targets.
- `--content_img` is not marked `required=True`, but image mode will fail when it tries to load a missing content filename.
- README video default text may differ from the inspected parser; prefer source defaults in this reference.
- `--color_convert_time before` is not implemented in the inspected conversion path.
- Video full execution requires files beyond the parser: VGG weights, input frames, previous output frames, `.flo` files, and reliability text files for the default `prev_warped` path.
