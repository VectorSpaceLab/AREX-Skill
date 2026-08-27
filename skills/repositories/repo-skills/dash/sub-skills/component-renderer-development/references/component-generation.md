# Component Generation

## When to read

Read this when a task involves generating or refreshing Dash component wrappers,
component metadata, or built-in component package artifacts.

## Generation pipeline

Dash component packages follow this flow:

1. React/TypeScript source defines component props and behavior.
2. Metadata is extracted from the source.
3. `dash-generate-components` maps metadata into Python wrapper classes.
4. Built-in package files are copied or refreshed in Dash's package tree.
5. The resulting package exposes component classes from `dash`, `dcc`,
   `html`, or `dash_table`.

## Important source facts

- `Component` is the Python base class for generated wrappers.
- `ComponentRegistry` tracks imported component modules and resources.
- `ComponentMeta` auto-registers components.
- `to_plotly_json()` serializes a component into `{type, namespace, props}`.
- `_children_props` describes nested component-bearing props that the renderer
  must crawl.

## CLI details

### `dash-generate-components`

Generates wrappers from React component metadata. Key arguments include:

- `components_source`
- `project_shortname`
- `--package-info-filename`
- `--ignore`
- `--r-prefix`
- `--r-depends`
- `--r-imports`
- `--r-suggests`
- `--jl-prefix`
- `--keep-prop-order`
- `--max-props`
- `--custom-typing-module`

Use `dash-generate-components --help` as a safe first check.

### `dash-update-components`

Refreshes Dash's built-in component package artifacts from their package
sources. It can also run npm install/build in the component packages before
copying the generated artifacts into the main Dash package.

Use `dash-update-components --help` before a full update. A full update may also
need Black in the active environment because the build scripts format generated
files.

### Built-in package notes

- The built-in HTML, DCC, and DataTable packages are separate npm/Python
  component packages.
- Their package scripts often combine npm install, React build, metadata
  generation, and Python wrapper generation.
- Keep wrapper generation and browser/runtime testing separate so that a failed
  build is easy to diagnose.

## Workflow tips

- When wrappers are missing in a development checkout, generate or refresh them
  before debugging app-level imports.
- When generated wrappers exist but browser behavior fails, route to the renderer
  internals reference.
- When a build script fails because a formatter is missing, install the explicit
  formatter/tool prerequisite and rerun the script.
