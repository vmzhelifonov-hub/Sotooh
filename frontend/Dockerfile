# syntax=dockerfile:1

# ---- Build stage ----------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ .
RUN npm run build

# ---- Runtime stage --------------------------------------------------------
FROM caddy:2-alpine AS runtime

COPY --from=build /app/dist /usr/share/caddy

EXPOSE 80
