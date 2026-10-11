# Architecture

This project is a merged HIrisPlex-S and PLEX-34 full stack application. It starts from a FastAPI and React HIrisPlex-S workflow, then adds PLEX-34 CSV conversion, PLEX-34 STRUCTURE package generation, and STRUCTURE output parsing as native backend and frontend features.

The repository is self-contained for runtime use. It doesn't need the earlier source folders that were used while assembling this copy.

## Stack

- Backend: FastAPI, Python, cyvcf2, Pydantic.
- Frontend: Vite, React, TypeScript, Tailwind CSS, TanStack Query, Axios.
- Local development ports: backend `3002`, frontend `5173`.
- Docker ports: frontend `80`, backend `8000`.

## Processing Method

The app transforms an uploaded VCF file into inputs for HIrisPlex-S and PLEX-34, then reads result files produced by external tools. File handling, genomic processing, result parsing, and visualization stay separate so the HIrisPlex-S and PLEX-34 workflows remain independent.

### 1. Input Storage

The user uploads a `.vcf` or `.vcf.gz` file through the React interface. The backend checks the extension, assigns a unique ID, and writes the upload to temporary storage in chunks.

Before anything is written the backend runs the retention sweep and checks the upload directory quota (1 GiB by default; `507` when full). While streaming it enforces the per-file limit (20 MiB; `413`). Once stored it detects gzip by the `1f 8b` signature rather than the filename: gzip content named `.vcf` is rejected, and gzip named `.vcf.gz` is walked to enforce the 100 MiB decompressed limit. Finally a single text pass checks the VCF shape (at most 5,000 samples, 10,000 variants and 2,000,000 sample x variant cells; unique, whitespace-free sample names). Any failure deletes the file and returns `4xx`.

Uploads are short-lived. Each use of a `file_id` (validate, convert, download, STRUCTURE input) refreshes the file's idle timer; a file is deleted 5 minutes after its last use, or 30 minutes after upload at the latest, whichever comes first. A background sweeper runs every minute and before every new upload. The frontend also deletes the upload (`DELETE /api/vcf/upload/{file_id}`) when the user removes the file. In containers uploads and artifacts live under `/data`, outside the source tree.

### 2. VCF Validation

The uploaded file is opened with `cyvcf2` and checked before conversion. Validation:

1. Confirms variants have marker identifiers.
2. Extracts sample names and marker identifiers.
3. Compares identifiers with vendored HIrisPlex-S and PLEX-34 marker lists.
4. Detects missing genotypes and records affected variants and samples.
5. Checks reference and alternate alleles for valid nucleotide symbols, `A`, `T`, `G`, or `C`.
6. Detects duplicate marker identifiers and returns warnings.

All six checks run in a single pass over the file inside a bounded thread pool. Per-variant genotype detail is retained for the first 100 variants only; the missing-genotype count covers the whole file. Files cyvcf2 cannot parse return `400`.

The frontend shows missing markers, missing genotypes, duplicate IDs, and other warnings before conversion.

### 3. Genotype Conversion

For each requested marker, VCF genotype allele indexes are resolved against the variant reference and alternate alleles. The result is represented as nucleotide pairs. Missing genotypes are represented as empty values in converted outputs.

The processor transposes the data so samples form rows and marker identifiers form columns. It can export:

- A HIrisPlex-S CSV containing the marker set required by HIrisPlex-S.
- A PLEX-34 CSV containing the marker set required by PLEX-34.
- A full VCF-derived CSV for inspection and download.

Marker definitions are loaded from bundled data files so conversion is reproducible within this repository.

### 4. PLEX-34 STRUCTURE Package Generation

The PLEX-34 STRUCTURE workflow uses the PLEX-34 marker list, bundled population metadata, and vendored STRUCTURE parameter templates. The service preserves marker order, records markers absent from the input, and writes a temporary artifact with:

- `plex34_structure_input.txt`, with sample genotypes and population information.
- `mainparams`, with sample count, marker count, and input filename.
- `extraparams`, copied from the project template.

The files are compressed into a uniquely named zip archive for download. Artifact directories are pruned by age and count before new artifacts are created.

### 5. External Analysis and Result Reading

The app prepares input files and reads uploaded results. It doesn't run the HIrisPlex-S website or the STRUCTURE binary.

For HIrisPlex-S, the result reader expects eye, hair, and hair-shade probability columns. Each value must be numeric and between `0` and `1`. For each sample, the app selects the category with the highest probability for eye color, hair color, and hair shade. Skin is shown as unavailable when skin probability columns aren't present.

For PLEX-34, the result reader locates the `Inferred ancestry of individuals` section and reads sample rows until `Estimated Allele Frequencies in each cluster`. It extracts cluster probabilities, validates numeric values, identifies the highest probability, and returns the top cluster and confidence value.

### 6. Presentation

The frontend uses the API client and VCF store to manage upload, validation, conversion, and result state. UI components show upload controls, validation warnings, downloads, phenotype predictions, ancestry probabilities, and the PLEX-34 map-style summary.

HIrisPlex-S and PLEX-34 results are displayed as separate workflows. Samples are not matched between them.

### 7. Reliability

The backend uses typed Pydantic response models and explicit error responses for invalid files, malformed result data, missing sections, unsupported formats, and size violations. Unexpected failures return a generic message with an `X-Request-ID` that matches the server log; exception text and paths never reach the client.

Temporary uploads are kept for 5 minutes after their last use (30 minutes at most) within a 1 GiB quota; STRUCTURE artifacts are kept for 30 minutes, at most 100 at a time and 512 MiB in total. One periodic sweeper enforces both. Heavy VCF work runs in a thread pool capped at two concurrent jobs per worker, so `/health` and light requests keep answering while files are processed.

## Main Modules

### Backend

- `backend/app/main.py`: FastAPI app entry point and router registration.
- `backend/app/api/routes/vcf.py`: VCF upload, validation, conversion, marker lookup, and download endpoints.
- `backend/app/api/routes/hirisplex_results.py`: HIrisPlex-S result CSV ingestion endpoint.
- `backend/app/api/routes/plex34_structure.py`: PLEX-34 STRUCTURE package generation and result parsing endpoints.
- `backend/app/core/config.py`: Runtime settings, ports, upload limits, and artifact retention rules.
- `backend/app/models/schemas.py`: Request and response models used by the API.
- `backend/app/services/vcf_processor.py`: Core VCF parsing and conversion workflow.
- `backend/app/services/marker_service.py`: Marker metadata and marker-type handling.
- `backend/app/services/plex34_structure.py`: PLEX-34 STRUCTURE package generation logic.
- `backend/app/services/structure_output_parser.py`: STRUCTURE output parser.
- `backend/app/services/hirisplex_results_parser.py`: HIrisPlex-S result CSV parser.
- `backend/app/services/upload_storage.py`: Temporary upload storage lifecycle.
- `backend/app/services/upload_lookup.py`: Uploaded file and artifact metadata tracking.
- `backend/app/services/vcf_duplicate_warnings.py`: Duplicate marker and warning helpers.
- `backend/app/services/_plex34_structure_io.py`: File I/O helpers for STRUCTURE package artifacts.

### Frontend

- `frontend/src/main.tsx`: App bootstrap.
- `frontend/src/App.tsx`: Main page layout and route-level composition.
- `frontend/src/api/client.ts`: Backend API client.
- `frontend/src/store/vcfStore.ts`: Shared upload, validation, and conversion state.
- `frontend/src/components/ConversionSection.tsx`: HIrisPlex-S and PLEX-34 conversion UI.
- `frontend/src/components/ResultsUploadSection.tsx`: Upload UI for external result files.
- `frontend/src/components/FileUploadZone.tsx`: Drag and drop upload component.
- `frontend/src/components/ValidationPanel.tsx` and `ValidationWarnings.tsx`: Validation feedback.
- `frontend/src/components/HirisplexSResultsUploadCard.tsx`: HIrisPlex-S result upload card.
- `frontend/src/components/Plex34StructureCard.tsx` and `Plex34StructureOutputCard.tsx`: PLEX-34 package and output workflow cards.
- `frontend/src/components/Plex34AncestryMap.tsx` and `plex34AncestryRegions.ts`: Visual ancestry summary and region mapping.
- `frontend/src/components/JSONViewer.tsx` and `DataTable.tsx`: Debug and data display components.

## Scope and Limits

The app prepares inputs and reads outputs. It doesn't replace the statistical analysis performed by HIrisPlex-S or STRUCTURE, doesn't run either external analysis engine, and doesn't infer a joint result from both systems. Reported predictions and ancestry clusters depend on result files produced by those external tools.
