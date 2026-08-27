# Python inference API reference

The implementation lives in `deepdanbooru.data` and
`deepdanbooru.commands.evaluate`. The signatures below are the live signatures
for DeepDanbooru 1.0.0 at source commit
`7971936c0d050c6475b01e0eb97710a66c61b43e`.

## Image loading and preprocessing

```python
load_image_for_evaluate(
    input_, width: int, height: int, normalize: bool = True
) -> Any
```

- `input_` is either a filesystem path accepted by TensorFlow or a
  `six.BytesIO` object containing image bytes.
- `width` and `height` are target model dimensions, not a request to crop the
  image. The result is an HWC array of shape `(height, width, 3)`.
- With the default `normalize=True`, pixel values are divided by `255.0` after
  resizing and edge padding. Pass `normalize=False` only when a caller
  deliberately needs the unnormalized preprocessing result.
- The implementation reads PNG first, falls back to TensorFlow-IO WebP
  decoding, resizes with aspect ratio preserved, then calls
  `deepdanbooru.image.transform_and_pad_image`.

The inference functions do not validate that `width` and `height` are positive,
that the result has three channels, or that the tag count agrees with the model.
Perform those checks before a large run.

## One-image inference

```python
evaluate_image(
    image_input: Union[str, six.BytesIO],
    model: Any,
    tags: List[str],
    threshold: float,
) -> Iterable[Tuple[str, float]]
```

The function obtains dimensions from the model itself:

```python
width = model.input_shape[2]
height = model.input_shape[1]
```

It loads and normalizes the image, reshapes the HWC array to a batch of one,
then executes `model.predict(image)[0]`. It yields `(tag, score)` pairs for
each tag whose score is **greater than or equal to** `threshold`, preserving the
order of `tags`. Scores are not sorted. The model output is expected to be a
one-dimensional vector for the batch item.

The source builds a dictionary by enumerating `tags` and the prediction vector.
A tag list longer than the model output can raise an index error; a tag list
shorter than the output silently leaves some output units unnamed. There is no
explicit dimensionality or duplicate-tag validation. Treat exact dimensional
alignment as a precondition.

Minimal direct use:

```python
from deepdanbooru.commands.evaluate import evaluate_image

model = ...  # already loaded Keras model
with open("image.png", "rb") as stream:
    import io
    image_input = io.BytesIO(stream.read())

for tag, score in evaluate_image(image_input, model, tags, threshold=0.5):
    print(tag, score)
```

A normal `io.BytesIO` is compatible with the `six.BytesIO` check in the
supported environment. Do not pass a directory to `evaluate_image`.

## Multi-path CLI implementation function

```python
evaluate(
    target_paths,
    project_path,
    model_path,
    tags_path,
    threshold,
    allow_gpu,
    compile_model,
    allow_folder,
    save_txt,
    folder_filters,
    verbose,
)
```

The function first applies the CPU safeguard when `allow_gpu` is false. It
requires at least one of `project_path` and `model_path`, and separately at
least one of `project_path` and `tags_path`. Consequently:

- project only: load the model and tags from the project;
- project plus direct model: direct model wins, project tags are used unless
  overridden;
- project plus direct tags: project model is used, direct tags win;
- direct model plus direct tags: fully explicit mode;
- direct model without tags, or direct tags without model, and no project: an
  exception is raised before inference.

When `allow_folder` is true, each target that is not a regular file is expanded
recursively with `deepdanbooru.io.get_image_file_paths_recursive`. The filter
string is split literally on commas and each pattern is passed to
`pathlib.Path.rglob`; spaces are not stripped. The final list is passed through
`deepdanbooru.extra.natural_sorted`, so names such as `image2.png` sort before
`image10.png` when their paths otherwise compare alike.

The direct model is loaded with `tf.keras.models.load_model(model_path,
compile=compile_model)`. A project model is loaded with
`deepdanbooru.project.load_model_from_project(project_path,
compile_model=compile_model)`. Tags are loaded from the explicit file when
provided, otherwise from `PROJECT/tags.txt`.

## Project inference function

```python
evaluate_project(project_path, target_path, threshold)
```

This function requires `target_path` to exist. A regular file is evaluated as
one image. A directory is searched recursively using these exact patterns:

```text
*.[Pp][Nn][Gg]
*.[Jj][Pp][Gg]
*.[Jj][Pp][Ee][Gg]
*.[Gg][Ii][Ff]
```

The project loader is intended to read `project.json`, load `tags.txt`, and look
for `model-{project_context["model"]}.keras`, falling back to `.h5`. In the
exact 1.0.0 source revision, however, native `load_project()` calls
`dd.data.load_tags_from_project`, while that helper is exported under
`dd.project` and is not present on `dd.data`. Therefore unmodified native
`evaluate_project()` raises `AttributeError` before loading the model. Use the
CLI `evaluate` function with `project_path` and `allow_folder=True` for a
supported project-backed folder run; it loads tags through the available API.
The bundled smoke helper covers that fallback, not an unverified native run.
Preserve the source commit/version when comparing a corrected package because
this API contract is tied to the 1.0.0 provenance snapshot.

If a corrected package or separately reviewed native compatibility fix is used,
this route uses `project_context["image_width"]` and
`project_context["image_height"]` for preprocessing rather than reading
dimensions from `model.input_shape`. Keep those project values synchronized
with the saved model and record the package/source provenance.

Unlike `evaluate`, native `evaluate_project` has no `allow-gpu`, compile,
folder-filter, verbose, or save-sidecar parameter. It prints selected tags and
never writes `.txt` files.
