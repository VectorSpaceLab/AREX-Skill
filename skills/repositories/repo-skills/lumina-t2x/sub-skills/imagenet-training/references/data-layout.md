# ImageNet Data Layout

## Purpose

Read this when you need to prepare the ImageNet tree or update a benchmark launch script.

## Expected folder structure

The README examples use this shape:

```text
/path/to/imagenet/
  train/
    n01440764/
      many_images.JPEG
    n01443537/
      many_images.JPEG
  val/
    n01440764/
      ILSVRC2012_val_00000293.JPEG
    n01443537/
      ILSVRC2012_val_00000236.JPEG
```

## Path editing

The benchmark shell scripts define a `train_data_root` variable.
Replace the placeholder value with the local ImageNet train folder before launching.

## Validation intent

The bundled checker should confirm:

- `train/` exists and contains class subdirectories.
- `val/` exists and contains class subdirectories.
- The root path is a directory, not a file.
- The path chosen in the shell script matches the actual dataset root.
