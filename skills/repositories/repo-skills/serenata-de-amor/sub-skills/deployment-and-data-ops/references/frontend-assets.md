# Frontend and static assets

Jarbas includes a legacy Elm dashboard layer and Django static files. The asset workflow is optional for most data/API operations, but required when rebuilding the dashboard JavaScript bundle or producing production-like static assets.

## Legacy toolchain

| Component | Expected era | Why it matters |
| --- | --- | --- |
| Node.js | Node 8/9-era | The Docker asset image uses a Node 9-era base and dependencies from the same period. Modern Node can break Gulp 3 and Elm 0.18 tooling. |
| Elm | 0.18 | `elm-package.json` constrains Elm to `0.18.0 <= v < 0.19.0`. Elm 0.19 is not compatible with this project without migration work. |
| Gulp | 3.9.x | `gulpfile.js` uses Gulp 3 task syntax (`gulp.task('watch', ['elm'], ...)`). Newer Node versions can fail with old Gulp internals. |
| Django staticfiles | Django 2.1-era | `collectstatic` gathers files into `STATIC_ROOT`; production settings may use WhiteNoise/static storage. |

## Asset commands

Install JS dependencies:

```console
$ npm install
```

The post-install step runs Elm package install. If it does not, run the Elm package install explicitly with the legacy Elm package manager:

```console
$ ./node_modules/.bin/elm-package install --yes
```

Build the minified dashboard bundle:

```console
$ npm run assets
```

Development watch mode:

```console
$ npm run watch
```

Collect Django static assets after the JS bundle is present or when the current static bundle is acceptable:

```console
$ python manage.py collectstatic --no-input
```

Docker asset service:

```console
$ docker compose run --rm elm npm run assets
```

In the development Compose override, the `elm` service can run `npm run watch` and mounts the Jarbas layer directory so changes are reflected during development.

## Inputs and outputs

| Item | Meaning |
| --- | --- |
| Elm entrypoint | `jarbas/layers/elm/Main.elm` |
| Elm source directories | `jarbas/layers/elm` and `jarbas/layers/tests` |
| JS bundle output | `jarbas/layers/static/app.js` |
| Django static root | `staticfiles` directory under the checkout when `collectstatic` runs |

The Gulp task compiles Elm, logs errors without crashing the watch process, uglifies the output, renames it to the dashboard app bundle path, and writes it into the checkout.

## When to skip asset builds

Skip Node/Elm work when the task is only to:

- run `manage.py check`;
- migrate or seed the database;
- exercise management commands;
- validate API/data behavior where existing static files are irrelevant;
- troubleshoot Python/Django/Celery/PostgreSQL issues.

Do not install modern Node/Elm or upgrade frontend packages just to satisfy a Python service task.

## Troubleshooting

### `primordials is not defined` or Gulp crashes on startup

Likely cause: old Gulp 3 with modern Node. Use a Node 8/9-era runtime or the repository's legacy asset container rather than upgrading Gulp as a side effect.

### Elm package/version errors

Likely cause: Elm 0.19+ or missing `elm-package`. Use Elm 0.18 tooling. This codebase has not been migrated to Elm 0.19 module/package conventions.

### `npm install` fails on old packages

Treat the frontend stack as legacy. If the current task does not require regenerating `app.js`, use existing static assets and proceed with Python/Django operations.

### `collectstatic` fails with missing `SECRET_KEY` or database/cache settings

`collectstatic` imports Django settings. Provide safe local settings as in `configuration.md`; for pure static collection, dummy cache is acceptable, but a missing `SECRET_KEY` is not.

### Docker image build fails during `collectstatic`

Diagnose in this order:

1. Python dependency installation and import compatibility.
2. Required environment variables available at build/run time.
3. Static files storage backend.
4. Whether the frontend bundle needs to be regenerated before collection.

Do not patch asset tooling and Python dependencies simultaneously unless the user specifically requests modernization.
