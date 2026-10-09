FROM node:18-alpine AS builder

WORKDIR /app

# Copy monorepo root files for pnpm workspace
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy frontend package.json
COPY frontend/package.json ./frontend/
COPY backend/package.json ./backend/

# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile --filter frontend

# Copy frontend source code
COPY frontend/ ./frontend/

# Build the application
RUN pnpm --filter frontend run build

# Production stage
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
