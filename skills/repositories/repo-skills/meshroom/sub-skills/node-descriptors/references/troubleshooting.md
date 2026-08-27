# Node Descriptor Troubleshooting

- **Descriptor provider is `DESC_ERROR`:** a default value does not match its parameter type, a nested list/group child is malformed, or a validator rejected the descriptor. Run `scripts/validate_node_descriptor.py` against the module and fix the first reported attribute path.
- **`CommandLineNode` command is wrong:** placeholders are based on expanded node variables; inspect `buildCommandLine()` output and quote file paths. Avoid assuming the descriptor name is the same as the instance name.
- **Python node output is empty:** dynamic outputs must be assigned during processing; an output expression is only a path template until the node runs.
- **Output CLI target is rejected:** `OutputNode.setOutputAttribute()` accepts only names in `outputAttributes`; a non-exposed internal input cannot be configured with `--output`.
- **`InputFile` rejects an input:** the supplied path does not exist or the input list is empty. Direct and recursive inputs are separate arguments; validate before calling `initialize()`.
- **Dynamic chunk count is stale:** update the graph after the size-driving list/input changes, then recreate chunks. Test both `size` and `parallelization` behavior.
- **Compound attribute links disappear:** use the child attributes of `ListAttribute`/`GroupAttribute` and save after graph updates. `AnySet` child ordering and links require explicit serialization tests.
- **Scene helper subprocess fails:** check the template path, input/parameter override syntax, target `meshroom_batch` environment, and any external submitter/binary; the helper does not validate AliceVision installation for you.
