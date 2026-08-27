# PointLLM data formats and layouts

## Objaverse point clouds

The README's released convention is a directory of NumPy files:

```text
data/
├── objaverse_data/                         # released data may be a symlink
│   ├── <object_id>_8192.npy                # shape (8192, 6)
│   └── ...
└── anno_data/
    ├── PointLLM_brief_description_660K_filtered.json
    ├── PointLLM_brief_description_660K.json
    └── PointLLM_complex_instruction_70K.json
```

The two compressed Objaverse archives are merged and extracted into a folder
named `8192_npy` in the README workflow; the runtime only requires the resolved
point-file directory. A generated skill should describe this relative layout,
not depend on any particular checkout or machine path.

Each file is a numeric array with shape `(N, 6)`, normally `(8192, 6)`:

| Slice | Meaning | Required validation |
|---|---|---|
| `[:, 0:3]` | XYZ coordinates | Numeric, finite; may be translated/scaled before loading |
| `[:, 3:6]` | RGB color | Numeric, finite, each value in `[0, 1]` |

The filename is formed as `f"{object_id}_{pointnum}.npy"`. `ObjectPointCloudDataset`
loads that exact filename from `data_path`; it does not search alternate counts.
The point-only `load_objaverse_point_cloud` helper uses the same rule and defaults
to `pointnum=8192`.

## Annotation records

The released Objaverse instruction files are JSON arrays. A usable record has
this shape (extra fields may be present):

```json
{
  "object_id": "<Objaverse_ID>",
  "conversation_type": "simple_description",
  "conversations": [
    {"from": "human", "value": "<point>\nWhat is this?"},
    {"from": "gpt", "value": "A concise object description."}
  ]
}
```

The loader uses `object_id`, `conversation_type`, and `conversations`. The
conversation type defaults to `simple_description` when absent. Supported
workflow labels documented by the source are:

- `simple_description` for the default/stage-1 style data;
- `detailed_description`, `single_round`, and `multi_round` for complex/stage-2
  filtering.

The source's GPT-4 system prompt is provenance for the `complex_instruction_70K`
shape, not a runtime dependency or a reason to call an API. It describes one
caption, three single-round Q&As, and one three-round Q&A in a JSON object, but
released training annotations are consumed by `ObjectPointCloudDataset` as
`conversations` records. Validate the released annotation file you actually
have rather than assuming generated provenance is directly loadable.

## Annotation-to-file check

For every selected annotation record, construct:

```text
<point-data-directory>/<object_id>_<pointnum>.npy
```

and require that it exists and loads as a 2-D `(N, 6)` finite array with RGB in
range. The validator reports duplicate object IDs, malformed records, missing
files, and bad references without downloading anything.

The 660K filtered brief file is the training-oriented file recommended by the
README for reproducing the paper because it excludes the reserved validation
objects. The unfiltered brief file includes those validation objects. The
complex 70K file is based on training objects. Optional PointLLM-V2 annotation
files require separately sourced Objaverse-XL point clouds and are outside this
sub-skill's no-download validation scope.

## ModelNet40 layout

```text
data/
├── modelnet_config/                         # package-bundled defaults
│   ├── ModelNet40.yaml
│   └── modelnet40_shape_names_modified.txt
└── modelnet40_data/
    ├── modelnet40_train_8192pts_fps.dat     # needed for train split
    └── modelnet40_test_8192pts_fps.dat      # README evaluation artifact
```

The default YAML values are:

```yaml
NAME: ModelNet
DATA_PATH: data/modelnet40_data
NUM_CATEGORY: 40
USE_NORMALS: FALSE
npoints: 8192
random_sampling: TRUE
use_height: FALSE
use_normals: FALSE
```

`ModelNet` loads the path from `DATA_PATH`, then opens the split-specific pickle
file and unpacks `list_of_points, list_of_labels`. The source comments describe
points as `(8192, 6)` XYZ plus normals, but the default `USE_NORMALS: FALSE`
returns only XYZ after preprocessing. With `use_color=True`, the loader appends
an all-zero array of the same shape as the current point set; this is a
compatibility placeholder, not observed ModelNet color.

`modelnet40_shape_names_modified.txt` contains exactly 40 category names in
label-index order. Notable names preserve spaces, e.g. `flower pot`, `glass box`,
`night stand`, `range hood`, and `tv stand`; do not normalize them to underscores
when presenting `label_names`.

## Evaluation reference files

The README places Objaverse ground-truth annotations and optional validation ID
lists in `data/anno_data`, including 200-object and 3000-object reference files.
They use object IDs to refer to the same point-file naming contract. This
sub-skill validates references only; result generation and external evaluation
belong to sibling routes.
