# Core Services and Runtime Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'msgq.ipc_pyx'` | msgq Cython extension is missing | Build the msgq native targets in the target checkout. |
| `libparams_c.so` missing | Params shared library was not built | Build `openpilot/common/libparams_c.so`. |
| `UnknownKeyName` | Params key is not defined or the task used the wrong namespace | Verify the key name and whether the task should touch Params at all. |
| `SubMaster`/`PubMaster` tests hang | readers are not synchronized, or the socket is not published | Start with focused messaging tests, then use small helper scripts with explicit timeouts. |
| `generated services header is not valid C` plus `clang++: not found` | service-header validation test needs a host C++ compiler, not just Python/msgq imports | Install the repo's host compiler dependencies or skip this maintainer-style check on a minimal CPU inspection host. |
| loggerd tests leave files behind | temp log root not cleaned or host path mismatch | Use isolated temp dirs and inspect `Paths.log_root()` before blaming the test. |
| xattr/lock failures in uploader/deleter | filesystem does not support expected xattrs or the test is running on a nonstandard host filesystem | Use a filesystem with xattr support or treat the test as environment-sensitive. |
| onroad/power tests fail on CPU host | hardware/comma device assumptions are missing | Mark as skipped unless the device, camera, and runtime setup are available. |
| live timing helpers never exit | they are designed as continuous monitors | Use them only for debugging; do not treat them as finite verification gates. |
