# Input and Output Formats

Read this when validating image lists, dictionaries, output files, or checkpoint
paths for Tencent ML-Images inference workflows.

## Image list input

The inference scripts read a text file that contains one image path per line.
The public example uses tab-separated trailing metadata in some lines, but only
column 1 is used as the image path.

Example shape:

```text
data/im_list_for_classification.txt
```

Recommended practice:

- Use absolute or checkout-relative paths that exist on disk.
- Keep one image path per line when possible.
- Verify unreadable images before running the bundled command.

## Dictionary input

The classification workflow needs an ImageNet dictionary file. The project's
`imagenet2012_dictionary.txt` has rows such as:

```text
0\ttench\tTinca\ttinca
1\tgoldfish\tCarassius\tauratus
```

The classification code uses the first tab-separated field as the class id and
the second field as the human-readable label name.

## Classification output

The public classification example writes predictions to `label_pred.txt` by
default. Each image contributes a block of lines that looks like:

```text
+++ the predictions of <image> is:
<id> <label>: <probability>
```

The top-k count defaults to `5`.

## Feature-extraction output

The feature-extraction example writes a tab-separated file where each row stores
at least:

- image path
- optional trailing metadata copied from the input line
- floating-point feature vector values separated by spaces

Example shape:

```text
image.jpg\tlabel-metadata\t0.12 0.34 0.56 ...
```

The extracted feature vector is the `net.feat` tensor after global average
pooling. Its unsqueezed layout depends on `data_format`: explicit `NCHW` graph
smokes produce `[1, 2048, 1, 1]`, while the channels-last path produces
`[1, 1, 1, 2048]` before squeezing.

## Checkpoint path shape

The public scripts accept a checkpoint prefix or path via `--model_dir` or
`--pretrain_ckpt` depending on workflow. When validating inputs, look for the
usual TensorFlow checkpoint companions such as `.index`, `.data-*`, and
checkpoint metadata files rather than assuming a single binary file.

If the path is only a directory, make sure the directory actually contains the
TensorFlow checkpoint prefix expected by `Saver.restore`.
