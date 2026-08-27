# Extension troubleshooting

## Custom method is not visible in `ns-train --help`

Check the following in order:

1. The package is installed in the same environment used by the CLI.
2. The entry-point group is `nerfstudio.method_configs`.
3. The entry-point object resolves to a `MethodSpecification` or compatible return value.
4. The `method_name` inside the config is the name you expect to see.

## Custom dataparser is not visible

- Use the `nerfstudio.dataparser_configs` entry-point group.
- Ensure the dataparser specification resolves to a `DataParserSpecification` or compatible object.
- Reinstall the editable package after adding or renaming the entry point.

## Environment-variable registration fails

- Double-check the `name=module:object` syntax.
- Confirm the object exists and is importable from the target environment.
- If the environment variable points to a function, confirm the function returns the expected specification object.

## Config type errors

When the config is missing `_target` or a typed field has the wrong default, tyro help and the method registry can become misleading. Keep the config as a dataclass and prefer explicit types for nested configs.
