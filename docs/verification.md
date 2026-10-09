# Verification

## Backend Syntax Check

Run from `backend/`:

```bash
python3 -m py_compile app/core/config.py app/services/_plex34_structure_io.py app/services/hirisplex_results_parser.py app/services/plex34_structure.py app/services/structure_output_parser.py app/services/upload_lookup.py app/services/vcf_duplicate_warnings.py app/services/upload_storage.py app/services/__init__.py app/models/schemas.py app/models/__init__.py app/api/routes/vcf.py app/api/routes/hirisplex_results.py app/api/routes/plex34_structure.py app/main.py
```

## Frontend Checks

Run when Node and pnpm are available:

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

Run when Docker is available:

```bash
docker compose config
```

## Manual Runtime Check

1. Start the backend and frontend.
2. Open `http://localhost:5173`.
3. Upload a `.vcf` or `.vcf.gz` file.
4. Validate it.
5. Generate at least one CSV output and a PLEX-34 STRUCTURE package.
6. Upload a HIrisPlex-S result CSV and one STRUCTURE `.txt` or `.out` output file if test fixtures are available.

The app should show validation feedback, downloadable artifacts, and independent HIrisPlex-S and PLEX-34 summaries.
