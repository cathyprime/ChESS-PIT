FROM debian:bookworm-slim AS chess-tools
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tar && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://github.com/Disservin/fastchess/releases/download/v1.8.2-alpha/fastchess-linux-x86-64.tar -o /tmp/fastchess.tar \
 && tar -xf /tmp/fastchess.tar -C /tmp && install -m 755 "$(find /tmp -type f -name fastchess | head -1)" /fastchess
RUN curl -fsSL https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-ubuntu-x86-64.tar -o /tmp/stockfish.tar \
 && tar -xf /tmp/stockfish.tar -C /tmp && install -m 755 "$(find /tmp -type f -name 'stockfish*' -perm /111 | head -1)" /stockfish

FROM python:3.13-slim AS api
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY scripts/sandbox-engine.sh ./scripts/sandbox-engine.sh
COPY --from=chess-tools /fastchess /app/tools/fastchess
COPY --from=chess-tools /stockfish /app/tools/stockfish
ENV PYTHONPATH=/app/backend
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

FROM node:22-alpine AS web-build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM nginx:alpine AS web
COPY --from=web-build /web/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

FROM debian:bookworm-slim AS engine-runtime
RUN useradd --uid 65534 --no-create-home engine || true
USER 65534:65534
ENTRYPOINT ["/engine"]
