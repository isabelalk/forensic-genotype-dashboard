# Security review before VPS deployment

Reviewed revision: `56edcd2` on `main` (same as `origin/main`, clean tree). Review date: 2026-10-11.

## Verdict: block public deployment

Do not put this app on a public domain in its current form. Anyone on the internet could use every endpoint with no login. They could fill the VPS disk, tie up the backend, and download genetic data for any file ID they get hold of. The fixes are not large, but several of them must land before deployment. The "Must fix before deploy" list at the end gives the order.

## How this review was done

- Three reviewers read the whole backend, frontend, Docker, Nginx and dependency setup, each from a different angle: request paths and resource use; access and data handling; containers and dependencies.
- Two independent testers were assigned to re-check every finding. Neither delivered a result, so I ran the tests myself. Every finding marked "tested" below was checked once, by me, not twice.
- Tests ran the real backend modules in an isolated sandbox, using only small synthetic files:
  - no network
  - read-only source
  - unprivileged user
  - 512 MiB memory, 10 CPU seconds, 4 MiB maximum file size, 20 s wall time
- No real genetic data, running services, Docker daemon, firewall or Caddy config was touched.
- The installed Python has no FastAPI, pandas or cyvcf2, so no full HTTP request was sent. Findings that depend on those libraries are marked "from source" or "needs validation".
- Dependency advisories were checked against the OSV database and the FastAPI 0.115.6 metadata on PyPI.

Status labels used below:

- **Tested:** reproduced with a sandbox check.
- **From source:** proven by reading the code or config, not executed.
- **Needs validation:** depends on a library or host fact this review could not observe.

## Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | High (public deploy) | No authentication or ownership on any endpoint | From source |
| 2 | High | Uploads are kept forever with no total size limit | From source |
| 3 | High | Starlette and python-multipart versions have published denial-of-service flaws, one reachable without login | Advisory ranges confirmed |
| 4 | Medium | STRUCTURE input generation multiplies disk use 70 to 2,000 times | Tested |
| 5 | Medium | Results parsers turn a small upload into a large amount of RAM, and one has no size limit | Tested |
| 6 | Medium | All heavy work runs on the single event loop, so one slow request stalls the whole API | From source |
| 7 | Medium | Docker publishes backend port 8000 and frontend port 80 on all interfaces | From source |
| 8 | Medium | Rebuilding the backend image copies stored genetic files into the image | From source |
| 9 | Medium | Gzip data uploaded as `.vcf` skips the decompressed-size check | Partly tested |
| 10 | Low | Artifact cleanup can delete another user's recent artifact | Tested |
| 11 | Low | Exported CSVs keep spreadsheet formulas from sample names | From source |
| 12 | Low | Raw exception text is returned to the client | Partly tested |
| 13 | Low | HIrisPlex-S parser crashes with a 500 on a long field | Tested |
| 14 | Info | Frontend says "Max. 200MB"; the real limit is 100 MiB | From source |
| 15 | Hardening | Containers run as root with no resource limits | From source |

### 1. No authentication or ownership on any endpoint

`backend/app/main.py:14` adds only CORS. No route has an auth dependency. Uploads and artifacts are found by ID alone:

- `services/upload_lookup.py:5`: `UUID()` check, then `exists()`
- `api/routes/plex34_structure.py:32`: 32-hex regex, then `exists()`

No owner is stored with a file.

On a public domain, this has two effects:

- Anyone can call every processing endpoint. That turns findings 2 to 6 from local concerns into internet-facing ones.
- Anyone who has a file ID can download that file's per-sample genotypes indefinitely:
  - `GET /api/vcf/download-full/{id}`
  - `POST /api/vcf/convert`
  - `POST /api/vcf/validate`

The IDs are random UUIDs and cannot be guessed or listed. They do leak, though. They appear in GET URLs (`frontend/src/api/client.ts:61,78,117` opens them with `window.open`), in Nginx and Uvicorn access logs, and in browser history. Forensic DNA data is special-category personal data, so this matters more than it would for ordinary files.

CWE-306, CWE-862, CWE-598.

Fix:

- Put a login in front of the whole site. For a small team, Caddy `basic_auth` on the domain is the quickest option and needs no code change. Application login with per-user ownership is the long-term fix.
- Store an owner with each upload and artifact, and check it in `find_uploaded_vcf` and `_artifact_zip_path`.

Regression check: requests without credentials get 401, and user B asking for user A's file gets 404.

### 2. Uploads are kept forever with no total size limit

`api/routes/vcf.py:35-52` saves each upload as `uploads/<uuid>.vcf(.gz)`. The only deletions are on error paths at `vcf.py:56`, `:63` and `:67`. A search of `backend/app` finds no other `unlink` or `rmtree` on uploads. Each file is capped at 100 MiB (`core/config.py:19`), but nothing caps their number, total size or age. A plain `.vcf` upload is not checked for content.

`docker-compose.yml:9` stores uploads on the host disk under `./backend/app/uploads`. That disk has about 325 GB free, so about 3,300 requests of 100 MiB would fill it. Other apps on the VPS share the same disk. `docs/architecture.md` describes uploads as temporary, which the code does not match.

CWE-770, CWE-459.

Fix:

- Delete uploads after a TTL (24 hours is enough for this workflow).
- Enforce a total quota, for example 2 GiB, and reject new uploads with 507 when it is full.
- Add a delete endpoint the frontend calls when the user is done.
- Put uploads on a filesystem with a hard size limit (see the limits section), so a bug in the quota code still cannot fill the host disk.

Regression check: upload past the quota and get 507; age a file past the TTL and confirm the sweep removes it.

### 3. Dependency versions with published denial-of-service flaws

`backend/requirements.txt` pins `fastapi==0.115.6` and `python-multipart==0.0.20`. FastAPI 0.115.6 requires `starlette>=0.40.0,<0.42.0` (PyPI metadata). Every Starlette version in that range is inside the affected range of these advisories (OSV):

| Advisory | Package | Affected | Fixed | Reachable here |
|---|---|---|---|---|
| GHSA-7f5h-v6xp-fcq8 (CVE-2025-62727), CPU exhaustion from a crafted `Range` header on `FileResponse` | starlette | 0.39.0 to 0.49.0 | 0.49.1 | Yes. `plex34_structure.py:77` returns `FileResponse`. Anyone can create their own artifact, then send the header. |
| GHSA-2c2j-9gv5-cj73 (CVE-2025-54121), event loop blocks when a large upload rolls over to disk | starlette | below 0.47.2 | 0.47.2 | Yes, on all three upload routes |
| GHSA-82w8-qh3p-5jfq, form limits ignored for urlencoded bodies | starlette | 0.4.1 to below 1.3.1 | 1.3.1 | Likely. Routes with `File(...)` parse the form according to the client's Content-Type. Needs a runtime check. |
| GHSA-pp6c-gr5w-3c5g, GHSA-mj87-hwqh-73pj, GHSA-5rvq-cxj2-64vf, GHSA-v9pg-7xvm-68hf | python-multipart | all versions up to 0.0.26 to 0.0.31 | 0.0.31 covers all four | Multipart parsing is reached by every upload route. Each one's exact path was not run. |

These were not reproduced, because the libraries are not installed here. The version ranges are confirmed.

Fix:

- Upgrade FastAPI to a release whose Starlette range allows 1.3.1 or later.
- Pin `python-multipart>=0.0.31`.
- Generate a lock file (`pip-compile --generate-hashes` or `uv lock`) so every build installs the same versions.
- Run `pip-audit` against the lock file in CI and before each deploy.

### 4. STRUCTURE input generation multiplies disk use

`services/_plex34_structure_io.py` works as follows:

- `:100` takes every name in the `#CHROM` header as a sample, with no count limit, and repeated names are allowed.
- `:118-126` writes one row per sample with two codes per matched marker, filling `-9 -9` when a genotype is missing.
- `services/plex34_structure.py:57-99` writes that file plus a zip copy, with no byte limit.

Sandbox test, using the real 34-marker PLEX-34 list, single-letter sample names repeated, and one line per marker with no genotype columns:

| Samples | VCF bytes | Gzip bytes | STRUCTURE input bytes | Output vs VCF | Output vs gzip |
|---|---|---|---|---|---|
| 1,000 | 3,006 | 371 | 210,000 | 70x | 566x |
| 4,000 | 9,006 | 390 | 840,000 | 93x | 2,154x |

The ratio grows with sample count. A 20,000-sample run hit the sandbox's 4 MiB file limit. At 93x, a 100 MiB plain `.vcf` of this shape asks the server to write about 9 GB for one request, and a `.vcf.gz` gets there from a far smaller upload. Up to 25 artifacts are kept for 24 hours (`core/config.py:21-22`), and the age and count cleanup runs only when a new artifact is generated. If the write fails partway, the partial directory stays behind.

CWE-409, CWE-770.

Fix:

- Reject VCFs with more than a set number of samples (5,000 is far above any real casework file).
- Reject duplicate or whitespace-containing sample names.
- Stop writing once the output passes a byte limit (50 MiB), and delete the partial directory on any failure.
- Give the artifact directory a total byte quota.

Regression check: a VCF with 5,001 header samples is rejected with 400 before anything is written.

### 5. Results parsers turn a small upload into a large amount of RAM

Measured with Python's `tracemalloc`. The model classes were replaced by plain objects because Pydantic is not installed. Real Pydantic models use more memory, so these are lower bounds.

| Parser | Input | Peak Python memory | Ratio |
|---|---|---|---|
| HIrisPlex-S results, 10,000 rows | 180 KB | 13.9 MB | 77x |
| HIrisPlex-S results, 20,000 rows | 360 KB | 27.8 MB | 77x |
| STRUCTURE output, 100,000 probabilities on one line | 200 KB | 33.0 MB | 165x |
| STRUCTURE output, 200,000 probabilities on one line | 400 KB | 66.1 MB | 165x |

`api/routes/hirisplex_results.py:13` reads the whole upload with `await file.read()`, with no size or row limit. The only ceiling is Nginx's 100 MB body limit, and on port 8000 there is none (finding 7). At 77x or more, a 100 MB file needs at least 7.7 GB of RAM, and FastAPI then builds a JSON response of similar size.

The STRUCTURE output route caps uploads at 5 MiB (`plex34_structure.py:20`). At 165x that is still about 860 MB per request, and a few concurrent requests add up.

CWE-770.

Fix:

- HIrisPlex-S: read in chunks with a 5 MiB cap, like the STRUCTURE route, and reject more than 10,000 rows.
- STRUCTURE output: reject more than 64 clusters per line and more than 10,000 sample lines.

Regression check: a 10,001-row results CSV and a 65-cluster STRUCTURE line both return 400.

### 6. Heavy work blocks the whole API

Every route is `async def`, but the work inside is synchronous:

- file writes and gzip expansion (`upload_storage.py`)
- cyvcf2 parsing (`vcf.py:92-111` makes five full passes over the file for one validate call)
- pandas building and `to_csv` (`vcf.py:157`, `:199`, `:247`)
- STRUCTURE file writing

`backend/Dockerfile:31` runs a single Uvicorn process. While one of these requests runs, the server cannot answer anything else, including `/health`.

`services/vcf_processor.py:60-106` also collects every variant and every genotype before `vcf.py:120` keeps only the first 100. `get_full_vcf_dataframe` (`:193-232`) builds the whole file as a DataFrame on every download. No request is limited in time or memory.

This was not timed, because cyvcf2 and pandas are not installed.

CWE-770.

Fix:

- Make the handlers plain `def`, so FastAPI runs them in its thread pool, or send the heavy work to a small process pool (2 workers) with a per-job timeout that actually stops the work.
- Stop collecting after the first 100 variants in validate.
- Limit samples times variants, as described in the limits section.

Regression check: while a slow validate runs, `/health` still answers within 1 second.

### 7. Ports published on all interfaces

`docker-compose.yml:7` publishes backend `8000:8000` and `:28` publishes frontend `80:80`, both on all interfaces.

- Port 8000 skips Nginx entirely, along with its 100 MB body limit and any rate limits you add later. FastAPI's `/docs` and `/openapi.json` are also served there.
- Port 80 is the port Caddy uses on this VPS, so this compose file conflicts with Caddy as written.
- Docker adds its own iptables rules for published ports. The host's ufw rules (80/443 only) do not block them by default. The actual firewall state was not checked.

Fix: for the deployment, publish only the frontend, as `127.0.0.1:<port>:80`, and remove the backend `ports:` entry. Nginx already reaches the backend over the compose network. The `deploy-vps` workflow does this in an untracked `compose.deploy.yml` override, so the tracked file can stay as it is for local development. Also disable `/docs`, `/redoc` and `/openapi.json` in production.

`start-backend.sh` runs `uvicorn --reload --host 0.0.0.0`. Never use it on the VPS.

### 8. Rebuilding the backend image copies stored genetic files into it

`backend/Dockerfile:23` runs `COPY ./app ./app`. The uploads and artifacts that `docker-compose.yml:9-10` bind-mounts live inside `./backend/app`. There is no `.dockerignore` anywhere in the repo. `.gitignore` keeps those folders out of git but not out of the Docker build context.

Every redeploy rebuilds on the same host. Each rebuild therefore writes every stored upload into a new image layer, where it stays even after the files are deleted from disk. At runtime the bind mount hides the copy, but it remains in:

- the image
- the build cache
- any `docker save` output or registry push

This was not built, because no image build was allowed during the review.

CWE-538.

Fix: add `backend/.dockerignore` excluding `app/uploads`, `app/artifacts`, `venv*`, `.env*` and `__pycache__`. Better, move runtime data out of the source tree into a named volume such as `/data`.

### 9. Gzip data uploaded as `.vcf` skips the decompressed-size check

`services/upload_storage.py:29` checks the decompressed size only when the filename ends in `.gz`.

Tested with the same 4 KiB gzip payload and a 32-byte limit:

- `validate_stored_upload` accepted it as `x.vcf`.
- It rejected it as `x.vcf.gz`.

The STRUCTURE parser opens `.vcf` files as plain text, so there it raises `UnicodeDecodeError` instead of expanding. That error is not caught, so the client gets a 500.

**Needs validation:** cyvcf2 is used by validate, convert and download. If it detects gzip by content, as htslib normally does, it will expand the file with no size limit. That is a gzip bomb: a 100 KB upload can expand to many gigabytes. cyvcf2 is not installed here, so this could not be confirmed. Upload a small gzip file named `x.vcf` to a local copy of the app and call `/api/vcf/validate`.

Fix: check the first two bytes (`1f 8b`) of every upload and apply the decompressed-size check whenever they match, whatever the name.

### 10. Artifact cleanup can delete another user's recent artifact

`services/plex34_structure.py:126-132` keeps only the 25 newest artifacts across all users. Tested with three artifact folders and a limit of 2: the oldest was deleted even though all three were under a day old. Anyone can push out someone else's STRUCTURE package by generating 25 of their own.

Fix: this goes away with per-user ownership and a byte quota (findings 1 and 4).

### 11. Exported CSVs keep spreadsheet formulas

Sample names and VCF fields go into exported CSVs unchanged:

- sample names into CSV cells (`vcf_processor.py:164-182`)
- sample names into column headers, and `CHROM`, `ID`, `REF`, `ALT`, `FILTER` and `INFO` into cells (`:204-217`)

They are written with `df.to_csv` (`vcf.py:157`, `:199`, `:247`) with no escaping. A sample named `=HYPERLINK(...)` becomes a live formula when an analyst opens the CSV in Excel or LibreOffice. Spreadsheet apps warn before running external content, so the realistic risk is a malicious link or data leak if the analyst clicks through.

CWE-1236.

Fix: prefix cells that start with `=`, `+`, `-`, `@`, tab or carriage return with `'`, or reject such sample names during validation.

### 12. Exception text returned to the client

`vcf.py:68`, `:129`, `:169`, `:208`, `:228` and `:256`, and `plex34_structure.py:56` and `:58`, put `str(e)` in the response.

Tested: a missing marker file gives `Marker file not found: /app/data/missing_markers.txt`, which includes the server path. That case needs a broken server setup, though. Whether a malformed user upload makes cyvcf2 return a message containing the upload path was not observed.

CWE-209.

Fix: log the exception on the server and return a generic message with a request ID.

### 13. HIrisPlex-S parser crashes on a long field

Tested: a CSV field longer than 131,072 characters raises `_csv.Error` in `hirisplex_results_parser.py:42-68`. The route only catches `HirisPlexSResultsParseError`, so the client gets a 500. This is harmless on its own, but it is one more uncaught error path.

Fix: catch `csv.Error` and return 400.

### 14. Wrong upload limit shown in the frontend

`frontend/src/components/FileUploadZone.tsx:105` shows "Max. 200MB". Nginx and the backend allow 100 MiB.

- No dropzone sets `maxSize`.
- The dropzone accepts any `.gz` file, but the backend accepts only `.vcf.gz`.
- Validation results list every sample and every duplicate marker without paging, which can freeze the user's own browser tab.

Fix: show the real limit, set `maxSize` to match, and accept only `.vcf` and `.vcf.gz`.

### 15. Container hardening

Neither Dockerfile sets a `USER`, so both containers run as root. Compose sets none of these:

- memory, CPU or process limits
- a read-only root filesystem
- dropped capabilities
- a healthcheck
- a restart policy
- log rotation

Other gaps:

- The backend image keeps `gcc`, `g++` and `make` after the build.
- Base images use floating tags (`python:3.12-slim`, `node:18-alpine`, `nginx:alpine`).
- `npm install -g pnpm` installs whatever version is current.
- Node 18 is end of life.
- Nginx sends its version number and no security headers.

None of these is exploitable on its own. They decide how much damage any of the findings above can do to the rest of the VPS. The settings are in the next section.

## Resource limits to add

Real HIrisPlex-S and PLEX-34 casework VCFs cover 71 unique markers (41 HIrisPlex-S, 34 PLEX-34, some shared) and a handful of samples, so they are kilobytes, not hundreds of megabytes. The limits below are generous for that use and keep one bad request from affecting the VPS. The VPS has 8 CPUs, 31 GiB RAM and about 325 GB free disk, shared with your other apps.

### Caddy (public entry point)

- Require login on the whole site with `basic_auth` (Caddy 2.8 or later; `basicauth` on older versions) until the app has its own.
- Pass the real client IP to Nginx, so per-IP limits apply per user instead of per Caddy.

### Nginx (inside the frontend container)

| Setting | Value | Where |
|---|---|---|
| `client_max_body_size` | 1m | server default |
| `client_max_body_size` | 20m | `location = /api/vcf/upload` |
| `client_max_body_size` | 5m | `/api/results/` and `/api/vcf/plex34/structure-output` |
| `limit_req_zone` | 10 requests per minute per IP, burst 5 | upload and results routes |
| `limit_req_zone` | 60 requests per minute per IP, burst 20 | other `/api` routes |
| `limit_conn` | 5 per IP | `/api` |
| `client_body_timeout` / `client_header_timeout` | 30s | server |
| `proxy_read_timeout` | 120s | `/api`, matched to the backend job timeout |
| `client_body_temp_path` | on a tmpfs (see Docker) | server |
| `server_tokens` | off | http |
| `real_ip_header` / `set_real_ip_from` | the Caddy address | server |

Add security headers:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer` (also stops file IDs leaking in referrers)
- `X-Frame-Options: DENY`
- a basic `Content-Security-Policy`

### Application (backend settings and code)

| Limit | Value |
|---|---|
| `MAX_UPLOAD_SIZE` | 20 MiB |
| `MAX_UNCOMPRESSED_UPLOAD_SIZE` | 100 MiB, checked by gzip signature, not filename |
| Samples per VCF | 5,000 |
| Variants per VCF | 10,000 |
| Samples x variants processed | 2,000,000 cells, which keeps Python memory per job in the low hundreds of MB |
| STRUCTURE output written | 50 MiB per artifact |
| HIrisPlex-S results upload | 5 MiB and 10,000 rows |
| STRUCTURE output upload | 5 MiB (already enforced), 10,000 lines, 64 clusters per line |
| Upload retention | 24 hours, plus deletion when the user finishes |
| Total upload storage | 2 GiB |
| Total artifact storage | 1 GiB, cleaned on a timer as well as on generation |
| Concurrent heavy jobs | 2, in a process pool, each stopped after 60 s |
| Uvicorn | `--workers 2 --limit-concurrency 20 --timeout-keep-alive 5 --proxy-headers --forwarded-allow-ips <nginx container IP>` |

### Docker Compose (in `compose.deploy.yml`)

Backend:

```yaml
mem_limit: 2g
memswap_limit: 2g        # same as mem_limit, so no swap
cpus: 2
pids_limit: 256
read_only: true
tmpfs:
  - /tmp:size=256m       # multipart uploads spool here
user: "10001:10001"      # requires a matching user in the Dockerfile
cap_drop: [ALL]
security_opt: [no-new-privileges:true]
restart: unless-stopped
logging:
  driver: json-file
  options: { max-size: "10m", max-file: "3" }
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
  interval: 30s
  timeout: 5s
  retries: 3
```

Frontend:

```yaml
mem_limit: 256m
cpus: 0.5
pids_limit: 64
read_only: true
tmpfs:
  - /var/cache/nginx:size=64m
  - /var/run:size=1m
  - /tmp:size=32m
cap_drop: [ALL]
cap_add: [CHOWN, SETGID, SETUID, NET_BIND_SERVICE]   # or use nginxinc/nginx-unprivileged on port 8080 and drop all
security_opt: [no-new-privileges:true]
restart: unless-stopped
logging:
  driver: json-file
  options: { max-size: "10m", max-file: "3" }
```

Container memory limits do not cap disk use. Put uploads and artifacts on storage with a hard ceiling, for example a 5 GiB filesystem image mounted only for this app, or a project quota. Then a bug in the app's own quota cannot fill the host disk.

With these limits, the worst case for this app is about 2.25 GiB RAM, 2.5 CPUs and 5 GiB disk. Your other apps keep the rest.

## Checked and not a problem

- **Path traversal through file or artifact IDs.** `UUID()` rejects `../../etc/passwd`, tested. The artifact ID regex allows only 32 hex characters. The upload filename is used only for its extension. Zip entry names are fixed.
- **XSS in the frontend.** No `dangerouslySetInnerHTML`, `innerHTML`, `eval` or external scripts. Server text is rendered as React text. `window.open` only opens same-origin URLs built from server-issued IDs.
- **Injection into STRUCTURE parameter files.** Only integers and a fixed filename are written into `mainparams`. `extraparams` is copied from a server template.
- **Committed secrets.** `.env.example` and `.env.development` contain only ports, paths, sizes and CORS origins. `.env` is gitignored. The two commits in history contain no keys or credentials.
- **Zip bombs.** The server only writes zips. It never reads one from a client.
- **CORS.** The origin list is explicit and the app uses no cookies. Revisit when you add login: never combine `allow_credentials=True` with a wildcard origin.
- **The existing size checks.** The 100 MiB upload cap and the `.vcf.gz` decompression cap both work, tested.

## What was not tested, and why

- **Full HTTP requests.** FastAPI, Starlette, pandas and cyvcf2 are not installed in the review environment, and none were installed. Findings 3, 6 and the cyvcf2 half of 9 come from source and advisory data, not a running server.
- **Independent second check.** The two testers assigned to re-check findings did not return results. Every test here was run once, by one person.
- **Live VPS state.** Firewall rules, Caddy config, Docker iptables behavior and existing containers were deliberately left alone. Finding 7 describes the compose file, not what is reachable today.
- **Docker image builds.** Not run. Finding 8 comes from the Dockerfile and the missing `.dockerignore`.
- **Memory figures.** Measured with plain Python objects instead of Pydantic models, so real usage is higher.
- **Frontend dependencies.** Advisories for axios, react-router and Vite were reviewed by reading only. axios is used with fixed settings in the browser. react-router is listed in `package.json` but never imported. Vite only matters for the dev server, which the Docker build does not ship. `pnpm audit` was not run.

## Must fix before deploy

1. Login in front of the site (finding 1). Caddy `basic_auth` is enough to start.
2. Publish only the frontend, on `127.0.0.1` (finding 7).
3. Upgrade FastAPI and Starlette, pin `python-multipart>=0.0.31`, and add a lock file (finding 3).
4. Upload TTL and storage quota, on size-limited storage (findings 2 and 4).
5. Add `backend/.dockerignore`, or move data out of `backend/app` (finding 8).
6. Gzip sniffing on every upload (finding 9).
7. Size and row caps on both results parsers, and the sample and variant caps (findings 4 and 5).
8. The Docker and Nginx limits from the previous section.

Findings 6 and 10 to 15 can follow soon after. Finding 6 matters more as soon as more than one person uses the app.
