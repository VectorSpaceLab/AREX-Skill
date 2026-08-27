# Optional Elastix and Transformix Wrappers

## Availability Guard

- `ElastixImageFilter` and `TransformixImageFilter` are optional SimpleITK wrappers. Source files exist in this checkout, but the inspected wheel did not expose these Python classes.
- Always guard wrapper use before constructing filters:

```python
if not hasattr(sitk, "ElastixImageFilter"):
    raise RuntimeError("This SimpleITK build does not include ElastixImageFilter; use ImageRegistrationMethod or install/build a wrapper-enabled SimpleITK.")
if not hasattr(sitk, "TransformixImageFilter"):
    raise RuntimeError("This SimpleITK build does not include TransformixImageFilter; transformix operations are unavailable in this install.")
```

- Route build-option questions, source compilation, wrapper enabling, and packaging diagnostics to [../../builds-and-wrapping/SKILL.md](../../builds-and-wrapping/SKILL.md).
- Do not present elastix/transformix as guaranteed features of every `simpleitk` installation.

## Elastix Registration Pattern

```python
elastix = sitk.ElastixImageFilter()
elastix.SetFixedImage(fixed_image)
elastix.SetMovingImage(moving_image)
elastix.SetParameterMap(sitk.GetDefaultParameterMap("translation"))
elastix.AddParameterMap(sitk.GetDefaultParameterMap("affine"))
elastix.LogToConsoleOff()
result_image = elastix.Execute()
transform_parameter_maps = elastix.GetTransformParameterMaps()
```

- Parameter maps are dictionaries mapping string keys to lists of string values, for example `parameter_map["Transform"] = ["AffineTransform"]`.
- `sitk.GetDefaultParameterMap("translation")`, `"rigid"`, `"affine"`, and `"bspline"` are source-tested default map names.
- Multi-stage registration is represented by multiple parameter maps: `SetParameterMap(first_map)` then `AddParameterMap(next_map)`.
- `SetFixedMask` and `SetMovingMask` are available in source tests; masks must be spatially compatible with the images.
- Logging and output directories are optional; disable console/file logs in automation unless diagnostics are requested.

## Transformix Application Pattern

```python
transformix = sitk.TransformixImageFilter()
transformix.SetMovingImage(moving_image)
transformix.SetTransformParameterMaps(transform_parameter_maps)
transformix.ComputeDeformationFieldOn()
transformix.Execute()
warped = transformix.GetResultImage()
deformation = transformix.GetDeformationField()
```

- `TransformixImageFilter` applies transform parameter maps produced by elastix or read from parameter files.
- Set a moving image before execution; the Python test explicitly does this to avoid an input-required error.
- `ComputeDeformationFieldOn()` asks transformix to produce a vector deformation field when supported.
- The procedural `sitk.Transformix(...)` forms exist in source tests, but object-oriented use is easier to guard and diagnose.

## Parameter File IO

- `sitk.ReadParameterFile(path)` and `sitk.WriteParameterFile(parameter_map, path)` read and write elastix parameter maps when wrappers are built.
- Parameter map values are strings, not Python numbers: use `parameter_map["MaximumNumberOfIterations"] = ["512"]`, not `512`.
- Transform parameter maps from `GetTransformParameterMaps()` may contain output-directory or file references; inspect and sanitize paths before publishing configs.
- Keep reusable examples self-contained and avoid requiring repository example parameter files at runtime.

## Choosing Built-In Registration vs Elastix

- Prefer `ImageRegistrationMethod` when you need guaranteed SimpleITK availability, explicit metric/optimizer control, deterministic smoke tests, and direct `Transform` objects.
- Consider elastix when the runtime install exposes wrappers and the task needs elastix parameter maps, multi-stage elastix presets, transformix deformation fields, or interoperability with existing elastix configs.
- If wrappers are missing, either route to build guidance or rewrite the task with built-in SimpleITK transforms and `ImageRegistrationMethod`.

## Evidence Anchors

- `Code/ElastixTransformixWrappers/` contains C++ wrappers for `ElastixImageFilter`, `TransformixImageFilter`, parameter maps, logging, masks, output directories, and deformation-field flags.
- `Examples/Elastix/Registration/elx.py` demonstrates `ElastixImageFilter`, `ReadParameterFile`, `SetParameterMap`, `Execute`, `GetResultImage`, and `WriteParameterFile`.
- `Examples/Elastix/Registration/tfx.py` demonstrates `TransformixImageFilter`, `ReadParameterFile`, `SetTransformParameterMap`, `Execute`, and `GetResultImage`.
- `Examples/Elastix/ParameterMaps/ParameterMaps.py` demonstrates `GetDefaultParameterMap`, map modification, multi-stage registration, and parameter file round trips.
- `Wrapping/Python/tests/sitkTransformixImageFilterTest.py` shows transformix deformation-field computation and the need to set the moving image.
- `Testing/Unit/sitkElastixImageFilterTests.cxx` and `Testing/Unit/sitkTransformixImageFilterTests.cxx` cover default parameter maps, masks, procedural wrappers, transform parameter maps, and deformation fields.
