#!/usr/bin/env bash
set -euo pipefail
engine_path="${1:?engine path required}"
runtime_args=()
if [[ "${RUNNER_MODE:-podman}" == "gvisor" ]]; then
  runtime_args+=(--runtime=runsc)
fi
exec podman run --rm -i "${runtime_args[@]}" \
  --network=none --read-only --user=65534:65534 \
  --cap-drop=all --security-opt=no-new-privileges \
  --pids-limit=64 --memory=512m --cpus=1 --tmpfs=/tmp:rw,noexec,nosuid,size=16m \
  -v "$engine_path:/engine:ro,Z" cbfc-engine-runtime:latest /engine
