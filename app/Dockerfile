# Stage 1: Install dependencies
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build the static assets (adapter-static → build/)
COPY . .
RUN npm run build

# Stage 3: Serve with nginx
FROM nginx:alpine
# jq builds env-config.js safely — see docker-entrypoint.sh.
RUN apk add --no-cache jq
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# autoheal (docker-compose.yml) restarts containers Docker reports as
# unhealthy — without a HEALTHCHECK, "unhealthy" never fires and it's a no-op.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
