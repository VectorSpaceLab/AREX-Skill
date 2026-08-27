# Data and Configuration Troubleshooting

Use this table when a DeePMD-kit data system or training input fails before, during, or immediately after data loading.

## Symptom Matrix

| Symptom | Likely cause | Check | Repair |
| --- | --- | --- | --- |
| `type.raw` missing or loader says no system found | Path points at parent/raw/artifact folder instead of a DeePMD system | Look for root `type.raw` and at least one `set.*` | Point `systems` at the converted system, or use recursive parent discovery only after validating included folders. |
| Element names seem swapped, errors are huge, or energy bias is wrong | `type_map.raw` order differs from `model.type_map`, or `type_map.raw` is absent | Compare `type.raw`, root `type_map.raw`, and config `model.type_map` | Add/fix `type_map.raw`; keep all system element names in `model.type_map`; avoid changing type order after checkpointing. |
| Assertion about type map length | `max(type.raw)` is greater than available names | Inspect `max(type.raw)` and number of names in `type_map.raw` | Add missing names in the correct order or fix invalid type ids. |
| Periodic data fails loading boxes | `box.npy` is missing from one or more sets | Run `inspect_deepmd_system.py`; check `nopbc` | Add `box.npy` shaped `(Nframes, 9)` for periodic data, or add `nopbc` for truly non-periodic systems. |
| Non-periodic workflow still expects virials/box metrics | `nopbc` mismatch or virial loss left active | Check `nopbc`, `virial.npy`, and virial prefactors | For non-periodic systems, mark `nopbc`, disable virial loss, and avoid box-dependent testing. |
| Shape mismatch for `coord.npy` | Wrong atom count, flattened dimension not `Natoms * 3`, or bad frame axis | Compare `coord.npy.shape` with `len(type.raw)` | Re-convert data, reshape to `(Nframes, Natoms * 3)`, or split systems by atom count/formula. |
| Shape mismatch for `force.npy` or `aparam.npy` | Atomic label dimension does not match `Natoms * ndof` | Check label total width | Re-export labels with the same atom order as `coord.npy` and `type.raw`. |
| Missing virial errors | Nonzero virial prefactors but no `virial.npy` | Inspect `loss.start_pref_v`/`limit_pref_v` and system files | Provide `virial.npy` for each system or set virial prefactors to zero. |
| Hessian branch fails | Hessian label missing, flattened size wrong, or only one task owns Hessians | Inspect `hessian.npy` and `loss_dict` task keys | Add `hessian.npy` only to Hessian systems and nonzero Hessian prefactors only to matching task branches. |
| Tensor model complains about global/atomic labels | `dipole`/`polarizability` file uses atomic shape with global filename or vice versa | Compare file name and width to `pref`/`pref_atomic` | Use global files for global tensor loss and `atomic_*` files for atomic tensor loss. |
| DOS model shape error | `dos.npy`/`atom_dos.npy` width does not match fitting `numb_dos` | Compare label width to `numb_dos` and `Natoms * numb_dos` | Regenerate DOS labels or update fitting output dimension. |
| Property model cannot find labels | File named by `property_name` is absent | Check fitting `property_name` and set files | Rename or regenerate the property label file, e.g. `band_prop.npy`. |
| Spin metrics/loss fails | `spin.npy`, `force_mag.npy`, or magnetic masks are inconsistent | Check `model.spin`, `loss.type: ener_spin`, and files | Include `spin.npy`; include `force_mag.npy` only when magnetic force is supervised/tested. |
| Mixed-type loader says all sets must match mode | Some sets have `real_atom_types.npy` and others do not | Inspect every `set.*` | Convert all sets consistently to mixed-type or split into separate systems. |
| Mixed-type complains about type map | `type_map.raw` missing or `real_atom_types.npy` has out-of-range ids | Check root `type_map.raw` and min/max real atom types | Add complete `type_map.raw`; use `-1` only for virtual atoms; fix invalid positive ids. |
| Multiple formulas in one standard folder | Standard format has system-level `type.raw`, not frame-level types | Compare formulas per frame/source | Split by formula or convert to mixed-type with `real_atom_types.npy`. |
| Invalid JSON/YAML | Syntax error, wrong field name, or unsupported alias for installed version | Run parser/schema generation with `dp doc-train-input` | Repair syntax, regenerate schema, and use installed-version field names. |
| Training starts with long neighbor-stat pass | Descriptor selection uses `auto` on large data | Search config for `sel`, `nsel`, `e_sel`, `a_sel`, `three_body_sel` values of `auto` | Use explicit safe selections for debugging, reduce systems, or route training strategy to `../training-models/SKILL.md`. |
| Recursive `systems` picked unexpected data | Parent path contains raw folders, validation folders, or artifacts | Print collected systems through DeePMD logs or inspect tree | Use explicit lists or `rglob_patterns` to control discovery. |
| LMDB batch memory spikes | Variable local atom counts with unconstrained `batch_size` | Check LMDB frame atom counts if available | Use `max:N` or `filter:N` batch styles; start with `batch_size: 1` for debugging. |

## Type Map Debug Recipe

1. Read system root files:

   ```text
   type.raw       -> integer ids per atom
   type_map.raw   -> name for each integer id
   ```

2. Read config map:

   ```json
   "model": {"type_map": ["H", "O", "Si"]}
   ```

3. Verify:

   - `len(type_map.raw) > max(type.raw)`.
   - Every name in `type_map.raw` appears in `model.type_map`.
   - All systems use compatible names even if local integer order differs.
   - No downstream checkpoint/frozen model expects a different order.

4. If a data-only repair is possible, fix `type_map.raw` rather than changing model order.

## PBC and `nopbc` Recipe

- Periodic system:
  - No `nopbc` marker.
  - Every `set.*` has `box.npy` with `Nframes` rows and 9 values per frame.
  - Virial labels may be used if present and configured.
- Non-periodic system:
  - Root contains `nopbc` marker.
  - `box.npy` is optional and should not be relied on.
  - Virial metrics/loss are usually disabled.

If a system mixes PBC assumptions across sets, normalize it before training. Do not add dummy identity boxes to non-periodic data unless the physics and target workflow explicitly require periodic treatment.

## Mixed-Type and Virtual Atom Recipe

Use mixed-type only when the intended model workflow supports it.

- Root `type.raw`: placeholder length `Natoms`, often all zeros.
- Root `type_map.raw`: all real element names.
- Every set: `real_atom_types.npy` with shape `(Nframes, Natoms)`.
- Virtual atoms: `-1` in `real_atom_types.npy`.
- Atomic labels for virtual atoms: zeros for force-like/property-like arrays.
- Systems in one dataset: all standard or all mixed-type, not a mixture.

Common repair: if frames have different atom counts, pad coordinates and atomic labels to a common `Natoms`, mark padded atoms `-1`, and ensure padded labels are zero.

## Label/Config Ownership Recipe

When labels are missing, do not blindly create empty `.npy` files. First decide whether the config should request the label.

- Missing `energy.npy`: only valid when the selected workflow does not train/test energies.
- Missing `force.npy`: usually invalid for energy-force training with nonzero force weights.
- Missing `virial.npy`: valid if virial prefactors are zero or the system is non-periodic and virial metrics are not requested.
- Missing `hessian.npy`: valid for non-Hessian tasks; invalid for branches with nonzero Hessian prefactors.
- Missing `atom_pref.npy`: valid unless weighted force loss is active and backend defaults are not applicable.
- Missing `fparam.npy`/`aparam.npy`: valid only if the model dimension is zero or default parameters are available.

## Sparse Formula Repair

For source data with many formulas:

1. Group frames by formula and atom ordering.
2. For standard data, create one system per group.
3. For training, list all systems under `training_data.systems` and tune `auto_prob`/`sys_probs` if rare formulas matter.
4. For compatible mixed-type workflows, pad to a common atom count and use `real_atom_types.npy` instead of many tiny systems.
5. Keep validation split formula-aware so rare formula performance is visible.

## Fast Sanity Commands

From the generated skill subtree, use the bundled inspector for NumPy directories:

```bash
python sub-skills/data-config/scripts/inspect_deepmd_system.py /path/to/system --pretty
python sub-skills/data-config/scripts/inspect_deepmd_system.py /path/to/system --expect-type-map O H
python sub-skills/data-config/scripts/inspect_deepmd_system.py /path/to/system --max-sets 2 --pretty
```

Generate installed-version config docs when the CLI is available:

```bash
dp doc-train-input --out-type json_schema > deepmd-train.schema.json
```

The inspector intentionally performs read-only filesystem checks and does not import DeePMD-kit. Use backend-specific DeePMD commands after this preflight and after routing training/inference tasks to their owning sub-skills.
