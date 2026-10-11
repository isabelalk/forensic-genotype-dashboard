# Verification

Run every command from the repository root unless stated otherwise.

## Backend Tests

Requires the backend virtualenv at `backend/venv` (see [quickstart](quickstart.md)).

```bash
pnpm --filter backend run test
```

## Dependency Audit

Checks the hash-locked `backend/requirements.txt` against known vulnerabilities. Needs network access.

```bash
pnpm --filter backend run audit
```

To regenerate the lock first, run `pnpm --filter backend run lock`.

## Frontend Checks

```bash
pnpm lint
pnpm type-check
pnpm --filter frontend build
```

From `frontend/`, the local frontend checks are:

```bash
pnpm lint
pnpm type-check
pnpm build
```

## Docker Config Check

Run when Docker is available. The secret is required; without it compose exits non-zero and names `BACKEND_SHARED_SECRET`.

```bash
BACKEND_SHARED_SECRET=x docker compose config
```

The output must show exactly one published port: `8080` with `host_ip: 127.0.0.1` on `frontend`, and no `ports` on `backend`.

## Container Checklist

Run after `BACKEND_SHARED_SECRET=test docker compose up -d --build` and use the host's `curl`.

- [ ] `docker compose ps` shows both services `healthy`.
- [ ] `docker inspect --format '{{.HostConfig.Memory}} {{.HostConfig.MemorySwap}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}} {{.HostConfig.ReadonlyRootfs}}' $(docker compose ps -q backend)` prints `2147483648 2147483648 2000000000 256 true`.
- [ ] `docker compose exec backend id -u` prints `10001`.
- [ ] `docker compose exec backend sh -c 'touch /app/x'` fails with a read-only filesystem error.
- [ ] `docker compose exec backend sh -c 'touch /data/x /tmp/x && rm /data/x /tmp/x'` succeeds.
- [ ] `docker compose exec backend which gcc` finds nothing.
- [ ] `curl -s -o /dev/null -w '%{http_code}' localhost:8000/health` fails to connect (backend not published).
- [ ] `curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/api/vcf/markers/plex34` prints `200`.
- [ ] `curl -s -o /dev/null -w '%{http_code}\n' -H 'X-Internal-Token: nope' localhost:8080/api/vcf/markers/plex34` still prints `200` (the proxy overwrites the header).
- [ ] `curl -sI localhost:8080/` shows `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Content-Security-Policy` and `Server: nginx` without a version.
- [ ] `curl -s -o /dev/null -w '%{http_code}\n' -X POST --data-binary @<2 MB file> localhost:8080/` prints `413`.
- [ ] 20 quick `POST`s to `localhost:8080/api/vcf/upload` from one IP include at least one `429`.
- [ ] `curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/docs` prints `404` (same for `/redoc` and `/openapi.json`; Nginx refuses them, and the backend hides them with `APP_ENV=production`).

## Manual Runtime Check

1. Start the backend and frontend (`./start-dev.sh`), or the Docker stack.
2. Open `http://localhost:5173` (local) or `http://127.0.0.1:8080` (Docker).
3. Upload a `.vcf` or `.vcf.gz` file.
4. Validate it.
5. Generate at least one CSV output and a PLEX-34 STRUCTURE package.
6. Upload a HIrisPlex-S result CSV and one STRUCTURE `.txt` or `.out` output file if test fixtures are available.

The app should show validation feedback, downloadable artifacts, and independent HIrisPlex-S and PLEX-34 summaries. The browser console should show no Content-Security-Policy violations when using the Docker stack.
