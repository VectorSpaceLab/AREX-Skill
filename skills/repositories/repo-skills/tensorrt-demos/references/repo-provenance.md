# Repository Provenance

Read this before deciding whether the generated graph is current for another
checkout. Run a refresh when the commit, dirty paths, public entry points, or
major evidence paths differ.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "tensorrt_demos",
    "remote_url": "https://github.com/jkjung-avt/tensorrt_demos",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c7c7f035c7d29ed3ccdf0bd66d9cb06ff493a2db",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "tensorrt_demos", "version": null, "import_names": ["pytrt", "utils"]}
  ],
  "evidence": {
    "source_roots": ["utils", "modnet/torch2onnx", "pytrt.pyx", "trtNet.cpp"],
    "docs": ["README.md", "README_x86.md", "README_mAP.md", "googlenet/README.md", "ssd/README.md", "modnet/README.md", "plugins/README.md"],
    "examples": ["trt_googlenet.py", "trt_googlenet_async.py", "trt_mtcnn.py", "trt_ssd.py", "trt_ssd_async.py", "trt_yolo.py", "trt_yolo_cv.py", "trt_yolo_mjpeg.py", "trt_modnet.py"],
    "tests": ["test_modnet.py", "modnet/test_onnx.py"],
    "configs": ["setup.py", "Makefile", "common/Makefile.config", "plugins/Makefile", "yolo/requirements.txt", "modnet/torch2onnx/requirements.txt"]
  }
}
```

The source graph deliberately excludes generated engines, compiled plugins and
extensions, model/data binaries, calibration caches, system-mutating download
scripts, and the uninitialized third-party ONNX-TensorRT submodule. Those
artifacts remain task-owned inputs, not public runtime dependencies of this
skill.
