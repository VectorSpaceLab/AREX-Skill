# Build and Test Workflows

## Package metadata

The Bazel wheel target defines distribution `waymo-open-dataset-tf-2-12-0` version `1.6.7`, Python tag `py3`, and a TensorFlow 2.13 dependency line. Requirements are pinned from `requirements.in` into `requirements.txt`.

## Focused Bazel tests

Use focused targets before full-repo tests. Examples:

```bash
cd src
bazelisk test //waymo_open_dataset/v2:component_test
bazelisk test //waymo_open_dataset/v2:dataframe_utils_test
bazelisk test //waymo_open_dataset/utils:box_utils_test
bazelisk test //waymo_open_dataset/metrics/python:config_util_test
```

Full tests are expensive:

```bash
cd src
bazelisk test ... --test_output=errors --subcommands --verbose_failures --sandbox_debug --keep_going 2>&1 | tee bazel_wod_test.log
```

## Wheel build

Without Docker, install Bazelisk and run:

```bash
cd src
bazelisk build //waymo_open_dataset/pip_pkg_scripts:wheel
```

For manylinux-style Docker builds, use the documented build container and copy wheels from the output mount. Treat this as an expensive build workflow that may run all tests.

## Requirements update

```bash
cd src
bazelisk run //waymo_open_dataset:requirements.update
```

After updating requirements, rerun focused tests for changed areas and package import checks.

## Jupyter/tutorial container

The docs describe building an `open_dataset` image and running a notebook server on port 8888. This is for tutorial exploration, not required for library use.
