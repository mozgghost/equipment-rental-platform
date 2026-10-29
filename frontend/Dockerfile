FROM node:24.22.1-alpine AS build
ARG VITE_APP_NAME="Equipment Rental Platform"
ENV VITE_APP_NAME=$VITE_APP_NAME
WORKDIR /app
COPY frontend/package.json ./package.json
# npm install is used until package-lock.json is generated and reviewed in the repository.
RUN npm install
COPY frontend/ ./
RUN npm run build
FROM nginx:1.29-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD wget -q -O - http://127.0.0.1/ >/dev/null || exit 1
