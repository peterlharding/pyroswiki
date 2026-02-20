# 🐳 Docker Desktop Secrets Setup Guide

## Local Development with FastAPI + PostgreSQL

This guide explains how to securely configure **Docker Secrets** in
Docker Desktop for local development --- especially useful for projects
such as:

-   Stock-Control (FastAPI + PostgreSQL)
-   SQL-Explorer
-   Firefox Extension Backend APIs
-   JWT Authenticated Services

Moving passwords and API keys out of `.env` files into Docker Secrets is
an important step toward production‑grade security before eventual
deployment to ECS/Fargate.

------------------------------------------------------------------------

# 🔐 Why Docker Secrets?

Instead of this ❌

``` env
POSTGRES_PASSWORD=supersecret
JWT_SECRET=abc123
```

You do this ✅

    /run/secrets/postgres_password
    /run/secrets/jwt_secret

Secrets are:

-   NOT stored in image layers
-   NOT visible via `docker inspect`
-   NOT exposed as environment variables
-   NOT committed into your Git repository

------------------------------------------------------------------------

# 🚨 Important Docker Desktop Gotcha

Docker Secrets are **Swarm-only**

So even locally you must enable Docker Swarm:

``` bash
docker swarm init
```

You are NOT deploying to a cluster\
You are simply turning on the local secrets manager.

Check status:

``` bash
docker info | grep Swarm
```

Expected output:

    Swarm: active

------------------------------------------------------------------------

# 🪪 1. Create Secret Files

Inside your FastAPI project:

``` bash
mkdir secrets
```

Then create:

``` bash
echo "supersecretpassword" > secrets/postgres_password.txt
echo "verysecretjwtkey" > secrets/jwt_secret.txt
```

⚠️ Never commit this folder

Add to `.gitignore`:

``` gitignore
secrets/*
```

------------------------------------------------------------------------

# 🔐 2. Register Secrets with Docker

``` bash
docker secret create postgres_password secrets/postgres_password.txt
docker secret create jwt_secret secrets/jwt_secret.txt
```

Verify:

``` bash
docker secret ls
```

------------------------------------------------------------------------

# 📦 3. Update docker-compose.yml

``` yaml
version: "3.9"

services:

  db:
    image: postgres:16
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password

  api:
    build: .
    secrets:
      - jwt_secret
      - postgres_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/postgres_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret

secrets:
  postgres_password:
    external: true
  jwt_secret:
    external: true
```

------------------------------------------------------------------------

# 🚀 4. Deploy Using Docker Stack

Secrets DO NOT work with:

``` bash
docker compose up
```

Instead use:

``` bash
docker stack deploy -c docker-compose.yml stockcontrol
```

Check services:

``` bash
docker service ls
```

------------------------------------------------------------------------

# 🧠 5. Read Secrets in FastAPI (Python)

Secrets are mounted as files, not environment variables.

Create helper:

``` python
from pathlib import Path

def get_secret(name: str) -> str:
    return Path(f"/run/secrets/{name}").read_text().strip()
```

Use in your app:

``` python
DB_PASSWORD = get_secret("postgres_password")
JWT_SECRET  = get_secret("jwt_secret")
```

Ideal for:

-   JWT Authentication
-   PostgreSQL Connection Strings
-   MongoDB Credentials
-   API Keys

------------------------------------------------------------------------

# 🧹 6. Updating Secrets

Docker Secrets are immutable.

To update:

``` bash
docker secret rm jwt_secret
docker secret create jwt_secret secrets/jwt_secret.txt
docker stack deploy -c docker-compose.yml stockcontrol
```

------------------------------------------------------------------------

# 🧭 Production Compatibility

Later mapping:

  Docker Secrets    AWS Equivalent
  ----------------- ---------------------
  /run/secrets/\*   AWS Secrets Manager
  /run/secrets/\*   SSM Parameter Store

Because your FastAPI app already reads:

    /run/secrets/*

Your application code does not need to change when moving to
ECS/Fargate.

------------------------------------------------------------------------

# ✅ Next Steps (Optional)

-   Auto‑fallback to `.env` in development
-   Inject secrets into SQLAlchemy URL cleanly
-   Integrate with Pydantic Settings v2

------------------------------------------------------------------------

**End of Guide**
