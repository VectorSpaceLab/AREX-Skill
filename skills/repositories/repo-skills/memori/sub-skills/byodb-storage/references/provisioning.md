# Provisioning

## Public Python entry point

```python
Memori.provision(*, provider, build=True, cache=True, tag="memori", cache_key=None, **kwargs)
```

## Current packaged provisioning route

The Python provisioning path currently routes through the TiDB Zero provider.
That route:

- requires the MySQL driver family,
- caches provision results by provider and tag unless caching is disabled, and
- returns a ready `Memori` instance when provisioning succeeds.

## Important behavior

- `build=True` runs the schema build automatically after the provisioned DSN is
  attached.
- `cache=False` forces a fresh provisioning result.
- `tag` and `cache_key` control the cache namespace for repeated runs.
- `Memori.provision(...)` stores the returned provision result on the instance
  so later inspection can report how the database was created.

## When to use

Use this reference when the user wants a disposable development database or a
TiDB Zero setup and needs to know what gets created, cached, or built for them.

## When to stop

If the MySQL driver is missing or the environment cannot reach the provisioned
service, explain the stop condition rather than pretending the provision
succeeded.
