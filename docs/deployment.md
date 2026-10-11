# Deployment

This describes the Docker deployment behind Caddy on a single Linux host. Only the frontend container is published, and only on `127.0.0.1`. Caddy is the public entry point.

```text
Internet -> Caddy (host, 443) -> 127.0.0.1:8080 -> frontend (Nginx) -> backend:8000 (compose network only)
```

## Prerequisites

- Linux host with Docker and the Docker Compose plugin (`docker compose version`).
- Caddy 2 running on the host (not in this compose file).
- `openssl` to generate the shared secret.
- A domain that points at the host.

## Configure `.env`

Create `.env` next to `docker-compose.yml`. Compose reads it automatically. `.env` is git-ignored; never commit it.

```bash
cat > .env <<EOF
BACKEND_SHARED_SECRET=$(openssl rand -hex 32)
CORS_ORIGINS=https://example.org
EOF
chmod 600 .env
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `BACKEND_SHARED_SECRET` | yes | none | Secret that Nginx sends to the backend as `X-Internal-Token`. The backend rejects every `/api/` request without it (`403`). Compose refuses to start without it. Use hex or base64url characters only (what `openssl rand -hex 32` produces); quotes, `$` and spaces would break the rendered Nginx config. |
| `CORS_ORIGINS` | recommended | `http://127.0.0.1:8080` | Comma-separated origins the backend accepts. Set it to `https://<domain>`. |
| `FRONTEND_PORT` | no | `8080` | Host port the frontend binds on `127.0.0.1`. Change the Caddy upstream to match. |
| `TRUSTED_PROXY_CIDR` | no | `172.16.0.0/12` | Address range of the reverse proxy. Nginx trusts `X-Forwarded-For` only from this range. |

### `TRUSTED_PROXY_CIDR`

Nginx rate-limits per client IP. Behind Caddy, every connection comes from Caddy, so Nginx must read the real client IP from `X-Forwarded-For`. It does that only for connections from `TRUSTED_PROXY_CIDR`; from any other address it ignores the header (so clients cannot spoof their IP).

Caddy on the host reaches a published port through the Docker bridge, so the connection normally arrives from the bridge gateway (for example `172.18.0.1`). The default `172.16.0.0/12` covers all default Docker bridge networks.

To check what Nginx sees, load the site through Caddy once, then:

```bash
docker compose logs frontend | tail
```

The first field of each access-log line is the client address Nginx used. If it shows a Docker address such as `172.x.x.x` for every visitor, Caddy's address is not in the trusted range, or Caddy does not send `X-Forwarded-For`. If it shows real visitor IPs, the setting works. If Caddy connects from a different range, set `TRUSTED_PROXY_CIDR` to that range (for example `192.168.0.0/16`) in `.env`.

## Caddy

Add a block to your Caddyfile. Caddy sets `X-Forwarded-For` on proxied requests by default.

```caddyfile
example.org {
    reverse_proxy 127.0.0.1:8080
}
```

Reload Caddy afterwards (`sudo systemctl reload caddy` or `caddy reload --config /etc/caddy/Caddyfile`).

## Update dependency locks before each deploy

Run these from the repository root with the backend virtualenv created (see [quickstart](quickstart.md)):

```bash
pnpm --filter backend run lock    # regenerate backend/requirements.txt with hashes
pnpm --filter backend run audit   # fail if the locked set has a known vulnerability
```

Commit the updated `backend/requirements.txt` before building. The image installs from it with `pip install --require-hashes`, so a changed or missing hash fails the build.

## Build and start

```bash
docker compose config                # must succeed and show one port: 127.0.0.1:8080 on frontend
docker compose up -d --build
docker compose ps                    # wait until both services show "healthy"
```

`docker compose config` exits non-zero and names `BACKEND_SHARED_SECRET` if `.env` lacks it. The frontend starts only after the backend is healthy, so `docker compose ps` can show the frontend as `Created` or `Starting` for up to about 45 seconds.

Check the result:

```bash
curl -sI http://127.0.0.1:8080/ | head -n 12      # 200, security headers, "Server: nginx" without a version
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/api/vcf/markers/plex34   # 200
```

## Size-limited storage for `app-data`

The `app-data` volume holds uploads and generated artifacts (`/data/uploads`, `/data/artifacts`). The app enforces its own quotas (1 GiB uploads, 512 MiB artifacts), but container memory limits do not cap disk. Put the volume on a filesystem with a hard ceiling so a bug cannot fill the host disk.

Example: a 5 GiB ext4 image, loop-mounted at `/srv/fgd-data`:

```bash
sudo truncate -s 5G /srv/fgd-data.img
sudo mkfs.ext4 -F /srv/fgd-data.img
sudo mkdir -p /srv/fgd-data
sudo mount -o loop /srv/fgd-data.img /srv/fgd-data
echo '/srv/fgd-data.img /srv/fgd-data ext4 loop,nofail 0 0' | sudo tee -a /etc/fstab
sudo mkdir -p /srv/fgd-data/uploads /srv/fgd-data/artifacts
sudo chown -R 10001:10001 /srv/fgd-data
```

UID/GID `10001` is the backend container user.

Then bind the compose volume to that path with a `docker-compose.override.yml` next to `docker-compose.yml` (Compose merges it automatically; do not commit host-specific paths to the tracked file):

```yaml
volumes:
  app-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /srv/fgd-data
```

If the `app-data` volume already exists, remove it first so the new options apply (uploads are disposable):

```bash
docker compose down
docker volume rm "$(basename "$PWD")_app-data"
docker compose up -d --build
```

Verify the backend writes into the limited filesystem:

```bash
docker compose exec backend sh -c 'touch /data/uploads/probe && rm /data/uploads/probe && echo ok'
df -h /srv/fgd-data
```

## What is not exposed

- The backend port (8000): no `ports:` entry. Only the frontend container reaches it, over the compose network, and the backend still requires `X-Internal-Token`.
- `/docs`, `/redoc`, `/openapi.json`: the backend runs with `APP_ENV=production`, so these return `404`.
- Any host interface other than loopback: the frontend binds `127.0.0.1` only; Caddy is the only public listener.

## Rollback

Uploads and artifacts are disposable and there is no data migration.

```bash
docker compose down
git checkout <previous-commit>
docker compose up -d --build
```

The `app-data` volume can be deleted at any time (`docker compose down -v`).
