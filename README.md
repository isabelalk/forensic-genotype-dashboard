# HIrisPlex-S + PLEX-34 Full Stack Application

This repository is a self-contained FastAPI and React application for preparing HIrisPlex-S and PLEX-34 inputs, then reading result files produced by external HIrisPlex-S and STRUCTURE runs.

The app does not run the external HIrisPlex-S website or the STRUCTURE binary. It uploads and validates VCF files, generates CSV or STRUCTURE package outputs, and displays independent result summaries from uploaded external result files.

## Quick Links

- [Architecture](docs/architecture.md)
- [Quickstart](docs/quickstart.md)
- [Development](docs/development.md)
- [API](docs/api.md)
- [Verification](docs/verification.md)
- [Deployment](docs/deployment.md)
- [Design System](docs/design-system.md)
- [PLEX-34 STRUCTURE Workflow](docs/structure.md)
- [Cleanup Inventory](docs/cleanup-inventory.md)

## Local Ports

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:3002`
- API docs: `http://localhost:3002/docs`
- Health: `http://localhost:3002/health`

## Docker Ports

- Frontend: `http://127.0.0.1:8080` (bound to loopback; put Caddy or another reverse proxy in front for public access)
- Backend: not published; it is reachable only from the frontend container over the compose network

Docker needs `BACKEND_SHARED_SECRET` in `.env`. See [docs/deployment.md](docs/deployment.md).

## Start Locally

Install dependencies, then run the backend and frontend from the repository root:

```bash
./start-backend.sh
./start-frontend.sh
```

For full setup steps, see [docs/quickstart.md](docs/quickstart.md).

## Main Workflow

1. Upload a `.vcf` or `.vcf.gz` file.
2. Validate markers and genotypes.
3. Generate a HIrisPlex-S CSV, PLEX-34 CSV, or PLEX-34 STRUCTURE package.
4. Run HIrisPlex-S or STRUCTURE externally.
5. Upload the external result file back into the app.
6. Review the independent HIrisPlex-S phenotype and PLEX-34 STRUCTURE summaries.

Generated uploads and artifacts are temporary runtime files under `backend/app/uploads` and `backend/app/artifacts` (`/data/uploads` and `/data/artifacts` in Docker).

Uploads are kept 5 minutes after last use and at most 30 minutes, 20 MiB per file, 1 GiB in total, and are deleted when the user removes the file. See [docs/deployment.md](docs/deployment.md) for running the Docker stack.
# hirisplex-plex34-parser
