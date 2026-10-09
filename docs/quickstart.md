# Quickstart

Use these steps from the repository root.

## Prerequisites

- Node.js `18` or newer.
- pnpm `8` or newer.
- Python `3.12` or newer.
- Docker, optional.

## Install

```bash
pnpm install
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

## Run Locally

Start the backend in one terminal:

```bash
./start-backend.sh
```

Expected backend URLs:

- Health: `http://localhost:3002/health`.
- API docs: `http://localhost:3002/docs`.

Start the frontend in a second terminal:

```bash
./start-frontend.sh
```

Open `http://localhost:5173`.

You can also start both local processes with:

```bash
./start-dev.sh
```

## Docker

```bash
docker compose up --build
```

Docker URLs:

- Frontend: `http://localhost`.
- Backend: `http://localhost:8000`.

## Basic Workflow

1. Upload a `.vcf` or `.vcf.gz` file.
2. Validate markers and genotypes.
3. Generate a HIrisPlex-S CSV, PLEX-34 CSV, or PLEX-34 STRUCTURE package.
4. For HIrisPlex-S, upload the generated CSV to `https://hirisplex.erasmusmc.nl/`, then upload the website result CSV back into the app.
5. For PLEX-34, run STRUCTURE externally with the generated package, then upload one `.txt` or `.out` output file back into the app.
6. Read the independent visual summaries.

The app doesn't run HIrisPlex-S or STRUCTURE. It also doesn't match HIrisPlex-S samples with PLEX-34 samples.

## Quick Health Check

```bash
curl http://localhost:3002/health
```

Expected response:

```json
{"status":"ok"}
```
