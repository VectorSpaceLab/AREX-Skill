# Troubleshooting

Use this table when the sim2sim deployment fails.

| Symptom | Likely cause | What to check | Fix |
|---|---|---|---|
| `policy` path is missing | Export never happened or the wrong path was passed | Confirm that the file is a TorchScript export such as `policy_1.pt` or `policy_example.pt` | Route to `training-and-evaluation` to export a policy, then rerun the validator |
| TorchScript shape error such as `mat1 and mat2 shapes cannot be multiplied (1x47 and 705x512)` | A single-frame or wrong-width tensor was fed to a 705-D policy | Check the input width used by the validator and the current observation contract | Use the 705-D contract for this sub-skill, or treat a changed frame stack as `environment-customization` work |
| Output is not 12-D | Policy export or robot action space does not match XBot-L | Check the exported model and the current `num_actions` contract | Use a 12-action policy or rework the environment first |
| Missing MJCF, URDF, meshes, or `uneven.png` | Repo resource tree is incomplete or the wrong root was used | Check `XBot-L.xml`, `XBot-L-terrain.xml`, `XBot-L.urdf`, the mesh directory, and the terrain image | Restore the resource tree before launch |
| MuJoCo XML parse/version error | Incompatible MuJoCo package or broken asset file | Check `import mujoco`, the installed version, and whether the XML parses | Use the supported MuJoCo stack and revalidate the XML files |
| `mujoco_viewer` / OpenGL / X11 / EGL failure | No graphical session or no usable GL backend | Check `DISPLAY`, remote session setup, and GPU/display passthrough | Use a real graphical session or configure a valid X11/EGL/OSMesa path; this source has no headless flag |
| Terrain launch fails but plane works | Wrong MJCF choice or missing terrain image | Check whether `--terrain` was added and whether `terrain/uneven.png` exists | Use plane mode for a flat sanity check or restore the terrain asset |
| Policy loads but behavior is clearly off | Command velocities or PD constants do not match the source loop | Check `vx=0.4`, `vy=0.0`, `dyaw=0.0`, `action_scale=0.25`, `decimation=10`, `kps`, `kds`, and `tau_limit` | Match the source constants or treat the change as a control/environment customization |
| Need a headless launch flag | The source script does not define one | Inspect the CLI parser in `sim2sim.py` | Do not assume headless is supported; use a display path or edit the source first |
| A custom policy expects a different frame stack or action count | The environment contract changed | Check `frame_stack`, `num_single_obs`, and `num_actions` | Move the change to `environment-customization` and re-export the policy |

## Useful diagnosis commands

- Validate the assets and optional policy first:
  ```bash
  python scripts/validate_sim2sim_assets.py --repo-root <repo-root> --policy <policy.pt>
  ```
- Print a safe launch command:
  ```bash
  python scripts/build_sim2sim_command.py --policy <policy.pt> [--terrain]
  ```

If the validator passes but the viewer fails, the problem is usually the display stack rather than the policy shape or the asset tree.
