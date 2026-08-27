# syft-restrict policy

`syft-restrict` never runs model code. It parses Python source, resolves marked private regions, validates them with default-deny AST rules, and writes an obfuscated/hiding output when requested.

Marker forms:

```python
# syft-restrict: obfuscate-start
class PrivateModel:
    def __call__(self, x):
        return x + 1
# syft-restrict: obfuscate-end

SECRET = "x"  # syft-restrict: hide
```

A file with no markers raises `MarkerError`. Private regions reject imports, dynamic code, `with`, `try`/`raise`, async, generators, `assert`, `del`, f-strings, walrus, `match`, decorators, and unallowed calls/operators. Use explicit `allow_functions` and `allow_operators` for trusted math libraries and arithmetic/indexing/comparison operations.

Safe check:

```bash
python scripts/verify_obfuscate_file.py model.py --out model.obfuscated.py --allow-operator arithmetic
```
