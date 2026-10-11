# API

Local API base URL: `http://localhost:3002`.

In Docker the backend is not published on the host. The frontend's Nginx proxies `/api` to it on the compose network, so the API is reached through the frontend at `http://127.0.0.1:8080/api`.

Swagger UI (`/docs`, `/redoc`, `/openapi.json`) is served only when `APP_ENV=development`. In any other environment those paths return `404`.

## Access control

- When `API_SHARED_SECRET` is set, every request under `/api/` must carry `X-Internal-Token: <secret>` or it gets `403 {"detail": "Forbidden"}`. The Nginx proxy adds this header (from `BACKEND_SHARED_SECRET`) and overwrites any value the client sends. `/health` never needs it.
- When `API_SHARED_SECRET` is empty (local development), `/api` is open and the backend logs a warning at startup.
- CORS allows only the origins in `CORS_ORIGINS`, methods `GET`, `POST`, `DELETE`, and the `Content-Type` header. Credentials are never allowed.

## Request IDs and errors

- Every response carries `X-Request-ID`. Send your own (1 to 64 characters of `A-Z a-z 0-9 -`) and it is echoed; otherwise one is generated.
- Unexpected failures return `500 {"detail": "Internal server error. Reference: <request-id>"}`. The server log holds the traceback under the same ID. Response bodies never contain exception text or server paths.
- Problems with the uploaded content return `4xx` with a descriptive `detail`.

## Endpoints

- `GET /health`: service health check.
- `POST /api/vcf/upload`: upload a `.vcf` or `.vcf.gz` file (multipart field `file`). Returns `{file_id, filename, size, message}`.
- `DELETE /api/vcf/upload/{file_id}`: delete a stored upload. `204` on success, `404` for unknown or malformed IDs.
- `POST /api/vcf/validate?file_id={file_id}`: validate an uploaded VCF.
- `POST /api/vcf/convert`: convert validated data to a requested marker output.
- `GET /api/vcf/download/{file_id}/{marker_type}`: download converted HIrisPlex-S or PLEX-34 CSV output.
- `GET /api/vcf/markers/{marker_type}`: list marker metadata for a marker set.
- `GET /api/vcf/download-full/{file_id}`: download the full VCF-derived CSV.
- `POST /api/results/hirisplex-s`: upload and parse a HIrisPlex-S website result CSV.
- `POST /api/vcf/plex34/structure-input?file_id={file_id}`: generate a PLEX-34 STRUCTURE package.
- `GET /api/vcf/plex34/structure-input/{artifact_id}/download`: download a generated STRUCTURE package.
- `POST /api/vcf/plex34/structure-output`: upload and parse one STRUCTURE `.txt` or `.out` output file.

## Upload rules and retention

| Rule | Default | Setting |
|---|---|---|
| Per-file upload size | 20 MiB (`413` when exceeded) | `MAX_UPLOAD_SIZE` |
| Decompressed size of gzip uploads | 100 MiB (`413`) | `MAX_UNCOMPRESSED_UPLOAD_SIZE` |
| Gzip detection | By the `1f 8b` signature. Gzip data named `.vcf` → `400`; non-gzip data named `.vcf.gz` → `400` | – |
| Total upload storage | 1 GiB (`507` when full) | `MAX_UPLOAD_DIR_BYTES` |
| Idle expiry | 5 minutes after the last use of a `file_id` | `UPLOAD_IDLE_TTL_SECONDS` |
| Maximum age | 30 minutes after upload | `UPLOAD_MAX_AGE_SECONDS` |

Every endpoint that takes a `file_id` refreshes its idle timer. After expiry those endpoints return `404 {"detail": "File not found"}`.

## VCF shape limits

Checked when the upload is stored; violations return `400` and the file is removed.

| Limit | Default | Setting |
|---|---|---|
| Samples per VCF | 5,000 | `MAX_VCF_SAMPLES` |
| Variants per VCF | 10,000 | `MAX_VCF_VARIANTS` |
| Samples × variants | 2,000,000 | `MAX_VCF_CELLS` |
| Sample names | unique, non-empty, no whitespace | – |

Validation returns at most 100 `missing_genotypes` entries; `missing_genotypes_count` is the full count. At most `MAX_CONCURRENT_HEAVY_JOBS` (2) VCF jobs run at once per worker; extra requests wait.

## Results reader limits

| Reader | Limit | Setting |
|---|---|---|
| HIrisPlex-S results CSV | 5 MiB upload (`413`), 10,000 data rows (`400`) | `MAX_RESULTS_UPLOAD_BYTES`, `MAX_RESULTS_ROWS` |
| STRUCTURE output | 5 MiB upload (`413`), 10,000 sample lines, 64 clusters per line (`400`) | `MAX_RESULTS_UPLOAD_BYTES`, `MAX_STRUCTURE_OUTPUT_LINES`, `MAX_STRUCTURE_CLUSTERS` |

Malformed CSV (for example an oversized field) returns `400`.

## STRUCTURE packages

Generated packages are kept for 30 minutes (`MAX_ARTIFACT_AGE_SECONDS`), at most 100 at a time (`MAX_ARTIFACT_COUNT`) and 512 MiB in total (`MAX_ARTIFACT_DIR_BYTES`), oldest removed first. A single STRUCTURE input file may not exceed 50 MiB (`MAX_STRUCTURE_INPUT_BYTES`, `400`).

## CSV exports

Cells and headers in exported CSVs that start with `=`, `+`, `-`, `@`, tab or carriage return are prefixed with `'` so spreadsheets do not treat them as formulas.

## Result Readers

The HIrisPlex-S result reader expects probability columns for eye, hair, and hair shade. It returns the highest prediction for each sample. Skin is unavailable when the uploaded result CSV has no skin probability columns.

The PLEX-34 STRUCTURE reader extracts inferred ancestry rows, cluster probabilities, the highest cluster, and confidence from a STRUCTURE output file. Supported display labels are Africa, Europe, East Asia, and South Asia.
