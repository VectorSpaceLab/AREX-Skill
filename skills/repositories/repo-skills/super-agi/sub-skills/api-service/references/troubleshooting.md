# API Service Troubleshooting

## Symptoms and Recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| 401 from `/login` or `/validate-access-token` | Bad credentials or missing JWT token. | Confirm the `User` record, JWT secret, and client-provided token. |
| 401/404 from `/v1/agent/...` | Wrong API key, wrong agent/project/org context, or wrong prefix. | Verify the API-key record and make sure you are calling the external API prefix, not the internal CRUD prefix. |
| 404 on an obvious route | The caller used the wrong router prefix, or the route lives under a different controller module. | Check `main.py` prefixes first, then the controller module. |
| DB engine/config import errors | `DB_URL` malformed, `DB_HOST` unreachable, or startup code imports the app without a usable database. | Fix config and ensure the target DB is available before importing the live app. |
| `github-auth` redirect fails | GitHub client id/secret missing or the callback URL is wrong. | Read the auth reference and verify the callback URL and credentials. |
| Provider-key validation fails | The provider key is invalid, placeholder, or network access to the provider is unavailable. | Use a real credential only when the downstream user authorizes a live validation call. |
| Migration/state mismatch | Database schema is not in sync with the controller expectations. | Read the model/migration reference and apply the intended migration path first. |

## Safe Checks

- Use the root route-inspection helper before importing `main.py` if you only
  need endpoint discovery.
- Use `python -m pytest` only on focused controller tests when the environment
  already has the needed FastAPI/SQLAlchemy dependencies.
- Avoid service startup just to prove route mapping; static inspection is enough
  for most route-selection tasks.
