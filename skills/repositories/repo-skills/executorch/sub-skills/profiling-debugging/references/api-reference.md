# DevTools API Reference

## Inspector

Verified constructor shape from inspection:

```text
Inspector(etdump_path=None, etdump_data=None, etrecord=None, source_time_scale=TimeScale.NS, target_time_scale=TimeScale.MS, debug_buffer_path=None, delegate_metadata_parser=None, delegate_time_scale_converter=None, enable_module_hierarchy=False, reference_graph_name='edge_dialect_graph_module')
```

Common use:

```python
from executorch.devtools import Inspector
inspector = Inspector(etrecord="model.etrecord", etdump_path="run.etdp", debug_buffer_path="debug.bin")
inspector.print_data_tabular()
```

## Comparison Helpers

`executorch.devtools.inspector.compare_results` helps compare result structures. For backend-specific numerical debugging, use the owning backend sub-skill if it exposes a comparator or intermediate-output debugger.

## Time Scales

ETDump/Inspector data may use different source and target time scales. Keep units explicit when comparing host vs device runs.

