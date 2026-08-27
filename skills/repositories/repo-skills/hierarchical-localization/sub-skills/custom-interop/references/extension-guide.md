# Custom HLoc extension guide

This guide covers two supported interoperability paths:

1. **Export artifacts**: create HDF5 feature, global descriptor, or match files from any framework and feed those files to HLoc workflows.
2. **Add Python modules/configs**: implement a PyTorch extractor or matcher under the `hloc.extractors` or `hloc.matchers` Python namespace so HLoc can load it through a config.

Use artifact export for TensorFlow/JAX/C++/MATLAB pipelines, remote feature services, or one-off experiments. Use a Python module when the extractor or matcher should be selected by HLoc config name and run inside `hloc.extract_features.main`, `hloc.match_features.main`, or their CLIs.

## BaseModel contract

HLoc custom extractors and matchers inherit from `hloc.utils.base_model.BaseModel`. The verified public signature is:

```python
BaseModel(conf)
```

The base class behavior is part of the extension contract:

- Class attributes:
  - `default_conf = {}`: default options merged with the user-provided `conf`.
  - `required_inputs = []`: input keys that must be present in the runtime data dictionary.
- `__init__(conf)` merges `{**default_conf, **conf}`, copies `required_inputs`, calls child `_init(conf)`, and flushes stdout.
- `forward(data)` asserts that every key in `required_inputs` is present, then calls child `_forward(data)`.
- Child classes must implement `_init(self, conf)` and `_forward(self, data)`.

Minimal extractor shape:

```python
from hloc.utils.base_model import BaseModel

class MyExtractor(BaseModel):
    default_conf = {"descriptor_dim": 128}
    required_inputs = ["image"]

    def _init(self, conf):
        # initialize torch modules, load weights, or set constants
        ...

    def _forward(self, data):
        image = data["image"]  # tensor shaped like BxCxHxW, float in [0, 1]
        # Return tensors with a batch dimension. HLoc removes batch index 0
        # before writing the HDF5 datasets.
        return {
            "keypoints": keypoints,      # BxNx2, x/y image coordinates
            "descriptors": descriptors,  # BxDxN for sparse descriptors
            "scores": scores,            # BxN, recommended for matchers
        }
```

Minimal sparse matcher shape:

```python
from hloc.utils.base_model import BaseModel

class MyMatcher(BaseModel):
    default_conf = {"threshold": 0.2}
    required_inputs = ["keypoints0", "descriptors0", "keypoints1", "descriptors1"]

    def _init(self, conf):
        ...

    def _forward(self, data):
        # Return one match index per keypoint in image0.
        return {
            "matches0": matches0,                  # BxN0, -1 or index in image1
            "matching_scores0": matching_scores0,  # BxN0, float confidence
        }
```

`matching_scores0` is strongly recommended even if all scores are constant: downstream HLoc readers expect it when converting sparse match files into `(idx0, idx1)` arrays.

## Dynamic loading and module naming

HLoc resolves a model from a config by calling the verified signature:

```python
dynamic_load(root, model)
```

The loader imports the module path:

```text
{root.__name__}.{model}
```

Then it finds classes defined in that module, filters them to subclasses of `BaseModel`, and asserts that exactly one such class exists. Practical consequences:

- Extractor config `model.name: "my_extractor"` imports `hloc.extractors.my_extractor`.
- Matcher config `model.name: "my_matcher"` imports `hloc.matchers.my_matcher`.
- The module file basename must match `model.name`.
- Each module should define exactly one concrete `BaseModel` subclass. Helper classes should not inherit `BaseModel` in the same module.
- The subclass name can be descriptive; the loader does not require a class named `Model`.
- Import-time dependency errors surface as dynamic-load failures. Keep optional heavy dependencies inside `_init` if possible so simple config inspection remains usable.

## Config dictionaries

HLoc's built-in config dictionaries have this shape:

Extractor config:

```python
{
    "output": "feats-my-extractor",      # basename for <output>.h5
    "model": {"name": "my_extractor", "option": "value"},
    "preprocessing": {
        "grayscale": False,
        "resize_max": 1024,
        "resize_force": False,
        "interpolation": "cv2_area",
    },
}
```

Matcher config:

```python
{
    "output": "matches-my-matcher",      # used in match-file names
    "model": {"name": "my_matcher", "threshold": 0.2},
}
```

You can either add a named config to the relevant HLoc module in a project fork/wrapper package, or bypass named configs and call the Python API with an explicit dictionary:

```python
from pathlib import Path
from hloc import extract_features, match_features

feature_conf = {
    "output": "feats-my-extractor",
    "model": {"name": "my_extractor"},
    "preprocessing": {"grayscale": False, "resize_max": 1024},
}
features = extract_features.main(
    feature_conf,
    image_dir=Path("images"),
    export_dir=Path("outputs"),
    as_half=True,
)

matcher_conf = {
    "output": "matches-my-matcher",
    "model": {"name": "my_matcher"},
}
matches = match_features.main(
    matcher_conf,
    pairs=Path("pairs-query-db.txt"),
    features=features,
    matches=Path("outputs/matches-my-matcher.h5"),
)
```

Prefer a fork, editable package, or wrapper package on `PYTHONPATH` for reusable modules. Avoid modifying a long-lived environment's installed package in place unless it is a disposable experiment environment.

## Input and output keys by component type

### Extractors

Common extractor `required_inputs` is:

```python
required_inputs = ["image"]
```

The input image tensor comes from HLoc's image dataset after preprocessing:

- Shape is batched `B x C x H x W`.
- Values are float in `[0, 1]`.
- `C` is `1` for grayscale preprocessing and `3` for RGB preprocessing.

Local-feature extractor outputs should include:

| Key | Shape | Meaning |
| --- | --- | --- |
| `keypoints` | `B x N x 2` | x/y keypoint coordinates before HLoc writes them in original image coordinates. |
| `descriptors` | `B x D x N` | descriptor matrix matching HLoc sparse matcher convention. |
| `scores` | `B x N` | keypoint confidence; required by SuperGlue-style matchers, recommended otherwise. |
| `scales` | `B x N` | scale; needed by AdaLAM-style matching. |
| `oris` | `B x N` | orientation in degrees; needed by AdaLAM-style matching. |

Global-retrieval extractors should write:

| Key | Shape | Meaning |
| --- | --- | --- |
| `global_descriptor` | `B x D` or `D` after batch removal | one descriptor vector per image. |

HLoc's extraction writer also adds `image_size` as `[width, height]` for each image and stores keypoint uncertainty as a `keypoints` dataset attribute when the model exposes `detection_noise`.

### Matchers

Sparse matcher data is assembled by reading every dataset in each feature group and adding suffixes `0` and `1` for the first and second image. For example, feature datasets `keypoints`, `descriptors`, `scores`, and `image_size` become `keypoints0`, `descriptors0`, `scores0`, `image0`, and the corresponding `1` keys.

Verified built-in matcher input patterns:

| Matcher family | Required inputs |
| --- | --- |
| nearest-neighbor | `descriptors0`, `descriptors1` |
| LightGlue | `image0`, `keypoints0`, `descriptors0`, `image1`, `keypoints1`, `descriptors1` |
| SuperGlue | `image0`, `keypoints0`, `scores0`, `descriptors0`, `image1`, `keypoints1`, `scores1`, `descriptors1` |
| AdaLAM | `image0`, `image1`, `descriptors0`, `descriptors1`, `keypoints0`, `keypoints1`, `scales0`, `scales1`, `oris0`, `oris1` |
| LoFTR dense matcher | `image0`, `image1`; its semi-dense path is owned by HLoc dense matching rather than sparse match HDF5 input. |

Sparse matcher outputs should include:

| Key | Shape | Meaning |
| --- | --- | --- |
| `matches0` | `B x N0` | for each keypoint in image0, the matched keypoint index in image1, or `-1`. |
| `matching_scores0` | `B x N0` | score per keypoint in image0; use zeros or ones if no confidence exists. |

## Export external artifacts instead of modules

When the feature/matcher is not a PyTorch `BaseModel`, export HDF5 artifacts matching [data-formats.md](data-formats.md). Recommended sequence:

1. Use the same image names that downstream HLoc will use: relative paths from the image root, such as `db/1.jpg` or `query/night/0001.jpg`.
2. Write local features with `keypoints`, `descriptors`, `scores` when available, and `image_size`.
3. Write global descriptors with `global_descriptor` if retrieval pairs should be generated by HLoc.
4. Write match files with current HLoc pair names and both `matches0` and `matching_scores0`.
5. Validate before routing downstream:

   ```bash
   python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
     --features outputs/features.h5 \
     --matches outputs/matches.h5 \
     --retrieval pairs-query-db.txt \
     --strict
   ```

6. Route valid artifacts to [feature-retrieval](../../feature-retrieval/SKILL.md) for retrieval-pair generation or to [mapping-localization](../../mapping-localization/SKILL.md) for SfM/localization.

## Minimal HDF5 export snippets

Local feature export:

```python
import h5py
import numpy as np

features = {
    "db/1.jpg": {
        "keypoints": np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32),
        "descriptors": np.random.rand(128, 2).astype(np.float32),
        "scores": np.array([0.9, 0.7], dtype=np.float32),
        "image_size": np.array([640, 480], dtype=np.int32),  # width, height
    },
}

with h5py.File("features.h5", "w") as fd:
    for name, values in features.items():
        grp = fd.create_group(name)
        for key, value in values.items():
            grp.create_dataset(key, data=value)
```

Match export using HLoc's current pair naming:

```python
import h5py
import numpy as np

def hloc_pair_name(name0, name1, separator="/"):
    return separator.join((name0.replace("/", "-"), name1.replace("/", "-")))

name0 = "query/1.jpg"
name1 = "db/1.jpg"
pair = hloc_pair_name(name0, name1)
matches0 = np.array([0, -1, 2], dtype=np.int32)
scores0 = np.array([0.95, 0.0, 0.80], dtype=np.float32)

with h5py.File("matches.h5", "w") as fd:
    grp = fd.create_group(pair)
    grp.create_dataset("matches0", data=matches0)
    grp.create_dataset("matching_scores0", data=scores0)
```

Global descriptor export:

```python
import h5py
import numpy as np

with h5py.File("global-descriptors.h5", "w") as fd:
    for name in ["query/1.jpg", "db/1.jpg"]:
        grp = fd.create_group(name)
        desc = np.random.rand(4096).astype(np.float32)
        desc /= max(np.linalg.norm(desc), 1e-12)
        grp.create_dataset("global_descriptor", data=desc)
```
