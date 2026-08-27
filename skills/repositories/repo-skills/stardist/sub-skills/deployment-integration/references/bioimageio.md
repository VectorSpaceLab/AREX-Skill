# Optional BioImage.IO integration

StarDist exposes `export_bioimageio` and `import_bioimageio` from
`stardist.bioimageio_utils`. This is optional: the required baseline is CPU
TensorFlow plus compiled CPU extensions. The package extra declares
`bioimageio.core>=0.5.0` and `importlib-metadata`.

## Preflight and export

Use an isolated environment and make the dependency decision explicit:

```bash
python -m pip install 'stardist[bioimageio]'
python - <<'PY'
from stardist.bioimageio_utils import _import
print(_import(error=False) is not None)
PY
```

If the probe is false, record `SKIP_OPTIONAL_BIOIMAGEIO`; do not change the CPU
environment blindly. Version compatibility among `bioimageio.core`, RDF/spec
packages, xarray, ruamel.yaml, TensorFlow, and Keras can still affect export.

Export requires a constructed `StarDist2D` or `StarDist3D` and a small,
representative floating-point test input. The test input determines declared
axes, I/O shapes, preprocessing metadata, and test arrays; it is not a
training placeholder:

```python
from pathlib import Path
import numpy as np
from stardist.models import StarDist2D
from stardist.bioimageio_utils import export_bioimageio

model = StarDist2D(None, name="2D_demo", basedir="/data/models")
export_bioimageio(
    model, Path("/data/packages/2D_demo.zip"),
    test_input=np.asarray(image, dtype=np.float32),
    test_input_axes="YX", test_input_norm_axes="YX",
    name="2D_demo", mode="tensorflow_saved_model_bundle",
    min_percentile=1.0, max_percentile=99.8,
    generate_default_deps=False,
)
```

Use `StarDist3D`, `ZYX`, and the intended spatial normalization axes for a
volume. Declare `YXC`/`ZYXC` for channel data and decide whether `C` is jointly
normalized. The helper converts axes to BioImage.IO batch/lowercase semantics,
creates `rdf.yaml`, test arrays, weights, and for 2D a DeepImageJ
postprocessing macro. The default TensorFlow SavedModel bundle is supported;
`keras_hdf5` is rejected by the source helper, and TensorFlow SavedModel export
does not support multiclass models in this baseline.

`outpath` must be a directory or a `.zip` file. The export creates temporary
SavedModel assets and weights, so reserve disk and use a stable destination.
`generate_default_deps=True` records current TensorFlow/StarDist/package
requirements in `environment.yaml`; it is provenance, not a lockfile.

## Validate and import

With the optional validator already available, validate a local archive without
fetching a remote resource:

```python
from bioimageio.core.resource_tests import test_model
result = test_model("/data/packages/2D_demo.zip")
assert not [r for r in result if r["status"] != "passed"]
```

Also check that the ZIP contains `rdf.yaml`, test arrays, weights, and (for
2D) the postprocessing macro. A validator pass checks package declarations and
test I/O, not biological usefulness or microscope calibration.

Import requires a fresh destination:

```python
from stardist.bioimageio_utils import import_bioimageio
model = import_bioimageio(
    "/data/packages/2D_demo.zip", "/data/models/imported_2D_demo"
)
```

The helper rejects an existing destination, extracts to a temporary folder,
reads `rdf.yaml`, requires a StarDist-specific `config` and `thresholds` block,
locates the declared weight attachment, writes `config.json`,
`thresholds.json`, `weights_bioimageio.h5`, and preserves package material
under `bioimageio/`. Compare the imported config, thresholds, and weights with
the source package before prediction.

A local ZIP is bounded and preferable. A URL or registry resource can make
`bioimageio.core.export_resource_package` download a complete resource and
attachments, consuming network, cache, time, and disk. Prefer a reviewed local
archive; record source/provenance and do not put credentials in commands. If a
new destination is left incomplete after failure, clean only that new path;
never merge into or overwrite an existing model directory.

## Recovery matrix

| Failure | Recovery |
|---|---|
| Optional import missing | Keep native model workflow; record optional skip. |
| Bad axes/test shape | Match rank and `YX`/`YXC` or `ZYX`/`ZYXC`; use float32 and a size satisfying model grid/halo constraints. |
| Unsupported mode/multiclass | Use the default SavedModel mode for a non-multiclass model or retain native files. |
| Existing import destination | Choose a new path; the refusal is intentional. |
| Validator/network error | Separate local schema/model failure from unavailable remote service and preserve unresolved status. |
