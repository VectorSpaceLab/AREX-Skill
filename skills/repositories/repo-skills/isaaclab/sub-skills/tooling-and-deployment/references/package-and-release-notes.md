# Package and Release Notes

## Package layout signals

Repository package metadata is split across the core `source/*` package directories and the top-level repository metadata files.

Useful facts to keep in mind:

- The core extension metadata version comes from the package `extension.toml` files.
- Optional install groups are controlled by extras in the package setup files.
- The top-level `VERSION` file records the repository version snapshot.
- The main `setup.py` files describe the install-time dependency floors and extras for each package.

## Changelog fragment policy

When a change affects public behavior, add a fragment instead of editing the compiled changelog directly.

Rules to remember:

- Use a fragment under the touched package's `changelog.d/` directory.
- Pick a suffix based on bump severity: patch, minor, major, or skip.
- Write the fragment in past tense.
- Keep migration guidance in `Changed`, `Deprecated`, or `Removed` entries.
- Use the public symbol names and avoid private implementation details.

## Packaging caution points

- Keep package metadata consistent across related subpackages when they share a dependency constraint.
- Avoid widening dependency floors without a user-facing reason.
- Treat optional packages such as teleop, mimic, or contributed deployment extras as opt-in paths rather than baseline installs.
- Do not edit compiled release artifacts by hand when a fragment-based workflow exists.
