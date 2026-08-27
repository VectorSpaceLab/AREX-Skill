# Extending Nerfstudio

## Package entry points

Custom extensions are packaged as ordinary Python distributions that expose one of the following entry-point groups:

- `nerfstudio.method_configs`
- `nerfstudio.dataparser_configs`

A custom method typically exposes a `MethodSpecification` instance that wraps a `TrainerConfig`. A custom dataparser typically exposes a `DataParserSpecification` that wraps a dataparser config.

## Temporary registration

During development, the package can be registered without installation through environment variables:

```bash
export NERFSTUDIO_METHOD_CONFIGS="my-method=my_package.my_module:MyMethod"
export NERFSTUDIO_DATAPARSER_CONFIGS="my-parser=my_package.my_module:MyParser"
```

The value may point to a method/config object, a function that returns one, or a subclass-style object supported by the registry helpers.

## Config conventions

- Use dataclass configs and `_target` fields to point to the implementation class.
- Keep the config surface typed so `tyro` can expose it from CLI help.
- Avoid hidden package-level side effects; the registry should discover the object, not require a custom launcher.

## Discovery checks

- `ns-train --help` should show the new method when it is registered correctly.
- The plugin registry tests are the best lightweight proof that the environment variable or entry point is working.

## Packaging caution

A method/dataparser package must be installed or editable-installed in the same Python environment used by `ns-train`. A successful import from another interpreter is not enough.
