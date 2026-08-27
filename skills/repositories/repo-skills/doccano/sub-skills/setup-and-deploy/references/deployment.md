# Deployment notes

doccano is usually deployed one of three ways.

## Docker image

- Build or pull the published image and run it with the documented admin bootstrap variables.
- Container runtime helpers in `tools/` perform static-file collection, database initialization, role creation, admin creation, and process supervision for Django and Celery.
- Use the helper scripts as deployment wrappers, not as the only source of truth for runtime behavior.

## Docker Compose

- The production compose file lives at `docker/docker-compose.prod.yml`.
- The example environment file is `docker/.env.example`.
- The compose deployment expects explicit admin credentials and database/broker settings.
- If you change the exposed frontend port, update `CSRF_TRUSTED_ORIGINS` to match the new origin.

## AWS and Heroku

- `cloud/aws/template.aws.yaml` provisions an EC2-based deployment.
- The Heroku helper exists for bootstrap behavior in the container image path.
- These deployment flows still rely on the same core CLI and environment variables as local installs.
