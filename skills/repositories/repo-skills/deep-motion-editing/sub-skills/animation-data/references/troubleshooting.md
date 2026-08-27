# Animation-data troubleshooting

## Triage table

| Symptom | Likely cause | Safe diagnosis and bounded remedy |
| --- | --- | --- |
| `BVH parse error: ...` or missing `MOTION` | Truncated/malformed hierarchy, wrong file type, or a vendor extension | Run `inspect_bvh.py INPUT.bvh --json`; inspect the first failing section. Copy the file before any repair. Do not feed a partial hierarchy to a model. |
| Motion row has too few/many values | Channel declaration disagrees with frame data, often after deleting a joint by hand | The validator reports expected vs observed channel count. Restore the source export or regenerate both hierarchy and rows together; do not pad with zeros unless the downstream format explicitly defines those channels. |
| `Frames` differs from rows | Truncated transfer or stale header | Re-export or repair the header only after confirming all rows are complete. A header edit cannot recover missing motion. |
| Unknown skeleton / `Problem in file` | Retargeting hard-coded joint family does not exactly match names, order, or end-effectors | Compare names and parents, including namespace prefixes. Configure a complete new family in `bvh_parser.py` in the user's source checkout and test one copied fixture. Do not choose the nearest list. |
| Round-trip has changed the pose | Euler order, quaternion convention, offsets, or root translation were changed | Compare normalized rotation matrices and root/offset arrays; verify `xyz` versus `zyx` at every conversion. Keep input and output separate. A text round-trip can preserve topology while changing orientation if order is wrong. |
| Round-trip has extra/missing `End Site` | Writers synthesize zero-offset leaf markers and commonly discard source end-site lengths | This is expected for the repository writer. End sites have no channels. If end-site lengths matter for visualization, retain the source file or use a writer that accepts explicit end-site offsets; do not infer a model joint from an end site. |
| Feet slide in output | Contacts are noisy, joint IDs/order are wrong, or cleanup is being compared to raw motion | Confirm the contact tensor shape/order and skeleton end-effector map. Preserve `raw.bvh`, run cleanup only on a copy, and inspect the corrected file. Cleanup is IK-based and may change root/rotations. |
| `fixed.bvh` is absent | Cleanup was not run, output directory was wrong, or IK dependencies/checkpoint workflow failed | Confirm direct network output first, then invoke the style-transfer workflow's explicit cleanup stage. The data helper here does not generate `fixed.bvh`. |
| `fixed.bvh` looks below/above floor | `force_on_floor`, floor estimate, or BVH/Blender axis convention differs | Inspect BVH Y coordinates and the downstream visualization's axis swap separately. Do not apply Blender Z assumptions to the source BVH. |
| `AnimationData` assertion says rotations do not match skeleton | Full motion row has wrong channel count or a different skeleton | Check `(row_width - 8) % 4 == 0`, then compare J and skeleton metadata. Use the matching `skeleton_CMU.yml` or pass an explicit compatible `Skel`; do not reshape arbitrary channels. |
| Style transfer gets `FileNotFoundError` for `train_content.npz` | Normalization artifacts were not generated or config points at the wrong dataset | Put the user-provided normalization files in the configured extra-data directory, check `dataset_norm_config`, and use a matching `xia`/`bfa` dataset. This is not repaired by changing the BVH frame time. |
| OpenPose validator says required key missing | OpenPose JSON uses a different model/output schema or a person entry lacks hands/body | Regenerate with BODY_25 plus hand keypoints, or adapt a preprocessing stage explicitly. The source loader requires all three arrays even if confidence is unused. |
| Empty OpenPose `people` frames | No person detected | The source loader carries forward the last motion frame only after a person has appeared and backward-fills zeros. Review empty-frame count; do not treat it as trustworthy tracking. |
| Non-contiguous OpenPose names | Lexical ordering no longer represents time, or files were dropped | Rename to zero-padded contiguous frame names or supply a controlled preprocessing manifest. The validator does not rename files. |
| OpenPose JSON is accepted but output is upside down/offset | Source transformation flips y and subtracts the first root; scale is in model units | This is expected source normalization. Check `scale` and `smooth` arguments and compare raw pixels to the converted projection before changing model code. |
| `ModuleNotFoundError: numpy.core.umath_tests` | `utils/Animation.py` imports a removed NumPy private module | Use standalone text inspection. If the old class is required, test an isolated compatible NumPy pin or locally replace only the matrix multiply call with `numpy.matmul`, then run a copied tiny fixture. Do not claim all legacy methods are compatible after import succeeds. |
| `AttributeError: np.float` / `np.int` | Other legacy code uses removed NumPy aliases | Pin/patch only in a disposable environment after recording the exact failing path. Prefer a narrow compatibility edit (`float`, `int`) and rerun the targeted case; avoid broad automated rewrites. |
| PyTorch `Expected ...` shape error in FK | Caller mixed `(B, C, T)` and `(T, J, 4)` layouts | Use `AnimationData`/`ForwardKinematics` contracts: network inputs are channel-by-time, raw rotations are frame-by-joint. Print shapes before conversion and keep root position separate. |
| Kinematics gives implausible limbs | Parent topology is wrong or offsets are in a different skeleton/scale | Verify parent indices, offsets, and root position in a copied fixture. Kinematics is deterministic only for a consistent topology; it cannot repair mismatched names by itself. |
| Import works in one directory but not another | Legacy scripts depend on current directory and `sys.path` insertion | Run from the source workflow's documented directory or make imports explicit in a user-owned wrapper. The bundled validators deliberately do not depend on the source checkout. |
| Blender cannot import NumPy or project utilities | Blender 2.80 uses its own Python distribution | Install/check packages in Blender's Python or use Blender's documented interpreter replacement, then test `blender -b --python-expr ...`. Ordinary Conda imports do not prove Blender imports. |

## Compatibility decision record

The `numpy.core.umath_tests` failure is concrete and expected on modern NumPy. The affected module contains `transforms_multiply`, which only uses `ut.matrix_multiply`; an equivalent local implementation is `np.matmul(t0s, t1s)`. That is a plausible narrow patch, but it is not a verified repository change here because the old `Animation.py` also imports a legacy quaternion module and other code uses removed aliases. Use this escalation:

1. Structural-only need: run the bundled scripts and do not import `utils/Animation.py`.
2. Exact legacy utility need: make a disposable environment, record Python/NumPy versions, try a compatible NumPy pin, and run a copied tiny BVH fixture.
3. Maintained local fork need: patch the one matrix multiplication import/call and any separately observed aliases, run the tiny fixture round-trip plus FK numerical checks, and keep the patch in the user's fork—not in this runtime skill.

A failure in step 2 or 3 remains an unresolved compatibility block. Never convert it to a success merely because file parsing succeeded.

## Minimal diagnostic sequence

```bash
python <animation-data-skill>/scripts/inspect_bvh.py motion.bvh --json > motion.summary.json
python <animation-data-skill>/scripts/inspect_bvh.py motion.bvh --round-trip OUT_DIR/motion-copy.bvh
python <animation-data-skill>/scripts/inspect_bvh.py OUT_DIR/motion-copy.bvh --json
python <animation-data-skill>/scripts/validate_openpose_json.py path/to/json_frames --json
```
Replace `<animation-data-skill>` with the installed skill directory.

Use a temporary copied fixture, not a production output, for repair experiments. The commands above perform no network, model, or training operation; `--round-trip` only writes the explicitly named destination.
