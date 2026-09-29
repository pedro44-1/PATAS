FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
COPY packages/shared-types/package.json packages/shared-types/tsconfig.json ./packages/shared-types/
RUN npm ci
COPY frontend ./frontend
COPY packages/shared-types ./packages/shared-types
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
