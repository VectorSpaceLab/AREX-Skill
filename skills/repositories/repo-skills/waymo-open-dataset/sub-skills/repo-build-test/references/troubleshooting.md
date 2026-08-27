# Build and Test Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Wheel install fails on `jaxlib==0.4.13` | Python too new or old JAX wheel not on index | Use Python 3.10 and official JAX release links, or move to a newer compatible WOD wheel. |
| Bazel target not found | Running from wrong directory or using old target name | Run from `src` and query package targets with Bazel before testing. |
| Custom op or metric op ABI errors | TensorFlow and WOD wheel/compiled target mismatch | Align TensorFlow version with the package line and rebuild/install matching artifacts. |
| Docker build path fails | Wrong build context, Dockerfile path, or mount path | Use `src` as build context for pip package Docker workflows and verify output mount. |
| Requirements update churn | Broad dependency resolver changes | Review `requirements.in`, regenerate once, and run focused import/tests before committing. |
| Full `bazel test ...` takes too long | Full repository includes many C++/TF tests | Start with changed-package focused tests, then escalate to full tests only when needed. |
