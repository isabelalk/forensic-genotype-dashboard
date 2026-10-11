# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM node:22.23.3-alpine AS builder

WORKDIR /app

# pnpm version comes from "packageManager" in the root package.json
RUN corepack enable && corepack prepare pnpm@10.34.6 --activate

# Copy monorepo root files for pnpm workspace
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy workspace package manifests
COPY frontend/package.json ./frontend/
COPY backend/package.json ./backend/

RUN pnpm install --frozen-lockfile --filter frontend

# Copy frontend source code
COPY frontend/ ./frontend/

# Build the application
RUN pnpm --filter frontend run build

# ---- Runtime stage (non-root, listens on 8080) ----
FROM nginxinc/nginx-unprivileged:1.27.5-alpine

COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# The image entrypoint renders /etc/nginx/templates/*.template with envsubst
# into /etc/nginx/conf.d/ at startup.
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080
