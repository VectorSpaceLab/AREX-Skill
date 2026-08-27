# Vision and generative API reference

## Client methods

| Method | Use it when | Important inputs | Stored key / result |
|---|---|---|---|
| `convolutional_query(instruction=None, read_mode=None, preprocess=True, data_path=None, new_folders=True, image_column=None, test_size=0.2, fine_tune=None, augmentation=True, custom_arch=None, pretrained=None, epochs=10, height=None, width=None, show_feature_map=False, save_as_tfjs=None, save_as_tflite=None, generate_plots=None)` | Train an image classifier from folders or CSV image paths. | `read_mode`, `preprocess`, `image_column`, `custom_arch`, `pretrained`, `height`, `width`, export flags | `convolutional_NN` with `model`, `data_type`, `shape`, `data_sizes`, `losses`, `accuracy`, `plots`, `res`, `num_classes`. |
| `gan_query(instruction=None, type='dcgan', num_images=3, preprocess=True, data_path=None, verbose=0, epochs=10, height=None, width=None, output_path=None)` | Train a DCGAN over one image class folder and write generated images. | `num_images`, `preprocess`, `epochs`, `height`, `width` | `DCGAN` with `model`, `shape`, `data`, `losses`, and discriminator accuracy. |
| `tune(model_to_tune='convolutional_NN', ...)` | Tune an existing CNN model. | Keras Tuner arguments and `directory` | Replaces the stored CNN dict with tuned model data. |
| `plots(model='convolutional_NN', ...)` / `analyze(model='convolutional_NN', ...)` | Inspect plots and metrics after training. | existing model key | Reads or updates stored model dictionaries. |

## Pretrained architecture names
Supported `pretrained['arch']` values in the inspected source:
- `vggnet16`
- `vggnet19`
- `resnet50`
- `resnet101`
- `resnet152`
- `mobilenet`
- `mobilenetv2`
- `densenet121`
- `densenet169`
- `densenet201`

Set `pretrained={'arch': 'vggnet19', 'weights': 'imagenet'}` for ImageNet weights. If `weights` is absent or not `imagenet`, the architecture is randomly initialized.

## Related but owned by NLP
`image_caption_query(...)` and `generate_caption(...)` are documented in `sub-skills/nlp-and-generation` because their public methods are part of the NLP query module. Use this vision sub-skill to validate image paths and layout before captioning.
