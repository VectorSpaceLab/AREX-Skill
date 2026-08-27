# Custom ops and partitioning

Use this guide when a change adds backend custom ops, backend op tests, or ONNX partition marks.

## Custom-op decision points

Before implementing an op, decide which layer owns the change:

| Need | Extension point |
| --- | --- |
| Export should emit a different ONNX node | symbolic rewrite in Python |
| Backend must execute a custom domain op | backend custom-op/plugin implementation |
| Backend converter must rewrite ONNX into backend-native layers | backend converter/pass code |
| Test should validate backend execution | backend op unit test with exporter utility |

Keep the Python symbolic and backend implementation aligned on:
- domain, usually `mmdeploy` for custom exported nodes;
- op type string;
- attribute names and suffixes such as `_i`, `_f`, `_s` in `g.op(...)` calls;
- tensor input order;
- output count and output names.

## Backend custom-op structure

The backend custom-op tree is organized by backend.

Common patterns:
- common helper code shared by backend ops;
- ONNXRuntime custom-op registration plus one directory per op;
- TensorRT plugin directory per op plus common CUDA/plugin helpers;
- NCNN conversion and op registration files;
- TorchScript custom op/optimizer bindings.

When adding an op:
1. add or update the Python symbolic/rewrite that emits the custom node;
2. add backend implementation and registration in the backend-specific tree;
3. ensure build files include the new source files;
4. expose/load the custom-op library through the backend package;
5. add a backend op test that skips cleanly when the backend/plugin is absent.

## Backend op unit-test template

Use this shape for focused custom-op tests:

```python
import pytest
import torch
from mmengine import Config
from mmdeploy.core import RewriterContext
from mmdeploy.utils.test import WrapFunction

@pytest.mark.parametrize('backend', [TEST_TENSORRT, TEST_ONNXRT])
def test_my_custom_op(backend, save_dir=None):
    backend.check_env()

    x = torch.rand(1, 3, 8, 8)

    def wrapped_function(x):
        # call the Python op or autograd Function that should export to the
        # backend custom op
        return my_exportable_op(x)

    wrapped_model = WrapFunction(wrapped_function).eval()

    deploy_cfg = Config({'backend_config': {'type': backend.backend_name}})
    with RewriterContext(deploy_cfg, backend=backend.backend_name, opset=11):
        backend.run_and_validate(
            wrapped_model,
            [x],
            'my_custom_op',
            input_names=['input'],
            output_names=['output'],
            dynamic_axes=None,
            expected_result=None,
            save_dir=save_dir)
```

Adjust the template when:
- the expected result must be computed manually;
- dynamic axes are required;
- the model under test is an ONNX `ModelProto` instead of a PyTorch module;
- the backend needs `tolerate_small_mismatch=True` because of precision differences.

## Partition marks

`@mark` creates `mmdeploy::Mark` nodes in ONNX. It is used to identify partition start/end points.

Important rules:
- put `@mark` inside a function that is executed by a rewrite path;
- set stable `inputs` and `outputs` names;
- use `RewriterContext` during export;
- set `partition_config.apply_marks=True` in the deployment config;
- for TorchScript export, marks are removed instead of traced.

Minimal pattern:

```python
from mmdeploy.core import FUNCTION_REWRITER, mark

@FUNCTION_REWRITER.register_rewriter('some.package.Model.forward')
def model_forward__rewrite(self, x, *args, **kwargs):
    @mark('model_forward', inputs=['input'], outputs=['features'])
    def _impl(x):
        return FUNCTION_REWRITER.get_context().origin_func(
            self, x, *args, **kwargs)
    return _impl(x)
```

Mark metadata includes the mark function name, call index, input/output type, tensor name, tensor id, dtype, and shape. For lists, tuples, or dict outputs, names can receive suffixes such as `.0` or `.key`.

## `partition_config`

A partition config names the marks to extract.

Shape:

```python
partition_config = dict(
    type='my_partition_policy',
    apply_marks=True,
    partition_cfg=[
        dict(
            save_file='part0.onnx',
            start=['model_forward:input'],
            end=['model_forward:output'],
            output_names=['features'],
            dynamic_axes={'input': {0: 'batch'}, 'features': {0: 'batch'}})
    ])
```

Rules:
- `get_partition_config()` returns `None` unless `apply_marks=True`;
- `start` and `end` strings must match actual mark names in the exported ONNX graph;
- use `mark_name[index]:input` or `mark_name[index]:output` when multiple calls to the same mark occur and the exact call index matters;
- keep `output_names` and `dynamic_axes` aligned with the extracted graph.

## Relation to `extract_model`

`extract_model` extracts an ONNX subgraph from marker names.

Inputs:
- model path or loaded ONNX model;
- start marker or marker list;
- end marker or marker list;
- optional start/end name maps;
- optional dynamic axes;
- optional save file.

Use it after the full ONNX graph contains `Mark` nodes. If extraction returns the wrong graph, inspect the exported ONNX graph first and confirm that the actual marker strings match the config.

## What to verify

- ONNX graph contains the expected custom op domain and op type.
- Backend op library loads when `with_custom_ops=True` is required.
- Backend test skips cleanly if the backend package/plugin is unavailable.
- Backend output is close to PyTorch or manually computed expected output.
- Partition marks appear only when expected and extraction uses the intended boundary tensors.
