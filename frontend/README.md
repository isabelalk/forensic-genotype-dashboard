# Frontend

React + TypeScript + Vite frontend for the isolated HIrisPlex-S + PLEX-34 fullstack app.

## Local Run

From the project root:

```bash
./start-frontend.sh
```

Or from this folder:

```bash
pnpm dev
```

The frontend runs at `http://localhost:5173` and expects the local backend at `http://localhost:3002`.

### Backend shared secret in dev

If the backend is started with `API_SHARED_SECRET` set, it rejects requests that do not carry a matching `X-Internal-Token` header. The Vite dev proxy adds that header to every `/api` request when `BACKEND_SHARED_SECRET` is set in the dev server's environment:

```bash
BACKEND_SHARED_SECRET=change-me pnpm dev
```

Use the same value as the backend's `API_SHARED_SECRET`. Leave it unset when the backend runs without a secret. The variable is read only by the dev server; it is not `VITE_`-prefixed and never reaches the browser bundle.

## Upload Limits and Expiry

- The VCF dropzone accepts only `.vcf` and `.vcf.gz` files (a bare `.gz` is rejected) up to 20 MB (20 MiB) per file. Larger files or other extensions are rejected in the browser with a message, and no request is sent. The limit lives in `src/config/limits.ts` and must match the backend.
- The backend keeps an uploaded VCF for 5 minutes after its last use and for 30 minutes at most. When a validate, convert, download, or STRUCTURE request finds the upload gone (`404`), the app clears the upload and its validation results, returns to the upload step, and asks you to upload the file again.
- Removing the selected file sends `DELETE /api/vcf/upload/{file_id}` so the server drops it immediately. Closing or leaving the page attempts the same delete.
- Downloads are fetched in the page and saved directly; they no longer open a new tab.

## Checks

```bash
pnpm lint
pnpm type-check
pnpm build
```

## Features

- Upload `.vcf` or `.vcf.gz` files.
- Show backend validation results.
- Download HIrisPlex-S CSV output.
- Download simple PLEX-34 CSV output.
- Generate and download the PLEX-34 STRUCTURE input/config zip.
- Upload the external HIrisPlex-S result CSV and display highest eye, hair, and hair-shade predictions.
- Upload one STRUCTURE `.txt` or `.out` output file and display the highest STRUCTURE cluster with extracted inferred ancestry sample lines.

The frontend reads uploaded result files independently. It does not run HIrisPlex-S or STRUCTURE, and it does not match samples between the two systems.
