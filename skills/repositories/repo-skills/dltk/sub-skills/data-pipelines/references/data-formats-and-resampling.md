# Data formats, modality layouts, and resampling

## Common array contract

The DLTK tutorials and application readers use SimpleITK for NIfTI I/O:

```text
sitk_image = sitk.ReadImage(str(path))
array = sitk.GetArrayFromImage(sitk_image)
```

For one 3-D modality, add a final singleton channel dimension. For multiple
aligned modalities, normalize each volume and stack with `np.stack(...,
axis=-1)`. The resulting feature convention used by the examples is
`[z, y, x, channels]` (the source comments sometimes call spatial dimensions
`x, y, z`; trust the actual `GetArrayFromImage` array and verify orientation
against metadata). Segmentation labels remain `[z, y, x]`, with no channel
axis, so the class-balanced helper can check `image.shape[:-1] == label.shape`.

SimpleITK retains spacing, origin, direction, and pixel type in its `Image`
object. If a later deployment step writes a prediction back to NIfTI, preserve
that object in a side channel rather than yielding it through the TensorFlow
`dtypes` tree. The DLTK `Reader` only passes values described by TensorFlow
DTypes into `Dataset.from_generator`.

## CSV-driven IXI layouts

The DLTK IXI application recipe uses a demographic CSV with this
header:

```text
IXI_ID,"SEX_ID (1=m, 2=f)",HEIGHT,WEIGHT,ETHNIC_ID,MARITAL_ID,\
OCCUPATION_ID,QUALIFICATION_ID,DOB,DATE_AVAILABLE,STUDY_DATE,AGE
```

Rows contain IDs such as `IXI012`, sex values `1`/`2`, and age at column index
11. The readers use the ID to construct paths rather than storing every image
path in the row. The download/preparation scripts write separate CSVs for the
Hammersmith and Guy's subsets:

- `demographic_HH.csv` for the IXI Hammersmith Hospital subset;
- `demographic_Guys.csv` for the IXI Guy's Hospital subset.

The source scripts organize image files under a subject directory with names
such as `T1_1mm.nii.gz`, `T2_1mm.nii.gz`, `PD_1mm.nii.gz`, and `MRA_1mm.nii.gz`,
or the corresponding `2mm` names. Application readers use:

- IXI age/sex/super-resolution readers: one T1 volume, channel-last
  `[z, y, x, 1]`;
- IXI representation-learning reader: T1, T2, and PD stacked as channels
  `[z, y, x, 3]`;
- the DCGAN reader: center slices and a noise feature, with labels holding the
  image target as required by that model's unusual input contract.

When parsing a CSV for an object-preserving legacy workflow, the examples use
`dtype=object`, `keep_default_na=False`, and `na_values=[]`. Modern pandas may
not provide the old `.as_matrix()` method; replace that conversion only after
checking the resulting row values and ordering.

## MRBrainS13 layout

The MRBrainS application recipe uses a manifest with this shape. The folder
values are caller-owned placeholders and must be replaced with paths under the
chosen dataset root:

```text
id,subj_folder
1,/datasets/MRBrainS13/TrainingData/1/
...
5,/datasets/MRBrainS13/TrainingData/5/
```

Each subject folder is expected to contain:

```text
T1.nii
T1_IR.nii
T2_FLAIR.nii
LabelsForTraining.nii
```

The application stacks T1, T1 inversion recovery, and T2 FLAIR into
`[z, y, x, 3]`, whitens each modality, and casts the label to `int32`. It uses
`classes=9` for class-balanced patches. That is a label convention from the
example, not a guarantee for another MRBrainS release; inspect the label
values and task definition before selecting class count.

MRBrainS data requires an external download and registration. A manifest may contain placeholder paths rather than data. IXI archives and
demographic files are also external inputs. A reader skill must report these prerequisites rather
than downloading them implicitly or claiming that a synthetic smoke test proves
dataset availability.

## Resampling intent

Both IXI preparation scripts provide the same source-observed intent:

1. Use the T2 image as the reference modality.
2. Resample T2 to isotropic spacing `(1.0, 1.0, 1.0)` or
   `[2.0, 2.0, 2.0]` with a computed output size based on original size and
   spacing.
3. Reslice T1, PD, and MRA to the reference image's size/spacing, direction,
   and origin.
4. Use B-spline interpolation for intensity images and nearest-neighbor for
   labels (`is_label=True`).
5. Write modality files into a new `1mm/<subject>` or `2mm/<subject>` layout.

The source helper signatures are `resample_image(itk_image,
 out_spacing=(1.0, 1.0, 1.0), is_label=False)` in the Hammersmith script and
`resample_image(itk_image, out_spacing=[1.0, 1.0, 1.0], is_label=False)` in the
Guy's script; both also define `reslice_image(itk_image, itk_ref,
is_label=False)`. The scripts set output spacing, size, direction, origin,
identity transform, and a default pixel value. Verify physical alignment after
any adaptation; array shape equality alone is insufficient.

Resampling rules are semantic: never use B-spline or linear interpolation for
categorical labels, and do not independently resample modalities when their
shared voxel grid is required. For a safe new preparation job, write to a new
explicit output directory, record input/output spacing and metadata, and make
overwrite behavior explicit. Do not copy the source scripts' network download,
tar extraction, broad cleanup, `os.system('rm -rf orig')`, or automatic deletion
of archives into a bundled helper.

## Safe boundary

This subtree contains no downloader and no credential handling. Before using a
real dataset, obtain permission, verify a manifest and checksums where
available, check that all required modalities/labels exist, and use a bounded
fixture. Network access, registration credentials, archive extraction, storage
budget, and licensing are prerequisites owned by the caller/environment—not by
`read_fn` or a smoke script.
