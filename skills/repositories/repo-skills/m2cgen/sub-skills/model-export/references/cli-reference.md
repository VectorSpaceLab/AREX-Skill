# CLI reference

## Entry points

Use either of these entry points:

```bash
python -m m2cgen --language python model.pkl
m2cgen --language python model.pkl
```

Both paths call the same CLI implementation and dispatch to the same exporter functions as the Python API.

## Syntax

```bash
m2cgen [infile] --language <language> [--indent <n>] [--function_name <name>]
        [--class_name <name>] [--module_name <name>] [--package_name <name>]
        [--namespace <name>] [--recursion-limit <n>] [--pickle-lib pickle|joblib]
```

### Arguments

| Option | Required? | Meaning |
| --- | --- | --- |
| `infile` | no | Binary file containing the serialized fitted model. If omitted, reads bytes from stdin. |
| `--language`, `-l` | yes | Target language. Choices are listed below. |
| `--function_name`, `-fn` | no | Generated function or method name. Defaults to the selected exporter's own default. |
| `--class_name`, `-cn` | no | Generated class name when the target supports classes. |
| `--package_name`, `-pn` | no | Java package name. |
| `--module_name`, `-mn` | no | Module name for Visual Basic, Haskell, and Elixir. |
| `--namespace`, `-ns` | no | C# namespace. |
| `--indent`, `-i` | no | Indentation width. Default is `4`. |
| `--recursion-limit`, `-rl` | no | Sets Python recursion depth before export. Useful for large ensembles. |
| `--pickle-lib`, `-pl` | no | Deserialization library: `pickle` or `joblib`. Default is `pickle`. |
| `--version`, `-v` | no | Print package version. |

## Supported language choices

`python`, `java`, `c`, `go`, `javascript`, `visual_basic`, `c_sharp`, `powershell`, `r`, `php`, `dart`, `haskell`, `ruby`, `f_sharp`, `rust`, `elixir`

## Input modes

### Pickle file input

```bash
m2cgen model.pkl --language java > Model.java
```

### stdin piping

```bash
cat model.pkl | python -m m2cgen --language python > model_score.py
```

### joblib file input

```bash
m2cgen model.joblib --language go --pickle-lib joblib > model.go
```

### stdin with custom naming

```bash
cat model.pkl | python -m m2cgen \
  --language c_sharp \
  --namespace Demo.Models \
  --class_name CreditRiskModel \
  --function_name ScoreRisk \
  > CreditRiskModel.cs
```

Expected shape for the C# example: a `namespace Demo.Models` block containing a static class `CreditRiskModel` with a static method `ScoreRisk`.

## Naming behavior by target

| Target | Useful naming flags | Expected code shape |
| --- | --- | --- |
| Java | `--package_name`, `--class_name`, `--function_name` | optional `package ...;`, `public class <class_name>`, static method |
| C# | `--namespace`, `--class_name`, `--function_name` | `namespace <namespace>`, static class, static method |
| Visual Basic | `--module_name`, `--function_name` | `Module <module_name>`, `Function <function_name>` |
| Haskell | `--module_name`, `--function_name` | `module <module_name> where`, typed function |
| Elixir | `--module_name`, `--function_name` | `defmodule <module_name>`, `def <function_name>` |
| Other targets | `--function_name` | target-specific standalone function |

Unsupported naming flags are ignored by the CLI dispatcher for targets whose exporter does not accept them.

## Recursion tuning

For very large forests or boosted trees:

```bash
python -m m2cgen model.pkl --language java --recursion-limit 10000 > Model.java
```

Prefer reducing model size/depth when possible; raising recursion depth only makes export possible, it does not make the generated code smaller.

## Serialization requirements

- The model object must already be fitted before serialization.
- The class that created the serialized model must be importable in the export environment.
- `pickle` is the default; use `--pickle-lib joblib` for joblib files.
- Install optional estimator libraries before loading their serialized objects.

## Console-script fallback

If `m2cgen` is not on `PATH`, use `python -m m2cgen`. If `python -m m2cgen` works but the console script does not, the package is importable but the environment's script entry points are not exposed on `PATH`.