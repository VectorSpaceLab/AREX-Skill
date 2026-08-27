# API reference

`m2cgen` exports a fitted Python model object to a source-code string. The API does **not** train the model and does **not** write files for you.

```python
import m2cgen as m2c

code = m2c.export_to_java(model, package_name="demo.models", class_name="TinyModel")
```

## Public export surface

All public helpers live at `m2cgen` top level and in `m2cgen.exporters`.

| Function | Target | Signature shape | Notes |
| --- | --- | --- | --- |
| `export_to_java` | Java | `(model, package_name=None, class_name='Model', indent=4, function_name='score')` | Supports package/class naming. |
| `export_to_python` | Python | `(model, indent=4, function_name='score')` | Useful for a standalone generated Python scorer. |
| `export_to_c` | C | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_go` | Go | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_javascript` | JavaScript | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_visual_basic` | Visual Basic | `(model, module_name='Model', indent=4, function_name='Score')` | Module wrapper; VBA-compatible with manual adjustment. |
| `export_to_c_sharp` | C# | `(model, namespace='ML', class_name='Model', indent=4, function_name='Score')` | Supports namespace/class naming. |
| `export_to_powershell` | PowerShell | `(model, indent=4, function_name='Score')` | Function-only output. |
| `export_to_r` | R | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_php` | PHP | `(model, indent=4, function_name='score')` | Emits a PHP file header. |
| `export_to_dart` | Dart | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_haskell` | Haskell | `(model, module_name='Model', indent=4, function_name='score')` | Module wrapper. |
| `export_to_ruby` | Ruby | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_f_sharp` | F# | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_rust` | Rust | `(model, indent=4, function_name='score')` | Function-only output. |
| `export_to_elixir` | Elixir | `(model, module_name='Model', indent=4, function_name='score')` | Module wrapper. |

## Shared contract

- **Input**: a fitted estimator/booster object from a supported family.
- **Output**: a string containing generated source code.
- **Unsupported model**: raises `NotImplementedError` with the concrete runtime model name.
- **Unsupported kwargs**: the Python API rejects kwargs that are not in the function signature.

## Naming rules

- `function_name` defaults to `score` for most targets.
- `function_name` defaults to `Score` for Visual Basic, C#, and PowerShell.
- Java uses `package_name` and `class_name`.
- C# uses `namespace` and `class_name`.
- Visual Basic, Haskell, and Elixir use `module_name`.

## Useful notes

- The API mirrors the CLI exporter surface; the CLI is a thin wrapper around the same functions.
- Generated code is returned as text; write it to disk yourself if needed.
- The package imports a base `numpy` dependency, but the fitted model's library must still be installed if you are loading a serialized object.