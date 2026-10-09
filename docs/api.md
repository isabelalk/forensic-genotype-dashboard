# API

Local API base URL: `http://localhost:3002`.

Docker API base URL: `http://localhost:8000`.

Swagger UI is available at `http://localhost:3002/docs` in local development.

## Endpoints

- `GET /health`: service health check.
- `POST /api/vcf/upload`: upload a `.vcf` or `.vcf.gz` file.
- `POST /api/vcf/validate?file_id={file_id}`: validate an uploaded VCF.
- `POST /api/vcf/convert`: convert validated data to a requested marker output.
- `GET /api/vcf/download/{file_id}/{marker_type}`: download converted HIrisPlex-S or PLEX-34 CSV output.
- `GET /api/vcf/markers/{marker_type}`: list marker metadata for a marker set.
- `GET /api/vcf/download-full/{file_id}`: download the full VCF-derived CSV.
- `POST /api/results/hirisplex-s`: upload and parse a HIrisPlex-S website result CSV.
- `POST /api/vcf/plex34/structure-input?file_id={file_id}`: generate a PLEX-34 STRUCTURE package.
- `GET /api/vcf/plex34/structure-input/{artifact_id}/download`: download a generated STRUCTURE package.
- `POST /api/vcf/plex34/structure-output`: upload and parse one STRUCTURE `.txt` or `.out` output file.

## Result Readers

The HIrisPlex-S result reader expects probability columns for eye, hair, and hair shade. It returns the highest prediction for each sample. Skin is unavailable when the uploaded result CSV has no skin probability columns.

The PLEX-34 STRUCTURE reader extracts inferred ancestry rows, cluster probabilities, the highest cluster, and confidence from a STRUCTURE output file. Supported display labels are Africa, Europe, East Asia, and South Asia.
