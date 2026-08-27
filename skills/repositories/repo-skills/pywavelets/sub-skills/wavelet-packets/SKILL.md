---
name: wavelet-packets
description: "Routes PyWavelets users through 1D, 2D, and ND wavelet packet tree
  construction, traversal, and reconstruction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Wavelet Packets

Use this sub-skill when the task is about packet trees rather than ordinary DWT/SWT coefficient lists.

## Route here when the task asks for

- `WaveletPacket`, `WaveletPacket2D`, or `WaveletPacketND`
- `BaseNode`, `Node`, `Node2D`, `NodeND`
- path-based lookup, tuple path access, or `path_tuple`
- `get_level`, `get_leaf_nodes`, `walk`, `walk_depth`, `decompose`, `reconstruct`, `__getitem__`, `__setitem__`, or `__delitem__`
- node naming conventions such as `a/d`, `a/h/v/d`, or ND packet path tuples

## Route elsewhere when the task is about

- ordinary decimated transforms, SWT, MRA, or coefficient packing: go to `../discrete-transforms/SKILL.md`
- wavelet catalogs, custom wavelets, or CWT: go to `../wavelets-and-cwt/SKILL.md`

## Start here

- Read `references/api-reference.md` for the verified constructor signatures and packet-tree methods.
- Read `references/workflows.md` for tree traversal, reconstruction, and path-selection examples.
- Read `references/troubleshooting.md` when a path, axis, or reconstruction step fails.
- Run `../../scripts/check_pywavelets_install.py` when you want a quick no-network smoke check that includes packet reconstruction.

## Common workflow anchors

- `WaveletPacket` defaults to `mode='symmetric'` and one transformed axis.
- `WaveletPacket2D` and `WaveletPacketND` default to `mode='smooth'`.
- `WaveletPacket2D` uses `a/h/v/d` naming for the four children of each node.
- `WaveletPacketND` uses path tuples or repeated child tokens for deeper trees.
- `get_level(..., order='freq')` is available on the 1D and 2D packet classes for frequency-style ordering.
- `get_leaf_nodes(decompose=False)` returns the currently existing leaves without forcing deeper decomposition.

## Useful bundled data

- `pywt.data.aero()` and `pywt.data.camera()` are good for 2D packet smoke checks.
- `pywt.data.ecg()` is useful for 1D packet smoke checks.

## What to expect from the references

- `references/api-reference.md` lists the verified packet constructors and node methods.
- `references/workflows.md` shows how to navigate, replace, delete, and reconstruct packet nodes.
- `references/troubleshooting.md` covers invalid paths, axes, and shape-trimming surprises.
