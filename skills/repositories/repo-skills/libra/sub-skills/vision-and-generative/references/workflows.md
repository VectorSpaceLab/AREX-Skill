# Vision and generative workflows

## 1. Inspect layout before training

Run the safe helper before calling `convolutional_query`:

```bash
python skills/disco/libra/sub-skills/vision-and-generative/scripts/inspect_image_dataset.py --data-path path/to/images
```

For CSV-based image datasets:

```bash
python skills/disco/libra/sub-skills/vision-and-generative/scripts/inspect_image_dataset.py --data-path path/to/images --csv labels.csv
```

## 2. CNN image classification

### Setwise layout
Use when the data already has train/test splits:

```text
images/
  training_set/class_a/*.png
  training_set/class_b/*.png
  testing_set/class_a/*.png
  testing_set/class_b/*.png
```

```python
c = client("images")
c.convolutional_query("predict class", read_mode="setwise", epochs=1)
```

### Classwise layout
Use when a single root contains one subdirectory per class:

```text
images/
  class_a/*.png
  class_b/*.png
```

```python
c = client("images")
c.convolutional_query("predict class", read_mode="classwise", test_size=0.2, epochs=1)
```

### CSV-wise layout
Use when a CSV maps images to labels:

```python
c = client("images")
c.convolutional_query("predict label", read_mode="csvwise", image_column="filename", epochs=1)
```

## 3. Pretrained and custom architectures

Pretrained ImageNet weights require 224x224 input size:

```python
c.convolutional_query(
    "predict class",
    read_mode="setwise",
    pretrained={"arch": "vggnet19", "weights": "imagenet"},
    height=224,
    width=224,
    epochs=1,
)
```

Custom architecture JSON files require already-processed train/test folders and `preprocess=False`:

```python
c.convolutional_query(
    "predict class",
    preprocess=False,
    custom_arch="model_config.json",
    epochs=1,
)
```

## 4. Export and feature maps

Use export flags deliberately because outputs are written in the current working directory:

```python
c.convolutional_query("predict class", save_as_tfjs=True, save_as_tflite=True)
```

Use `show_feature_map=True` only after a CNN can produce at least one test batch.

## 5. GAN generation

Use a single folder containing images of one class:

```python
c = client("single_class_images")
c.gan_query("generate images", type="dcgan", num_images=3, epochs=1, height=64, width=64)
```

Expect `generated_images/` to appear relative to the data path. Use a temporary copy for experiments.
