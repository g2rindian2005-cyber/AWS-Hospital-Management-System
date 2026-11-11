# HealtheCare Hospital — frontend image
# Serves the static hospital dashboard with Nginx, mirroring the EC2
# production setup. The frontend talks directly to the AWS API, whose
# URL is baked in at build time:
#
#   docker build -t medicore-hospital .
#   docker build --build-arg API_BASE_URL=https://<api-id>.execute-api.us-east-1.amazonaws.com/prod -t medicore-hospital .
#   docker run -p 8080:80 medicore-hospital
#
FROM docker.io/library/nginx:1.27-alpine

ARG API_BASE_URL=https://s1gx9piqf1.execute-api.us-east-1.amazonaws.com/prod

# Nginx site config: gzip, long cache for static assets, SPA fallback.
RUN rm /etc/nginx/conf.d/default.conf && cat > /etc/nginx/conf.d/hospital.conf <<'NGINX'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    location ~* \.(css|js|jpg|png|gif|ico|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX

COPY frontend/ /usr/share/nginx/html/

# Point the frontend at the real API (the repo keeps a placeholder).
RUN sed -i "s|https://abc123.execute-api.us-east-1.amazonaws.com/prod|${API_BASE_URL}|g" \
        /usr/share/nginx/html/js/api.js && \
    grep -Fq "${API_BASE_URL}" /usr/share/nginx/html/js/api.js

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/login.html || exit 1
