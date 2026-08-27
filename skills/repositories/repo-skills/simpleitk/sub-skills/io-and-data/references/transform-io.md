# Transform IO

SimpleITK transform IO uses procedural functions for ordinary transform files:

```python
import SimpleITK as sitk

transform = sitk.Euler2DTransform()
transform.SetTranslation((2.0, 3.0))

sitk.WriteTransform(transform, "euler2d.tfm")
read_back = sitk.ReadTransform("euler2d.tfm")
assert isinstance(read_back, sitk.Euler2DTransform)
```

Use `sitk.WriteTransform(transform, filename)` to serialize a transform and `sitk.ReadTransform(filename)` to load it. Python `ReadTransform` returns a downcasted transform type when possible in modern SimpleITK builds, so an `Euler2DTransform` can usually be checked directly with `isinstance`.

## Common Format Choices

- Use `.tfm` or `.txt` for small rigid, affine, and simple smoke-test transforms where a human-readable file is useful.
- Use `.hdf` or `.mat` for larger transforms, composite transforms, or displacement-heavy workflows when the build supports the format.
- Use `.xfm` when a MINC transform workflow expects it and the local build supports MINC transform IO.
- If `ReadTransform` or `WriteTransform` reports an unsupported suffix, retry with a simpler known format such as `.tfm` for small transforms or `.hdf` for large/composite transforms.

Supported transform IO backends vary by build and can include text, HDF5, Matlab, and MINC transform IO.

## Validation Checklist

After reading a transform back:

- Compare `GetName()` or `isinstance(read_back, ExpectedTransformClass)` when the class is known.
- Compare `GetDimension()` for 2D versus 3D transforms.
- Compare `GetParameters()` and `GetFixedParameters()` for deterministic transform classes.
- Apply both transforms to one or two known points when semantic equivalence matters.
- Keep registration-specific interpretation, optimizer outputs, transform composition, and resampling effects in `../registration-transforms/SKILL.md`.

```python
point = (4.0, 5.0)
assert tuple(read_back.TransformPoint(point)) == tuple(transform.TransformPoint(point))
```

## Displacement-Field Caveats

Displacement field transforms can be large. Writing them as text can create very large files and slow IO. Prefer binary transform formats such as `.hdf` or `.mat` when serializing a `DisplacementFieldTransform`.

Another safe pattern is to save the displacement field image itself with a vector-capable image format such as `.nrrd`, `.nhdr`, `.mha`, `.mhd`, `.nii`, or `.nii.gz`, then reconstruct the transform in code that understands spacing, origin, direction, vector component order, and physical-coordinate semantics.

## Optional Wrapper Caveat

`ElastixImageFilter` and `TransformixImageFilter` are optional wrappers that may be present in the SimpleITK source tree but absent from installed wheels. Do not use elastix/transformix APIs as prerequisites for transform IO smoke tests or general transform file guidance.

## Evidence

Distilled from SimpleITK IO documentation, transform read/write examples, and Python transform IO tests. The bundled examples here use generated transforms only.
