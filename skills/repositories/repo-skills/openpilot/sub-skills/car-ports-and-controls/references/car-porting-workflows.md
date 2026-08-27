# Car Porting Workflows

## Evidence and utilities

Car porting in openpilot is strongly tied to opendbc platform definitions, DBC signal correctness, firmware fingerprints, route logs, and interface/controller tests.

Useful target-checkout utilities and their roles:

| Utility/test | Use | Safety |
| --- | --- | --- |
| `tools/car_porting/auto_fingerprint.py <route> [platform]` | Format FW versions from a route for a platform | Reads route logs; may require network/auth |
| `tools/scripts/fingerprint_from_route.py <route>` | Print CAN fingerprint, FW versions, and VIN from qlogs | Reads route logs |
| `tools/car_porting/test_car_model.py <route> --car <platform>` | Run opendbc route model tests for a port | Reads route logs and runs tests |
| `tools/test_runner.py openpilot/selfdrive/car/tests/test_car_interfaces.py -k <brand>` | Fuzz/update/apply car interfaces for selected platforms | CPU-safe but broad; narrow with `-k` |
| `tools/test_runner.py openpilot/selfdrive/car/tests/test_docs.py` | Validate supported cars docs generation | CPU-safe |

## Port triage sequence

1. Confirm the vehicle appears in supported-cars or opendbc platform lists.
2. Use Cabana/route logs to inspect CAN signals and DBC interpretation if the task is signal-level.
3. Extract CAN/FW/VIN summary from a known route; prefer qlogs for speed.
4. Resolve platform names and migration aliases before editing car values.
5. Run focused car interface tests for the brand/platform.
6. If route validation is needed, run `test_car_model.py` on a representative route or segment.
7. Update docs generation only after interface/platform data is coherent.

## Supported cars docs

`openpilot/selfdrive/car/docs.py` builds the openpilot `CARS.md` table from opendbc car docs. Use docs tests when platform docs, footnotes, or support flags change. Treat generated docs writes as repo-maintenance work; do not run writers in unrelated analysis tasks.

## Fingerprint outputs

A useful fingerprint summary records:

- CAN addresses and data lengths from bus 0/stock messages.
- Firmware ECU/address/subAddress tuples and versions.
- VIN if present in `carParams`.
- Platform chosen by explicit argument, existing `carFingerprint`, or fuzzy FW match.

Ambiguous FW matches should stop the porting workflow until platform evidence improves.
