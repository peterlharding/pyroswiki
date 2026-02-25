# Pyroswiki — Server Deployment

Replace `wiki.example.com` throughout with your actual domain.

| Service | External URL | Internal address |
|---------|-------------|------------------|
| Web UI | `https://wiki.example.com` | `127.0.0.1:8221` |
| API | `https://wiki.example.com:8443` | `127.0.0.1:8621` |

---

## 1. Create system user and directory

```bash
sudo useradd -r -s /bin/false -d /opt/pyroswiki pyroswiki
sudo mkdir -p /opt/pyroswiki/data/attachments
sudo chown -R pyroswiki:pyroswiki /opt/pyroswiki
```

## 2. Deploy application code

```bash
sudo -u pyroswiki git clone <repo-url> /opt/pyroswiki
# or rsync from dev machine:
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='.env' \
    ./ pyroswiki@<server>:/opt/pyroswiki/
```

## 3. Create virtual environment and install dependencies

```bash
sudo -u pyroswiki bash -c "
  cd /opt/pyroswiki
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
"
```

## 4. Configure environment

```bash
sudo cp /opt/pyroswiki/deploy/.env.example /opt/pyroswiki/.env
sudo nano /opt/pyroswiki/.env
```

Key values to set:
- `DATABASE_URL` — PostgreSQL connection string with real password
- `SECRET_KEY` — generate with: `python3 -c "import secrets; print(secrets.token_hex(64))"`
- `BASE_URL=https://wiki.example.com:8443`
- `WEB_BASE_URL=https://wiki.example.com`
- `CORS_ORIGINS=["https://wiki.example.com"]`
- `ALLOW_REGISTRATION=true` — leave enabled until the first admin user is created, then set to `false`

```bash
sudo chown pyroswiki:pyroswiki /opt/pyroswiki/.env
sudo chmod 600 /opt/pyroswiki/.env
```

## 5. Run database migrations

```bash
sudo -u pyroswiki bash -c "
  cd /opt/pyroswiki
  PYTHONPATH=. .venv/bin/alembic upgrade head
"
```

## 6. Bootstrap first admin user

User registration is **enabled by default** (`ALLOW_REGISTRATION=true`). This allows the first user to self-register via the web UI.

1. Start the services (step 7 below), then open the web UI and register your admin account.
2. Promote that account to admin via psql:

```bash
psql -h 127.0.0.1 -U pyroswiki -d pyroswiki \
  -c "UPDATE users SET is_admin = TRUE WHERE username = 'your-username';"
```

3. Once your admin account is set up, **disable public registration** so no one else can self-register:

```bash
# In /opt/pyroswiki/.env
ALLOW_REGISTRATION=false
```

Then restart the API service:

```bash
sudo systemctl restart pyroswiki-api
```

> After registration is disabled, only admins can create new user accounts via the **Admin → Users** page in the web UI.

## 7. Install systemd services

```bash
sudo cp /opt/pyroswiki/deploy/pyroswiki-api.service /etc/systemd/system/
sudo cp /opt/pyroswiki/deploy/pyroswiki-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pyroswiki-api pyroswiki-web
sudo systemctl start  pyroswiki-api pyroswiki-web
sudo systemctl status pyroswiki-api pyroswiki-web
```

## 8. Install nginx config

```bash
sudo cp /opt/pyroswiki/deploy/nginx-py-foswiki.conf \
    /etc/nginx/sites-available/wiki.example.com
sudo ln -s /etc/nginx/sites-available/wiki.example.com \
    /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

> **SSL certificates** must already exist. If not, obtain them first:
> ```bash
> sudo certbot --nginx -d wiki.example.com
> ```
> Then update the `server_name` and `ssl_certificate` paths in the nginx config
> to match your domain and certbot certificate paths.

## 9. Open firewall ports

```bash
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
```

Port 80 should already be open for HTTP→HTTPS redirect and certbot renewals.

## Useful commands

```bash
# View logs
sudo journalctl -u pyroswiki-api -f
sudo journalctl -u pyroswiki-web -f

# Restart after code update
sudo systemctl restart pyroswiki-api pyroswiki-web

# Run migrations after update
sudo -u pyroswiki bash -c "cd /opt/pyroswiki && PYTHONPATH=. .venv/bin/alembic upgrade head"
```
