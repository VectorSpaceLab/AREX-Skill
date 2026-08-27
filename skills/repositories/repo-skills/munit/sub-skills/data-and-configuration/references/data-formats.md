# Data Formats and Loader Behavior

## Folder Mode

A config with `data_root` uses folder mode. The data root must contain four domain split folders:

```text
<data_root>/
  trainA/
  trainB/
  testA/
  testB/
```

The loader recursively walks each split directory and includes files ending with these extensions: `.jpg`, `.JPG`, `.jpeg`, `.JPEG`, `.png`, `.PNG`, `.ppm`, `.PPM`, `.bmp`, `.BMP`.

Training uses `trainA` paired with `trainB` and `testA` paired with `testB`. The training loop zips the domain A and B data loaders, so the shorter domain controls epoch length. `drop_last=True` is used in the data loader.

## List Mode

A config without `data_root` uses list mode and must provide all eight keys:

```yaml
data_folder_train_a: /path/to/trainA
data_list_train_a: /path/to/list_trainA.txt
data_folder_test_a: /path/to/testA
data_list_test_a: /path/to/list_testA.txt
data_folder_train_b: /path/to/trainB
data_list_train_b: /path/to/list_trainB.txt
data_folder_test_b: /path/to/testB
data_list_test_b: /path/to/list_testB.txt
```

Each list file contains one image path per line. Although the source comment mentions Caffe-style `impath label`, the actual reader uses the whole stripped line as the relative image path and does not split labels. Therefore list entries should be plain relative paths such as:

```text
./00002.jpg
subdir/example.png
```

The loader joins each entry to its paired `data_folder_*`. A common error is using the dataset parent as `data_folder_*` while list entries are relative to `trainA` or `testA`; this produces file paths like `<dataset>/./00002.jpg` instead of `<dataset>/trainA/00002.jpg`.

## Demo Dataset Evidence

The repository includes a small `demo_edges2handbags` dataset with train/test A/B folders and list files. It is useful evidence for layout shape and tiny data-loader checks, but generated skill users should supply their own dataset paths rather than depending on that checkout.

## Transform Pipeline

Both folder and list loaders apply the same transform sequence:

1. Optional resize to `new_size`, or to `new_size_a`/`new_size_b` selected by domain.
2. Optional random crop to `crop_image_height` x `crop_image_width` when `train=True` or crop is requested.
3. Optional random horizontal flip in training mode.
4. `ToTensor()`.
5. Normalize with mean `(0.5, 0.5, 0.5)` and std `(0.5, 0.5, 0.5)`, producing roughly `[-1, 1]` tensors.

## Output Image Conventions

Training sample grids are written through helper functions that save generated A-to-B and B-to-A grids under the training output image directory. Inference output conventions are covered by `../inference-and-evaluation/`.

## Inspection Helper

Run:

```bash
python scripts/inspect_munit_dataset.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
```

It reports split counts, missing directories, missing list files, list entries that do not resolve under their paired folder, and whether `display_size` exceeds a split count.
