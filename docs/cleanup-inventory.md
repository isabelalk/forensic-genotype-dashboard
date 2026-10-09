# Cleanup Inventory

This repository used to keep overlapping durable docs at the root. Their content now lives in the root `README.md` and the focused files under `docs/`.

## Consolidated Sources

- `README.md`: architecture, processing method, module inventory, local development, API list, verification commands, and usage flow.
- `DESIGN.md`: UI identity, theme tokens, typography, layout, component rules, motion, and surface guidance.
- `HOW_TO_RUN.md`: local run commands, Docker run command, workflow notes, and troubleshooting.
- `PROJECT_SUMMARY.md`: current scope, project layout, runtime ports, API list, runtime behavior, and verification commands.
- `QUICKSTART.md`: short install and local run steps.
- `FINAL_INSTRUCTIONS.md`: local and Docker URLs plus the external-result-reader reminder.
- `FIRST_README.md`: original Portuguese quick run notes and PLEX-34 STRUCTURE workflow summary.
- `UPDATED_PORTS.md`: local and Docker port mapping.
- `md_txt/instructions_install_structure.md`: Portuguese STRUCTURE installation and external execution instructions.

## New Documentation Map

- `docs/architecture.md`: app scope, architecture, processing method, modules, and limits.
- `docs/quickstart.md`: install, local run, Docker run, and first workflow.
- `docs/development.md`: local services, runtime data, vendored data, and troubleshooting.
- `docs/api.md`: endpoint list and result reader behavior.
- `docs/verification.md`: backend, frontend, Docker, and manual checks.
- `docs/design-system.md`: durable UI design system guidance.
- `docs/structure.md`: PLEX-34 STRUCTURE package and external run instructions.
- `docs/cleanup-inventory.md`: this preservation map.

## Root Files Kept

- `README.md`: concise entry point.
- `frontend/README.md`: frontend-specific notes, kept in place.

## Root Files Removed After Preservation

- `DESIGN.md`.
- `HOW_TO_RUN.md`.
- `PROJECT_SUMMARY.md`.
- `QUICKSTART.md`.
- `FINAL_INSTRUCTIONS.md`.
- `FIRST_README.md`.
- `UPDATED_PORTS.md`.
- `START_HERE.txt`.

## Generated Artifacts Removed

- `hirisplex-light-snapshot.md`: Playwright accessibility snapshot output.
- `md_txt/instructions_install_structure.md`: ignored duplicate of the STRUCTURE instructions now preserved in `docs/structure.md`.
- `frontend/qa-*.png`: frontend QA screenshots.
- `hirisplex-*.png`: root visual QA screenshots.
- `plex34-*.png`: root PLEX-34 visual QA screenshots.
- `visual-*.png`: root visual comparison screenshots.
- `.playwright-mcp/`: generated Playwright MCP page snapshots, logs, and test output files.

The generated image names had no exact source or Markdown references outside this inventory before deletion.
