# Wavelet Packet API Reference

## When to read

Read this when you need the verified packet constructors, level-navigation methods, or node semantics for 1D, 2D, and ND packet trees.

## Constructors

- `WaveletPacket(data, wavelet, mode='symmetric', maxlevel=None, axis=-1)`
- `WaveletPacket2D(data, wavelet, mode='smooth', maxlevel=None, axes=(-2, -1))`
- `WaveletPacketND(data, wavelet, mode='smooth', maxlevel=None, axes=None)`

## Shared node classes

- `BaseNode`
- `Node`
- `Node2D`
- `NodeND`

Common node attributes and methods:

- `data`, `parent`, `wavelet`, `axes`, `mode`, `level`, `path`, `path_tuple`, `node_name`, `maxlevel`
- `is_empty`, `has_any_subnode`
- `decompose()`, `reconstruct(update=False)`
- `get_subnode(part, decompose=True)`
- `__getitem__(path)`, `__setitem__(path, data)`, `__delitem__(path)`
- `get_leaf_nodes(decompose=False)`
- `walk(func, ...)`, `walk_depth(func, ...)`

## Level helpers

- `WaveletPacket.get_level(level, order='natural', decompose=True)`
- `WaveletPacket2D.get_level(level, order='natural', decompose=True)`
- `WaveletPacketND.get_level(level, decompose=True)`

`WaveletPacket` and `WaveletPacket2D` also support frequency ordering via `order='freq'`.

## Node naming conventions

- 1D packet children use `a` and `d`.
- 2D packet children use `a`, `h`, `v`, and `d`.
- ND packet paths are built from repeated child tokens across the transformed axes.
- Tuple paths are accepted in `__getitem__` for all packet classes.

## Reconstructing data

- `reconstruct(update=False)` returns the current node data when no children exist.
- When children do exist, `reconstruct` returns the inverse packet reconstruction and trims any excess shape to the original data size if needed.
- `update=True` replaces the node's stored data with the reconstructed value.

## Live behavior reminders

- `WaveletPacket` defaults to `mode='symmetric'`.
- `WaveletPacket2D` and `WaveletPacketND` default to `mode='smooth'`.
- `WaveletPacketND` uses the same packet-tree semantics even when only a subset of axes is transformed.
