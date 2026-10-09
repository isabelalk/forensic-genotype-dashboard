# Development

## Local Services

Local development uses two processes:

- Backend: `http://localhost:3002`.
- Frontend: `http://localhost:5173`.

Run the backend:

```bash
./start-backend.sh
```

Run the frontend:

```bash
./start-frontend.sh
```

Run both with the helper script:

```bash
./start-dev.sh
```

## Docker Services

Docker exposes:

- Frontend: `http://localhost`.
- Backend: `http://localhost:8000`.

Start Docker:

```bash
docker compose up --build
```

## Runtime Data

Generated uploads and artifacts are temporary runtime files under:

- `backend/app/uploads`.
- `backend/app/artifacts`.

The backend enforces `max_upload_size` during upload streaming, checks `.vcf.gz` decompressed size with `max_uncompressed_upload_size`, and prunes generated STRUCTURE artifact folders by `max_artifact_age_seconds` and `max_artifact_count` before creating new packages.

Generated `mainparams` uses `LOCDATA 1` so it remains consistent with the vendored `extraparams` `LOCPRIOR 1` setting.

## Vendored Data

Required metadata is kept in the repository:

- `backend/app/data/hrisplexs_id.txt`.
- `backend/app/data/plex34_id.txt`.
- `backend/app/data/plex34_structure/mainparams`.
- `backend/app/data/plex34_structure/extraparams`.
- `backend/app/data/plex34_structure/metapop_3202samples.csv`.

The root `data/` folder also keeps marker-list copies for project visibility, but the backend reads from `backend/app/data` by default.

## Troubleshooting

If the backend port is already in use:

```bash
lsof -i :3002
kill -9 <PID>
```

If the frontend port is already in use:

```bash
lsof -i :5173
kill -9 <PID>
```

Reinstall backend dependencies:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Reinstall frontend dependencies:

```bash
pnpm install
```
