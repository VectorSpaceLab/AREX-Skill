# Binary Size Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Size diff is dominated by debug info | Compared unstripped binaries | Strip both before and after or use section analysis. |
| `bloaty -d compileunits` unhelpful | Release build lacks debug info | Use symbols/sections or rebuild a diagnostic binary with debug info, separate from deployable size. |
| Size change disappears after clean build | Incremental artifact mismatch | Clean/reconfigure and rebuild both baseline and candidate with identical flags. |
| Runtime operators missing after size reduction | Registration/object files pruned too aggressively | Restore required force-load/whole-archive behavior and run runtime tests. |
| Latency regresses | Size optimization changed hot-path code | Benchmark representative workloads before accepting the change. |

