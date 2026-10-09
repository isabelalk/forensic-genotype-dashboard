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
