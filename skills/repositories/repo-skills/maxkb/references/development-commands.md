# Development commands

## Backend lifecycle
```bash
python main.py dev
python main.py dev celery
python main.py dev local_model
python main.py start all -d
python main.py start web -w 3
python main.py start task
python main.py stop all
python main.py status
```

## Database and static assets
```bash
python main.py upgrade_db
python main.py collect_static
python apps/manage.py makemigrations <app>
python apps/manage.py migrate
```

## Internationalization
```bash
python apps/manage.py makemessages -l zh_Hant
python apps/manage.py compilemessages
```

## Frontend
```bash
cd ui
npm install
npm run dev
npm run chat
npm run build
npm run build-chat
npm run build-only
npm run build-only-chat
npm run lint
npm run type-check
npm run format
npm run preview
```

## Direct inspection tips
- Use `PYTHONPATH=apps MAXKB_CONFIG_TYPE=ENV` for ad hoc Django/import checks.
- Use `python main.py` entrypoints instead of bypassing the repo bootstrap unless you are doing static inspection.
- If live services are unavailable, document the missing dependency rather than pretending a full run succeeded.
