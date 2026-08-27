# Wavelet Packet Workflows

## When to read

Read this when you need a practical recipe for navigating, editing, or reconstructing packet trees.

## 1D packet workflow

1. Construct `WaveletPacket(data, wavelet, mode)`.
2. Read nodes with string paths such as `wp['a']`, `wp['ad']`, or `wp['aaa']`.
3. Use `get_level(level, order='natural')` to collect nodes on one depth.
4. Use `get_level(level, order='freq')` when you want frequency-style ordering.
5. Assign to subnodes with `wp['aa'] = some_array` or delete them with `del wp['ad']`.
6. Call `reconstruct(update=False)` to verify the result before mutating the stored data.

Example:

```python
import pywt

x = [1, 2, 3, 4, 5, 6, 7, 8]
wp = pywt.WaveletPacket(x, 'db1', 'symmetric')
leaf_paths = [node.path for node in wp.get_level(3)]
rec = wp.reconstruct()
```

## 2D packet workflow

- Use `WaveletPacket2D` for image-style packet trees.
- The child names are `a`, `h`, `v`, and `d`.
- Use `get_level(level, order='freq')` to inspect the four-way tree in a frequency-friendly order.
- `expand_2d_path` is useful when you want to print the row/column interpretation of a node path.

Example:

```python
import pywt
import pywt.data

img = pywt.data.camera()
wp2 = pywt.WaveletPacket2D(img, 'db1', 'symmetric')
node = wp2['av']
```

## ND packet workflow

- Use `WaveletPacketND` when the packet tree needs to span arbitrary axes.
- You can address nodes with tuples such as `('aa', 'ad')` or by repeated path segments.
- Use `get_level(level)` to collect all packet nodes on one depth.
- Use `get_leaf_nodes(decompose=False)` when you only want the currently existing leaves.

## Tree editing

- Assigning `wp['path'] = array` replaces the node data.
- Assigning another node object to a path is also supported for convenience.
- Deleting a node with `del wp['path']` removes that branch from the tree.

## Reconstruction tips

- Packet reconstruction may trim to the original input shape when the path's transformed axis length is odd.
- For subnodes, reconstructing that node alone returns the local shape rather than the whole-tree shape.
- If a tree looks unexpectedly shallow, check `maxlevel` before forcing deeper decomposition.

## Smoke fixtures

- `pywt.data.ecg()` works well for a 1D packet tree.
- `pywt.data.camera()` and `pywt.data.aero()` work well for 2D packet trees.
- A small `np.ones((4, 4, 4))` cube is enough for an ND path/reconstruction smoke check.
