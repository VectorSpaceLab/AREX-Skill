# BYODB Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `UnsupportedDatabaseError` | the connector type does not match a supported adapter | pick a supported DB family or wrap the connection in the documented shape |
| `Unsupported database dialect` | the adapter could not infer the backend | use a supported connector and verify the connection object's module name |
| Tables are missing after startup | `build()` was not called | run `mem.config.storage.build()` once before the first write |
| SQLite works in tests but not in the app | a different path or connection lifetime is being used | use the same temporary file path and call `close()` when done |
| Provisioning fails for TiDB Zero | missing `pymysql` or service/network access | install the MySQL driver and confirm the provisioning environment |
| Database-specific import fails | the optional extra is not installed | install only the extra for the selected family |
| Long-lived server leaks connections | connection lifetime is tied to a local temporary object | use a factory or pooled session and close it explicitly |

## Recovery steps

1. Identify the database family the user actually has.
2. Install only the driver or extra for that family.
3. Build the schema after creating the Memori instance.
4. If provisioning is involved, confirm the provider, network, and cache
   settings.

## Avoid

- Do not suggest unsupported dialects as if they were verified.
- Do not suggest provisioning routes that the Python package does not expose.
- Do not treat a cloud connection-string workaround as a generic database fix.
