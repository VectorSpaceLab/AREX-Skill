# Vision data formats

## Image extensions
The image preprocessing code searches for common image extensions such as `.jpg`, `.jpeg`, `.png`, and `.gif`.

## Setwise classification layout

```text
data_root/
  training_set/
    class_a/image1.png
    class_b/image2.png
  testing_set/
    class_a/image3.png
    class_b/image4.png
```

Requirements:
- both `training_set` and `testing_set` must exist
- both sets must contain the same number of class folders
- each class folder needs at least one image

## Classwise classification layout

```text
data_root/
  class_a/*.png
  class_b/*.png
```

Requirements:
- at least two class folders
- each class must contain enough images for the requested train/test split
- preprocessing creates `proc_training_set` and `proc_testing_set`

## CSV-wise classification layout

```text
data_root/
  labels.csv
  images/*.png
```

The CSV needs:
- an image column containing existing image paths, filenames, or names resolvable inside child directories
- a label column selected by the instruction
- at least two classes
- at least two images per class

Pass `image_column` when automatic path-column detection could choose the wrong column.

## Already processed layout
Use `preprocess=False` only when the root already has `training_set` and `testing_set` folders compatible with Keras `flow_from_directory`.

## GAN layout
`gan_query` uses a single class folder of images. It preprocesses into `proc_training_set` and writes generated outputs under `generated_images` relative to the data path.

## Captioning note
Captioning uses image paths plus text captions and is documented in `sub-skills/nlp-and-generation/references/data-formats.md`.
