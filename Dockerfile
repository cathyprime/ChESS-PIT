FROM debian:bookworm-slim@sha256:63a496b5d3b99214b39f5ed70eb71a61e590a77979c79cbee4faf991f8c0783e AS chess-tools
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tar && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://github.com/Disservin/fastchess/releases/download/v1.8.2-alpha/fastchess-linux-x86-64.tar -o /tmp/fastchess.tar \
 && echo "1003f920bebe841acdab5e6d7871e93171a4586857b3ec91c21ef5777f26ff96  /tmp/fastchess.tar" | sha256sum -c - \
 && tar -xf /tmp/fastchess.tar -C /tmp && install -m 755 "$(find /tmp -type f -name fastchess | head -1)" /fastchess
RUN curl -fsSL https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-ubuntu-x86-64.tar -o /tmp/stockfish.tar \
 && echo "5c6f38b02a4da5f3ffe763f27da6c3e743eebefd92b50cb3661623b96696adff  /tmp/stockfish.tar" | sha256sum -c - \
 && tar -xf /tmp/stockfish.tar -C /tmp && install -m 755 "$(find /tmp -type f -name 'stockfish*' -perm /111 | head -1)" /stockfish

FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91 AS api
WORKDIR /app
COPY backend/requirements.txt backend/requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY backend ./backend
COPY scripts/sandbox-engine.py ./scripts/sandbox-engine.py
COPY --from=chess-tools /fastchess /app/tools/fastchess
COPY --from=chess-tools /stockfish /app/tools/stockfish
ENV PYTHONPATH=/app/backend
RUN groupadd -g 10001 chesspit && useradd -u 10001 -g chesspit -M chesspit \
 && chmod 755 /app/scripts/sandbox-engine.py
USER 10001:10001
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--ws-max-size","16384"]

FROM node:22-alpine@sha256:76789712cd1ae89a1225eac9077010d68987a423588042dac30446f502f1858c AS web-build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM nginx:alpine@sha256:1d40e3eb3bf4f138de1d67193f2aa5309fcaf343eb5ffadbf5e9439de1eb1ebb AS web
COPY --from=web-build /web/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

FROM debian:bookworm-slim@sha256:63a496b5d3b99214b39f5ed70eb71a61e590a77979c79cbee4faf991f8c0783e AS data-init
CMD ["sh", "-c", "install -d -o 10001 -g 10001 -m 0770 /app/data /app/data/bots /app/data/matches /app/data/avatars"]

FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91 AS runner
WORKDIR /runner
COPY scripts/runner-daemon.py ./runner-daemon.py
RUN groupadd -g 10001 chesspit \
 && install -d -o root -g chesspit -m 2770 /run/chesspit-runner \
 && install -d -o root -g root -m 0711 /cache
ENV RUNNER_SOCKET=/run/chesspit-runner/runner.sock \
    BOT_STORAGE_DIR=/app/data/bots \
    RUNNER_CACHE_DIR=/cache \
    ENGINE_BACKEND=container-process \
    RUNNING_IN_ENGINE_CONTAINER=true
CMD ["python", "/runner/runner-daemon.py"]
