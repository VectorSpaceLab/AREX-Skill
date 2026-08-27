# CLI Troubleshooting

Use this reference for command-line symptoms. Route deeper planning-model issues to `../../network-planning/SKILL.md`, protocol/backend issues to `../../protocols/SKILL.md`, and result interpretation to `../../results-analysis/SKILL.md`.

## Fast Triage

1. Re-run the command with `--help` in the same command position you used.
2. Check phase boundaries: planner commands create transformation JSONs; `quickrun` executes one transformation JSON; gather commands summarize result JSONs.
3. Confirm global options appear before the subcommand.
4. Confirm all paths are unique and point to the expected phase artifacts.
5. Avoid rerunning simulations until cache and output-path state are understood.

## Common Symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No such option: --log` after a subcommand | `--log` is a global option but was placed after the subcommand. | Use `openfe --log logging.conf quickrun transformation.json ...`, not `openfe quickrun --log logging.conf ...`. |
| `openfe quickrun` cannot find the transformation file | Planner output directory is wrong, transformation glob is empty, or the command points at the network JSON instead of an edge JSON. | Look for `output_dir/transformations/*.json`; pass one file from that directory to each quickrun command. |
| Planner output does not contain expected transformation JSONs | Planning failed before output, ligand network has no edges, or the wrong output directory was inspected. | Review planner stdout, verify `-M` input and protein/membrane options, and inspect the output directory layout. Route topology or atom-mapping failures to `../../network-planning/SKILL.md`. |
| Planning fails with malformed YAML or unexpected fields | YAML indentation, top-level section names, method names, or settings are invalid. | Keep only `mapper`, `network`, and `partial_charge` top-level sections; use known method names; validate indentation and scalar quoting. |
| Radial network central ligand selects the wrong ligand | YAML value like `0` was parsed as integer rather than ligand name string. | Quote ligand names that look numeric, for example `central_ligand: '0'`. |
| Planner rejects protein parameters | Both `--protein` and `--protein-membrane` were supplied, no protein context was supplied for RBFE, or file extension is unsupported. | Provide exactly one RBFE protein context; use PDB/PDBx/mmCIF-compatible files; route component-loading problems to `../../network-planning/SKILL.md`. |
| Planner or charge command fails during charge generation | Optional backend missing, unsupported method, bad molecules, existing charges not overwritten, or expensive charge generation timed out. | Start with default `am1bcc`/AmberTools if available, reduce input size for diagnosis, use `--overwrite-charges` only when intended, and route molecule validity to `../../network-planning/SKILL.md`. |
| `charge-molecules` refuses to write output | Output SDF already exists. | Choose a fresh `-o` path; the command intentionally avoids overwriting. |
| `quickrun` rejects `-o` with `is a file` | The chosen result JSON path already exists. | Choose a new output path or move/delete the old result only after confirming it is not needed. |
| `quickrun` says transformation is incomplete and asks for `--resume` | A quickrun cache exists for the same transformation/output path and the previous run did not finish. | If continuing the same job, rerun with the same transformation, `-d`, `-o`, and `--resume`; otherwise remove the named cache file before starting fresh. |
| `quickrun --resume` starts a fresh execution | No matching cache exists for that transformation/output path. | Confirm the original `-d` and `-o` values. If there truly is no cache, decide whether fresh execution is acceptable. |
| `quickrun --resume` reports corrupt cache | Cached `dag-cache-<key>.json` is unreadable, often due to interruption during write. | Remove the named cache file before a fresh run. Do not delete result or work artifacts unless the user confirms they are no longer needed. |
| Parallel repeats overwrite each other | Repeats reused the same `-o` result path or `-d` work directory. | Generate repeat commands with unique `results_<i>/...` and `work_<i>/...` or use the bundled helper's duplicate checks. |
| Gather finds no results | It was pointed at transformation JSONs, an empty work directory, or outputs with non-result JSON content. | Point gather at result JSON files or the root containing result folders, not at `transformations/`. |
| `gather-abfe` or `gather-septop` behavior changes across versions | These gather commands are experimental and under development. | Verify command help in the installed environment and route output schema questions to `../../results-analysis/SKILL.md`. |
| `view-ligand-network` fails in a terminal session | It requires a readable GraphML file and a GUI-capable Matplotlib backend. | Confirm `ligand_network.graphml` exists. In headless environments, avoid the viewer and inspect/convert the GraphML by other means. |
| `openfe test` takes too long | The command runs the OpenFE and OpenFE CLI test suites; `--long` enables much slower tests. | Use import/help checks for a quick sanity pass; run `openfe test` only when requested, and avoid `openfe test --long` unless validating a full installation. |
| `openfe fetch` fails unexpectedly | Resource requires internet, cache is unavailable, or the resource name is wrong. | Use `openfe fetch --help` and the resource subcommand help first; ask before downloading data. |

## Quickrun Cache Decision Tree

- **Cache exists and job should continue:** rerun the exact original command plus `--resume`.
- **Cache exists but the user wants a fresh run:** preserve useful artifacts if needed, then remove only the named `dag-cache-<key>.json` and rerun without `--resume`.
- **Cache missing and `--resume` was used:** quickrun starts fresh; stop if that is not intended.
- **Cache JSON corrupt:** remove the corrupt cache file and start fresh; corruption prevents safe resume.

The cache key uses the transformation identity and absolute output path, so changing `-o` changes the cache identity.

## Repeat Command Safety Checklist

Before submitting or running generated quickrun commands:

- Every transformation argument points to a `transformations/*.json` file.
- Every repeat has a unique `-o` result JSON path.
- Every repeat has a unique `-d` work directory, unless the user intentionally serializes work in a controlled way.
- Parent result/work roots are not shared with unrelated campaigns.
- Planned protocol repeats are understood: for parallel repeats, prefer planning with `--n-protocol-repeats 1` and launching independent quickrun commands.
- Generated Slurm snippets are reviewed and adapted for the user's cluster modules, environment activation, GPU requests, wall time, and account/partition policies.

## Fetch and Network Assumptions

`openfe fetch` is a convenience for tutorials/resources, not a guaranteed offline operation. Some resources may be packaged locally, while others require internet and cache writes. Always inspect `openfe fetch --help` and ask before relying on network access or downloads.
