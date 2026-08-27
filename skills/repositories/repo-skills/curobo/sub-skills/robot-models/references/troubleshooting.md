# Robot-model troubleshooting

- **YAML/config not found:** pass a bundled content-relative robot name or an
  explicit user-owned path; do not pass a path from a prior checkout.
- **URDF parse or mesh error:** check URDF package/mesh references, XML validity,
  active joints, mimic joints, and the selected base/tool links. Start from a
  simple bundled URDF to isolate parser versus geometry issues.
- **Unexpected DOF/joint order:** inspect `kin.joint_names`, `get_dof()`, and
  `JointState` names. Reorder named input state rather than silently slicing.
- **Bad FK pose:** confirm quaternion is wxyz, target tool frame is present, the
  input is in radians, and the device/dtype match `DeviceCfg`.
- **CUDA OOM:** select a free GPU, reduce batch size, and avoid generating large
  sphere sets until the model is valid.
- **Autograd has no gradient:** retain `requires_grad=True`, avoid converting
  the FK input to NumPy or detaching the output before computing the loss.
- **Builder output plans badly:** inspect sphere density, per-link padding,
  limits, tool frame, and self-collision ignore pairs before disabling costs.
