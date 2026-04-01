# Stage 1: Install dependencies
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build the static assets (adapter-static → dist/)
COPY . .
RUN npm run build

# Stage 3: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
