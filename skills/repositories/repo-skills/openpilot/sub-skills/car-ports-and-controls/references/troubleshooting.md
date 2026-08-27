# Car Porting and Controls Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` or missing signal in car interface tests | DBC signal name, fingerprint, or platform mapping is wrong | Use route-based fingerprint extraction, inspect DBC mappings, and rerun focused brand tests. |
| FW match is ambiguous | More than one platform fits the observed firmware set | Do not guess; collect better route evidence or a better local test route. |
| panda safety mismatch | CarState and panda safety model disagree | Treat as a safety regression; investigate before modifying behavior. |
| `test_car_model.py` fails on a route | The route lacks required signals, safety assumptions, or the selected platform is wrong | Pick a more representative route or narrow the brand/platform. |
| process replay cannot find logs | Route not uploaded, cache missing, or network/auth unavailable | Prefer a local route or a smaller `LogReader`-based test first. |
| process replay changes too much | Whitelist/blacklist too broad, or reference logs are stale | Narrow the process set, compare one process at a time, and only update references intentionally. |
| maneuver report is empty | Route lacks maneuver alerts or the wrong route ID/description was used | Confirm the route actually contains maneuver alerts and that the route ID matches the report expectations. |
| live Params write or device mode change is requested | Safety-sensitive operation | Require explicit user approval and explain the offroad/device-state prerequisites. |
