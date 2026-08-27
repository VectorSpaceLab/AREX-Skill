# Resources and React Runtime

## When to read

Read this for `_js_dist`, `_css_dist`, local-versus-CDN resource loading,
and React version/shim behavior.

## Resource loading model

Dash collects resources from component packages and from app-level script/style
registration. The important resource fields are:

- `namespace`
- `relative_package_path`
- `external_url`
- `dev_package_path`
- `dynamic`
- `async`
- `external_only`
- `attributes`

Behavioral rules:

- `serve_locally=True` uses package resources when available.
- `serve_locally=False` prefers external URLs.
- `dev_package_path` is used for dev bundles and debugging helpers.
- `dynamic=True` means the resource is loaded on demand.
- `async` controls dynamic loading mode and interacts with eager-loading.
- Invalid combinations like both `dynamic` and `async` on one resource should be
  treated as a resource definition error.

## React version details

Dash currently exposes a React runtime selection mechanism. Verified baseline
facts:

- Default React version is `18.3.1`.
- `18.2.0` and `19.2.4` are also supported by the runtime selector.
- React 19 uses a shim/runtime strategy so component bundles can still resolve
  the expected JSX runtime globals.

Important guidance:

- If a component bundle externalizes `react/jsx-runtime`, use Dash's defensive
  externalization pattern rather than a bare global name.
- A React 19 bundle error that mentions `ReactJSXRuntime` usually means the shim
  was not loaded or the bundle expects the wrong external expression.

## Built-in component resources

The built-in component packages ultimately register JS/CSS resources under the
Dash package namespace. When a generated wrapper import fails, do not jump to a
renderer bug until you have confirmed that the corresponding package resources
exist and the package was generated or installed correctly.

## Safe checks

- Inspect `dash-generate-components --help` and `dash-update-components --help`.
- Check whether the generated wrapper class imports from `dash`, `dcc`, `html`,
  or `dash_table` succeed in the current environment.
- Confirm browser console errors only after resource installation/namespace issues
  are ruled out.
